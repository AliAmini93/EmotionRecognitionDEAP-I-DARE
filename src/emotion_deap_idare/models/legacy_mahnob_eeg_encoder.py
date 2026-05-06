"""
Adapted legacy MAHNOB EEG encoder for I-DARE/DEAP cache smoke tests.

This module keeps the original MAHNOB encoder family as an R0 / historical
baseline, but adapts the defaults to the current cache setting:

- input: [B, 32, 640]
- sampling rate: 128 Hz
- window: 5 seconds
- output embedding: [B, Dembed]

It is intentionally kept separate from EEGSegmentClassifier-v1.
Use it through OldStyleEEGClassifier when running classification smoke tests.
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


def _group_norm(num_channels: int, groups: int = 32) -> nn.GroupNorm:
    groups = min(groups, num_channels)
    while num_channels % groups != 0 and groups > 1:
        groups -= 1
    return nn.GroupNorm(groups, num_channels)


class Norm1D(nn.Module):
    def __init__(self, channels: int, kind: str = "gn") -> None:
        super().__init__()
        if kind == "bn":
            self.norm = nn.BatchNorm1d(channels)
        elif kind == "gn":
            self.norm = _group_norm(channels, groups=32)
        else:
            raise ValueError(f"Unknown norm kind: {kind}")

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.norm(x)


def auto_k0(timelen: int) -> int:
    """Legacy-style initial kernel selection, capped for short windows."""
    k = min(41, timelen if timelen % 2 == 1 else timelen - 1)
    k = max(7, k)
    if k > timelen:
        k = timelen if timelen % 2 == 1 else max(1, timelen - 1)
    return int(max(1, k))


def auto_s0(timelen: int) -> int:
    """Legacy-style stride selection."""
    if timelen > 512:
        return 4
    if timelen > 256:
        return 2
    return 1


def get_legacy_mahnob_preset(modelsize: str = "lite", timelen: int = 640) -> dict:
    """Return the original MAHNOB-family capacity preset.

    For 5-second windows, the lite preset uses the shorter dilation schedule.
    """
    if modelsize == "base":
        return {
            "Fper": 16,
            "Dgat": 64,
            "nheads": 4,
            "dilations": [1, 2, 4, 8, 16, 32, 64, 128] if timelen > 512 else [1, 2, 4, 8, 16, 32, 64],
            "Dembed": 256,
        }
    if modelsize == "lite":
        return {
            "Fper": 8,
            "Dgat": 32,
            "nheads": 2,
            "dilations": [1, 2, 4, 8, 16, 32, 64] if timelen > 256 else [1, 2, 4, 8, 16, 32],
            "Dembed": 128,
        }
    raise ValueError(f"Unknown legacy MAHNOB modelsize: {modelsize}")


class DepthwiseTemporalStem(nn.Module):
    def __init__(
        self,
        C: int,
        Fper: int,
        k0: int = 15,
        s0: int = 1,
        dropout: float = 0.05,
        norm_kind: str = "gn",
    ) -> None:
        super().__init__()
        p0 = k0 // 2
        self.dw = nn.Conv1d(C, C, kernel_size=k0, stride=s0, padding=p0, groups=C, bias=False)
        self.pw = nn.Conv1d(C, C * Fper, kernel_size=1, bias=False)
        self.norm = Norm1D(C * Fper, kind=norm_kind)
        self.drop = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.dw(x)
        x = self.pw(x)
        x = self.norm(x)
        x = F.elu(x)
        return self.drop(x)


class TCNBlockDW(nn.Module):
    def __init__(
        self,
        C: int,
        Fper: int,
        dilation: int,
        dropout: float = 0.1,
        k: int = 3,
        norm_kind: str = "gn",
    ) -> None:
        super().__init__()
        inch = C * Fper
        pad = dilation * (k // 2)

        self.norm1 = Norm1D(inch, kind=norm_kind)
        self.conv1 = nn.Conv1d(
            inch,
            inch,
            kernel_size=k,
            padding=pad,
            dilation=dilation,
            groups=C,
            bias=False,
        )
        self.norm2 = Norm1D(inch, kind=norm_kind)
        self.mix = nn.Conv1d(inch, inch, kernel_size=1, groups=C, bias=False)
        self.drop = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        res = x
        x = self.norm1(x)
        x = F.elu(x)
        x = self.conv1(x)
        x = self.norm2(x)
        x = F.elu(x)
        x = self.mix(x)
        x = self.drop(x)
        return x + res


class TCNStackDW(nn.Module):
    def __init__(
        self,
        C: int,
        Fper: int,
        dilations: list[int],
        dropout: float = 0.1,
        k: int = 3,
        norm_kind: str = "gn",
    ) -> None:
        super().__init__()
        self.blocks = nn.ModuleList(
            [TCNBlockDW(C, Fper, d, dropout=dropout, k=k, norm_kind=norm_kind) for d in dilations]
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        for block in self.blocks:
            x = block(x)
        return x


class TemporalAttnPool1D(nn.Module):
    def __init__(self, C: int, Fper: int) -> None:
        super().__init__()
        self.C = C
        self.Fper = Fper
        self.scorer = nn.Conv1d(C * Fper, C, kernel_size=1, groups=C, bias=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B, _CF, Tt = x.shape
        C, Fp = self.C, self.Fper
        scores = self.scorer(x)
        alpha = torch.softmax(scores, dim=-1)
        x4 = x.view(B, C, Fp, Tt)
        h = (x4 * alpha.unsqueeze(2)).sum(dim=-1)
        return h


class ChannelGAT(nn.Module):
    def __init__(
        self,
        C: int,
        Fin: int,
        Dgat: int = 64,
        nheads: int = 4,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.C = C
        self.projin = nn.Linear(Fin, Dgat)
        self.attn = nn.MultiheadAttention(Dgat, nheads, dropout=dropout, batch_first=False)
        self.ln1 = nn.LayerNorm(Dgat)
        self.ffn = nn.Sequential(
            nn.Linear(Dgat, 2 * Dgat),
            nn.ELU(),
            nn.Dropout(dropout),
            nn.Linear(2 * Dgat, Dgat),
            nn.Dropout(dropout),
        )
        self.ln2 = nn.LayerNorm(Dgat)

    def forward(self, h: torch.Tensor) -> torch.Tensor:
        x = self.projin(h)
        xt = x.transpose(0, 1)
        attn_out, _ = self.attn(xt, xt, xt, need_weights=False)
        xt = self.ln1(xt + attn_out)
        xffn = self.ffn(xt)
        xt = self.ln2(xt + xffn)
        return xt.transpose(0, 1)


class ChannelAttnPool(nn.Module):
    def __init__(self, Dgat: int, dropout: float = 0.1) -> None:
        super().__init__()
        self.score = nn.Linear(Dgat, 1)
        self.drop = nn.Dropout(dropout)

    def forward(self, h: torch.Tensor) -> torch.Tensor:
        w = self.score(h).squeeze(-1)
        alpha = torch.softmax(w, dim=-1).unsqueeze(-1)
        z = (h * alpha).sum(dim=1)
        return self.drop(z)


class LegacyMAHNOBEEGEncoder(nn.Module):
    """Original MAHNOB-family EEG encoder adapted for current 5-second EEG windows."""

    def __init__(
        self,
        C: int = 32,
        timelen: int = 640,
        dropout: float = 0.1,
        modelsize: str = "lite",
        norm_kind: str = "gn",
        use_temp_pools: bool = False,
    ) -> None:
        super().__init__()

        cfg = get_legacy_mahnob_preset(modelsize=modelsize, timelen=timelen)

        Fper = cfg["Fper"]
        Dgat = cfg["Dgat"]
        nheads = cfg["nheads"]
        dilations = cfg["dilations"]
        Dembed = cfg["Dembed"]

        k0 = auto_k0(timelen)
        s0 = auto_s0(timelen)

        self.modelsize = modelsize
        self.C = C
        self.timelen = timelen
        self.Fper = Fper
        self.Dembed = Dembed

        self.stem = DepthwiseTemporalStem(
            C=C,
            Fper=Fper,
            k0=k0,
            s0=s0,
            dropout=0.05,
            norm_kind=norm_kind,
        )
        self.pool1 = nn.AvgPool1d(4) if use_temp_pools else nn.Identity()

        self.tcn = TCNStackDW(
            C=C,
            Fper=Fper,
            dilations=dilations,
            dropout=dropout,
            k=3,
            norm_kind=norm_kind,
        )
        self.pool2 = nn.AvgPool1d(8) if use_temp_pools else nn.Identity()

        self.tpool = TemporalAttnPool1D(C=C, Fper=Fper)
        self.gat = ChannelGAT(C=C, Fin=Fper, Dgat=Dgat, nheads=nheads, dropout=dropout)
        self.cpool = ChannelAttnPool(Dgat=Dgat, dropout=dropout)

        self.proj = nn.Sequential(nn.LayerNorm(Dgat), nn.Linear(Dgat, Dembed))

    def forward(self, x_eeg: torch.Tensor) -> torch.Tensor:
        if x_eeg.ndim != 3:
            raise ValueError(f"Expected x_eeg [B, C, T], got shape {tuple(x_eeg.shape)}")
        if x_eeg.shape[1] != self.C:
            raise ValueError(f"Expected {self.C} channels, got {x_eeg.shape[1]}")

        x = self.stem(x_eeg)
        x = self.pool1(x)
        x = self.tcn(x)
        x = self.pool2(x)
        h = self.tpool(x)
        h = self.gat(h)
        z = self.cpool(h)
        z = self.proj(z)
        return z


class LegacyMAHNOBEEGClassifier(nn.Module):
    """Standalone classifier form for the adapted legacy encoder.

    This is provided for direct use, but the recommended project path is:
        LegacyMAHNOBEEGEncoder + OldStyleEEGClassifier
    """

    def __init__(
        self,
        C: int = 32,
        timelen: int = 640,
        n_classes: int = 2,
        pdrop: float = 0.3,
        modelsize: str = "lite",
        norm_kind: str = "gn",
        use_temp_pools: bool = False,
    ) -> None:
        super().__init__()

        self.enc = LegacyMAHNOBEEGEncoder(
            C=C,
            timelen=timelen,
            dropout=0.1,
            modelsize=modelsize,
            norm_kind=norm_kind,
            use_temp_pools=use_temp_pools,
        )

        self.head = nn.Sequential(
            nn.LayerNorm(self.enc.Dembed),
            nn.Linear(self.enc.Dembed, 128),
            nn.ELU(),
            nn.Dropout(pdrop),
            nn.Linear(128, n_classes),
        )

    def forward(self, x_eeg: torch.Tensor):
        z = self.enc(x_eeg)
        logits = self.head(z)
        return logits, {"z": z, "logits": logits}


if __name__ == "__main__":
    torch.manual_seed(7)
    enc = LegacyMAHNOBEEGEncoder(C=32, timelen=640, modelsize="lite")
    x = torch.randn(4, 32, 640)
    z = enc(x)
    print("z:", z.shape)
    clf = LegacyMAHNOBEEGClassifier(C=32, timelen=640, n_classes=2, modelsize="lite")
    logits, aux = clf(x)
    print("logits:", logits.shape)
    print("aux z:", aux["z"].shape)
