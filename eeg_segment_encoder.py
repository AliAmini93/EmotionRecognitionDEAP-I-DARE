"""
EEG segment encoder V1.

This file contains:
    - EEGSegmentEncoder

It also contains all helper modules required by the encoder:
    - MultiBranchTemporalStem
    - TemporalBranch
    - BranchFusion
    - TCNStackDW
    - TemporalAttnPool1D
    - ChannelPositionEmbedding
    - ChannelMixer
    - ChannelAttnPool
    - optional SpectralEncoder and EmbeddingFusion

Default intended use:
    - 5-second EEG windows
    - 128 Hz sampling rate
    - binary valence / arousal experiments on DEAP / I-DARE
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple, Union

import torch
import torch.nn as nn
import torch.nn.functional as F


# ============================================================
# Utilities
# ============================================================


def _make_odd(k: int) -> int:
    """Force a convolution kernel size to be positive and odd."""
    k = int(max(1, k))
    return k if k % 2 == 1 else k + 1


def kernel_sizes_from_durations(
    durations_sec: Sequence[float],
    sampling_rate: int,
    max_kernel: Optional[int] = None,
) -> List[int]:
    """
    Convert kernel durations in seconds to odd Conv1d kernel sizes.

    Example at 128 Hz:
        [0.125, 0.25, 0.5] -> [17, 33, 65]
    """
    kernels: List[int] = []
    for duration in durations_sec:
        k = _make_odd(round(float(duration) * sampling_rate))
        if max_kernel is not None:
            k = min(k, _make_odd(max_kernel))
        kernels.append(k)
    return kernels


def choose_valid_groups(num_channels: int, requested_groups: int = 32) -> int:
    """Choose a valid GroupNorm group count that divides num_channels."""
    groups = min(requested_groups, num_channels)
    while num_channels % groups != 0 and groups > 1:
        groups -= 1
    return groups


class Norm1D(nn.Module):
    """BatchNorm1d or GroupNorm wrapper for [B, C, T] tensors."""

    def __init__(self, channels: int, kind: str = "gn", groups: int = 32):
        super().__init__()
        kind = kind.lower()
        if kind == "bn":
            self.norm = nn.BatchNorm1d(channels)
        elif kind == "gn":
            self.norm = nn.GroupNorm(choose_valid_groups(channels, groups), channels)
        else:
            raise ValueError(f"Unsupported norm kind: {kind}. Use 'gn' or 'bn'.")

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.norm(x)


# ============================================================
# Multi-branch temporal stem
# ============================================================


class TemporalBranch(nn.Module):
    """
    One temporal branch:
        depthwise temporal convolution per electrode
        pointwise expansion per electrode group

    Input:
        x: [B, C, T]

    Output:
        y: [B, C * Fper, T']
    """

    def __init__(
        self,
        C: int,
        Fper: int,
        kernel_size: int,
        stride: int = 1,
        dropout: float = 0.05,
        norm_kind: str = "gn",
    ):
        super().__init__()
        kernel_size = _make_odd(kernel_size)
        padding = kernel_size // 2

        self.dw = nn.Conv1d(
            in_channels=C,
            out_channels=C,
            kernel_size=kernel_size,
            stride=stride,
            padding=padding,
            groups=C,
            bias=False,
        )
        self.pw = nn.Conv1d(C, C * Fper, kernel_size=1, bias=False)
        self.norm = Norm1D(C * Fper, kind=norm_kind)
        self.drop = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.dw(x)
        x = self.pw(x)
        x = self.norm(x)
        x = F.elu(x)
        x = self.drop(x)
        return x


class BranchFusion(nn.Module):
    """
    Fuse outputs of multi-scale temporal branches.

    Supported fusion modes:
        - concat: concatenate branch channels, then project back to C*Fper
        - sum: sum branch outputs directly
        - attn: global branch attention over existing branches
        - moe: lightweight branch-scale MoE gate over existing branches

    All branch outputs must have shape [B, C*Fper, T].
    """

    def __init__(
        self,
        num_branches: int,
        channels: int,
        fusion: str = "concat",
        dropout: float = 0.05,
        norm_kind: str = "gn",
        gate_hidden: int = 16,
    ):
        super().__init__()
        self.num_branches = num_branches
        self.channels = channels
        self.fusion = fusion.lower()

        if self.fusion == "concat":
            self.proj = nn.Sequential(
                nn.Conv1d(num_branches * channels, channels, kernel_size=1, bias=False),
                Norm1D(channels, kind=norm_kind),
                nn.ELU(),
                nn.Dropout(dropout),
            )
        elif self.fusion == "sum":
            self.proj = nn.Identity()
        elif self.fusion in {"attn", "moe"}:
            self.gate = nn.Sequential(
                nn.Linear(num_branches * channels, gate_hidden),
                nn.GELU(),
                nn.Linear(gate_hidden, num_branches),
            )
            self.proj = nn.Identity()
        else:
            raise ValueError(
                f"Unsupported stem fusion: {fusion}. Use concat, sum, attn, or moe."
            )

    def forward(
        self,
        xs: Sequence[torch.Tensor],
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        if len(xs) != self.num_branches:
            raise ValueError(f"Expected {self.num_branches} branches, got {len(xs)}.")

        branch_weights: Optional[torch.Tensor] = None

        if self.fusion == "concat":
            x = torch.cat(xs, dim=1)
            x = self.proj(x)
            return x, branch_weights

        if self.fusion == "sum":
            x = torch.stack(xs, dim=0).sum(dim=0)
            return x, branch_weights

        # attn / moe: both are implemented as lightweight branch-scale gates.
        summaries = [x.mean(dim=-1) for x in xs]  # each: [B, channels]
        gate_input = torch.cat(summaries, dim=-1)
        logits = self.gate(gate_input)
        branch_weights = torch.softmax(logits, dim=-1)  # [B, K]

        stacked = torch.stack(xs, dim=1)  # [B, K, channels, T]
        x = (stacked * branch_weights[:, :, None, None]).sum(dim=1)
        return x, branch_weights


class MultiBranchTemporalStem(nn.Module):
    """
    Multi-scale per-electrode temporal stem.

    Input:
        x: [B, C, T]

    Output:
        y: [B, C*Fper, T']
        aux: optional diagnostics
    """

    def __init__(
        self,
        C: int,
        Fper: int,
        sampling_rate: int = 128,
        window_sec: float = 5.0,
        kernel_sizes: Optional[Sequence[int]] = None,
        kernel_durations: Sequence[float] = (0.125, 0.25, 0.5),
        stride: int = 2,
        fusion: str = "concat",
        dropout: float = 0.05,
        norm_kind: str = "gn",
        max_kernel_fraction: float = 0.25,
    ):
        super().__init__()
        self.C = C
        self.Fper = Fper
        self.sampling_rate = sampling_rate
        self.window_sec = window_sec
        self.stride = stride

        timelen = int(round(window_sec * sampling_rate))
        max_kernel = max(7, int(round(max_kernel_fraction * timelen)))

        if kernel_sizes is None:
            kernel_sizes = kernel_sizes_from_durations(
                kernel_durations,
                sampling_rate=sampling_rate,
                max_kernel=max_kernel,
            )

        self.kernel_sizes = [_make_odd(k) for k in kernel_sizes]

        self.branches = nn.ModuleList(
            [
                TemporalBranch(
                    C=C,
                    Fper=Fper,
                    kernel_size=k,
                    stride=stride,
                    dropout=dropout,
                    norm_kind=norm_kind,
                )
                for k in self.kernel_sizes
            ]
        )

        self.fusion = BranchFusion(
            num_branches=len(self.branches),
            channels=C * Fper,
            fusion=fusion,
            dropout=dropout,
            norm_kind=norm_kind,
        )

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        branch_outputs = [branch(x) for branch in self.branches]
        x, branch_weights = self.fusion(branch_outputs)

        aux: Dict[str, torch.Tensor] = {}
        if branch_weights is not None:
            aux["stem_branch_weights"] = branch_weights

        return x, aux


# ============================================================
# Temporal TCN blocks
# ============================================================


class TCNBlockDW(nn.Module):
    """
    Depthwise/grouped temporal residual block.

    The design keeps electrode groups separated by using groups=C.
    """

    def __init__(
        self,
        C: int,
        Fper: int,
        dilation: int,
        dropout: float = 0.1,
        kernel_size: int = 3,
        norm_kind: str = "gn",
    ):
        super().__init__()
        channels = C * Fper
        padding = dilation * (kernel_size // 2)

        self.norm1 = Norm1D(channels, kind=norm_kind)
        self.conv1 = nn.Conv1d(
            channels,
            channels,
            kernel_size=kernel_size,
            padding=padding,
            dilation=dilation,
            groups=C,
            bias=False,
        )
        self.norm2 = Norm1D(channels, kind=norm_kind)
        self.mix = nn.Conv1d(channels, channels, kernel_size=1, groups=C, bias=False)
        self.drop = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = x

        x = self.norm1(x)
        x = F.elu(x)
        x = self.conv1(x)

        x = self.norm2(x)
        x = F.elu(x)
        x = self.mix(x)
        x = self.drop(x)

        return x + residual


class TCNStackDW(nn.Module):
    """Stack of grouped depthwise temporal residual blocks."""

    def __init__(
        self,
        C: int,
        Fper: int,
        dilations: Sequence[int],
        dropout: float = 0.1,
        kernel_size: int = 3,
        norm_kind: str = "gn",
    ):
        super().__init__()
        self.blocks = nn.ModuleList(
            [
                TCNBlockDW(
                    C=C,
                    Fper=Fper,
                    dilation=d,
                    dropout=dropout,
                    kernel_size=kernel_size,
                    norm_kind=norm_kind,
                )
                for d in dilations
            ]
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        for block in self.blocks:
            x = block(x)
        return x


class TemporalAttnPool1D(nn.Module):
    """
    Per-electrode learned temporal attention pooling.

    Input:
        x: [B, C*Fper, T]

    Output:
        h:     [B, C, Fper]
        alpha: [B, C, T]
    """

    def __init__(self, C: int, Fper: int):
        super().__init__()
        self.C = C
        self.Fper = Fper
        self.scorer = nn.Conv1d(C * Fper, C, kernel_size=1, groups=C, bias=True)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        batch_size, channels, timesteps = x.shape

        expected_channels = self.C * self.Fper
        if channels != expected_channels:
            raise ValueError(f"Expected {expected_channels} channels, got {channels}.")

        scores = self.scorer(x)  # [B, C, T]
        alpha = torch.softmax(scores, dim=-1)

        x4 = x.view(batch_size, self.C, self.Fper, timesteps)
        h = (x4 * alpha.unsqueeze(2)).sum(dim=-1)  # [B, C, Fper]

        return h, alpha


# ============================================================
# Channel position embeddings and channel mixer
# ============================================================


class ChannelPositionEmbedding(nn.Module):
    """
    Channel identity / position embedding.

    Modes:
        - none: no embedding
        - learnable: learned [C, D] channel embedding
        - coord: coordinate MLP; requires coordinates
    """

    def __init__(
        self,
        C: int,
        D: int,
        mode: str = "learnable",
        coord_dim: int = 3,
        coords: Optional[torch.Tensor] = None,
    ):
        super().__init__()
        self.C = C
        self.D = D
        self.mode = mode.lower()
        self.coord_dim = coord_dim

        if self.mode == "none":
            self.emb = None
            self.coord_mlp = None

        elif self.mode == "learnable":
            self.emb = nn.Parameter(torch.zeros(C, D))
            nn.init.trunc_normal_(self.emb, std=0.02)
            self.coord_mlp = None

        elif self.mode == "coord":
            self.emb = None
            self.coord_mlp = nn.Sequential(
                nn.Linear(coord_dim, D),
                nn.GELU(),
                nn.Linear(D, D),
            )

            if coords is not None:
                if coords.shape != (C, coord_dim):
                    raise ValueError(
                        f"coords must have shape {(C, coord_dim)}, got {tuple(coords.shape)}"
                    )
                self.register_buffer("coords", coords.float())
            else:
                self.coords = None

        else:
            raise ValueError("channel_pos_mode must be one of: none, learnable, coord")

    def forward(
        self,
        h: torch.Tensor,
        coords: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        # h: [B, C, D]
        if self.mode == "none":
            return h

        if self.mode == "learnable":
            return h + self.emb[None, :, :]

        # coord mode
        if coords is None:
            coords = getattr(self, "coords", None)
        if coords is None:
            raise ValueError("Coordinate mode requires coords either in init or forward.")

        pos = self.coord_mlp(coords.to(device=h.device, dtype=h.dtype))  # [C, D]
        return h + pos[None, :, :]


class ChannelMixer(nn.Module):
    """
    Channel self-attention block.

    Modes:
        - none: linear projection only
        - mha: MultiheadAttention over channel tokens
        - graph_bias: MHA with optional additive attention mask / bias

    Input:
        h: [B, C, Fin]

    Output:
        x: [B, C, D]
    """

    def __init__(
        self,
        Fin: int,
        D: int = 64,
        nheads: int = 4,
        dropout: float = 0.1,
        mode: str = "mha",
    ):
        super().__init__()
        self.mode = mode.lower()
        self.projin = nn.Linear(Fin, D)

        if self.mode in {"mha", "graph_bias"}:
            self.attn = nn.MultiheadAttention(
                embed_dim=D,
                num_heads=nheads,
                dropout=dropout,
                batch_first=True,
            )
            self.ln1 = nn.LayerNorm(D)
            self.ffn = nn.Sequential(
                nn.Linear(D, 2 * D),
                nn.ELU(),
                nn.Dropout(dropout),
                nn.Linear(2 * D, D),
                nn.Dropout(dropout),
            )
            self.ln2 = nn.LayerNorm(D)

        elif self.mode == "none":
            self.attn = None
            self.ln1 = nn.LayerNorm(D)
            self.ffn = None
            self.ln2 = None

        else:
            raise ValueError("channel_mixer must be one of: none, mha, graph_bias")

    def forward(
        self,
        h: torch.Tensor,
        graph_bias: Optional[torch.Tensor] = None,
        need_weights: bool = False,
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        x = self.projin(h)  # [B, C, D]

        if self.mode == "none":
            return self.ln1(x), None

        attn_mask = None
        if self.mode == "graph_bias" and graph_bias is not None:
            # PyTorch MHA attn_mask is additive. Shape can be [C, C].
            # Negative values suppress attention; zero means no bias.
            attn_mask = graph_bias.to(device=x.device, dtype=x.dtype)

        attn_out, attn_weights = self.attn(
            x,
            x,
            x,
            attn_mask=attn_mask,
            need_weights=need_weights,
            average_attn_weights=False,
        )

        x = self.ln1(x + attn_out)
        xffn = self.ffn(x)
        x = self.ln2(x + xffn)

        return x, attn_weights


class ChannelAttnPool(nn.Module):
    """Attention pooling over EEG channel tokens."""

    def __init__(self, D: int, dropout: float = 0.1):
        super().__init__()
        self.score = nn.Linear(D, 1)
        self.drop = nn.Dropout(dropout)

    def forward(self, h: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        # h: [B, C, D]
        logits = self.score(h).squeeze(-1)  # [B, C]
        alpha = torch.softmax(logits, dim=-1).unsqueeze(-1)

        z = (h * alpha).sum(dim=1)
        z = self.drop(z)

        return z, alpha.squeeze(-1)


# ============================================================
# Optional spectral branch
# ============================================================


class SpectralEncoder(nn.Module):
    """
    Optional encoder for precomputed spectral features.

    Input:
        x_spec: [B, C, num_bands]

    Output:
        z_spec: [B, Dembed]

    Spectral features should be computed outside the model so preprocessing
    remains fold-aware and reproducible.
    """

    def __init__(
        self,
        C: int,
        num_bands: int,
        Dembed: int,
        hidden: int = 64,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.C = C
        self.num_bands = num_bands

        self.band_mlp = nn.Sequential(
            nn.LayerNorm(num_bands),
            nn.Linear(num_bands, hidden),
            nn.GELU(),
            nn.Dropout(dropout),
        )

        self.channel_pool = nn.Linear(hidden, 1)

        self.proj = nn.Sequential(
            nn.LayerNorm(hidden),
            nn.Linear(hidden, Dembed),
            nn.GELU(),
        )

    def forward(self, x_spec: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        if x_spec.ndim != 3:
            raise ValueError(
                f"x_spec must be [B, C, num_bands], got {tuple(x_spec.shape)}"
            )

        _, C, num_bands = x_spec.shape
        if C != self.C or num_bands != self.num_bands:
            raise ValueError(
                f"Expected [B, {self.C}, {self.num_bands}], got {tuple(x_spec.shape)}"
            )

        h = self.band_mlp(x_spec)  # [B, C, hidden]

        logits = self.channel_pool(h).squeeze(-1)  # [B, C]
        alpha = torch.softmax(logits, dim=-1).unsqueeze(-1)

        pooled = (h * alpha).sum(dim=1)
        z = self.proj(pooled)

        return z, alpha.squeeze(-1)


class EmbeddingFusion(nn.Module):
    """Fuse raw EEG embedding and optional spectral embedding."""

    def __init__(self, D: int, mode: str = "concat", dropout: float = 0.1):
        super().__init__()
        self.mode = mode.lower()

        if self.mode == "concat":
            self.fuse = nn.Sequential(
                nn.LayerNorm(2 * D),
                nn.Linear(2 * D, D),
                nn.GELU(),
                nn.Dropout(dropout),
            )

        elif self.mode == "gate":
            self.gate = nn.Sequential(
                nn.LayerNorm(2 * D),
                nn.Linear(2 * D, D),
                nn.Sigmoid(),
            )

        else:
            raise ValueError("spectral_fusion must be concat or gate")

    def forward(
        self,
        z_raw: torch.Tensor,
        z_spec: torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        x = torch.cat([z_raw, z_spec], dim=-1)

        if self.mode == "concat":
            z = self.fuse(x)
            gate = torch.empty(0, device=z.device)
            return z, gate

        gate = self.gate(x)
        z = gate * z_raw + (1.0 - gate) * z_spec
        return z, gate


# ============================================================
# EEG segment encoder
# ============================================================


def eeg_preset(modelsize: str = "lite", timelen: int = 640) -> Dict[str, Union[int, List[int]]]:
    """
    Small preset dictionary.

    Defaults are conservative for DEAP / I-DARE 4-6 second windows.
    """
    modelsize = modelsize.lower()

    if modelsize == "lite":
        return {
            "Fper": 8,
            "Dgat": 32,
            "nheads": 2,
            "Dembed": 128,
            "dilations": [1, 2, 4, 8, 16, 32]
            if timelen <= 768
            else [1, 2, 4, 8, 16, 32, 64],
        }

    if modelsize == "base":
        return {
            "Fper": 16,
            "Dgat": 64,
            "nheads": 4,
            "Dembed": 256,
            "dilations": [1, 2, 4, 8, 16, 32, 64],
        }

    raise ValueError("modelsize must be 'lite' or 'base'")


class EEGSegmentEncoder(nn.Module):
    """
    EEG segment encoder V1.

    This is the first-stage EEG-only backbone:
        - no EMG
        - no trial sequence encoder
        - no contrastive loss inside the model
        - optional spectral branch is supported but disabled by default

    Input:
        x_eeg:  [B, C, T]
        x_spec: optional [B, C, num_bands]

    Output:
        z:   [B, Dembed]
        aux: dictionary with embeddings and attention diagnostics
    """

    def __init__(
        self,
        C: int = 32,
        sampling_rate: int = 128,
        window_sec: float = 5.0,
        modelsize: str = "lite",
        dropout: float = 0.1,
        norm_kind: str = "gn",
        # Temporal stem
        temporal_kernel_sizes: Optional[Sequence[int]] = None,
        temporal_kernel_durations: Sequence[float] = (0.125, 0.25, 0.5),
        stem_stride: int = 2,
        stem_fusion: str = "concat",
        # Channel position / mixer
        channel_pos_mode: str = "learnable",
        channel_coord_dim: int = 3,
        channel_coords: Optional[torch.Tensor] = None,
        channel_mixer: str = "mha",
        # Optional spectral branch
        use_spectral_branch: bool = False,
        num_spectral_bands: int = 5,
        spectral_fusion: str = "concat",
        use_temp_pools: bool = False,
    ):
        super().__init__()
        self.C = C
        self.sampling_rate = sampling_rate
        self.window_sec = window_sec
        self.timelen = int(round(sampling_rate * window_sec))
        self.modelsize = modelsize
        self.use_spectral_branch = use_spectral_branch

        cfg = eeg_preset(modelsize=modelsize, timelen=self.timelen)
        self.Fper = int(cfg["Fper"])
        self.Dgat = int(cfg["Dgat"])
        self.nheads = int(cfg["nheads"])
        self.Dembed = int(cfg["Dembed"])
        self.dilations = list(cfg["dilations"])

        self.stem = MultiBranchTemporalStem(
            C=C,
            Fper=self.Fper,
            sampling_rate=sampling_rate,
            window_sec=window_sec,
            kernel_sizes=temporal_kernel_sizes,
            kernel_durations=temporal_kernel_durations,
            stride=stem_stride,
            fusion=stem_fusion,
            dropout=0.05,
            norm_kind=norm_kind,
        )

        self.pool1 = nn.AvgPool1d(4) if use_temp_pools else nn.Identity()

        self.tcn = TCNStackDW(
            C=C,
            Fper=self.Fper,
            dilations=self.dilations,
            dropout=dropout,
            kernel_size=3,
            norm_kind=norm_kind,
        )

        self.pool2 = nn.AvgPool1d(4) if use_temp_pools else nn.Identity()

        self.tpool = TemporalAttnPool1D(C=C, Fper=self.Fper)

        self.channel_pos = ChannelPositionEmbedding(
            C=C,
            D=self.Fper,
            mode=channel_pos_mode,
            coord_dim=channel_coord_dim,
            coords=channel_coords,
        )

        self.channel_mixer = ChannelMixer(
            Fin=self.Fper,
            D=self.Dgat,
            nheads=self.nheads,
            dropout=dropout,
            mode=channel_mixer,
        )

        self.cpool = ChannelAttnPool(D=self.Dgat, dropout=dropout)

        self.proj = nn.Sequential(
            nn.LayerNorm(self.Dgat),
            nn.Linear(self.Dgat, self.Dembed),
            nn.GELU(),
        )

        if use_spectral_branch:
            self.spec_encoder = SpectralEncoder(
                C=C,
                num_bands=num_spectral_bands,
                Dembed=self.Dembed,
                hidden=max(32, self.Dembed // 2),
                dropout=dropout,
            )
            self.spec_fusion = EmbeddingFusion(
                D=self.Dembed,
                mode=spectral_fusion,
                dropout=dropout,
            )
        else:
            self.spec_encoder = None
            self.spec_fusion = None

    def forward(
        self,
        x_eeg: torch.Tensor,
        x_spec: Optional[torch.Tensor] = None,
        channel_coords: Optional[torch.Tensor] = None,
        graph_bias: Optional[torch.Tensor] = None,
        return_attn: bool = False,
    ) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        if x_eeg.ndim != 3:
            raise ValueError(f"x_eeg must be [B, C, T], got {tuple(x_eeg.shape)}")

        _, C, _ = x_eeg.shape
        if C != self.C:
            raise ValueError(f"Expected C={self.C}, got C={C}")

        aux: Dict[str, torch.Tensor] = {}

        x, stem_aux = self.stem(x_eeg)
        aux.update(stem_aux)

        x = self.pool1(x)
        x = self.tcn(x)
        x = self.pool2(x)

        h, temporal_attn = self.tpool(x)  # [B, C, Fper]
        h = self.channel_pos(h, coords=channel_coords)

        h, channel_mha = self.channel_mixer(
            h,
            graph_bias=graph_bias,
            need_weights=return_attn,
        )

        z_raw, channel_pool_attn = self.cpool(h)
        z_raw = self.proj(z_raw)

        z = z_raw

        if self.use_spectral_branch:
            if x_spec is None:
                raise ValueError("use_spectral_branch=True requires x_spec [B, C, num_bands].")

            z_spec, spec_channel_attn = self.spec_encoder(x_spec)
            z, spec_gate = self.spec_fusion(z_raw, z_spec)

            aux["z_raw"] = z_raw
            aux["z_spec"] = z_spec
            aux["spectral_channel_attn"] = spec_channel_attn

            if spec_gate.numel() > 0:
                aux["spectral_gate"] = spec_gate

        aux["z"] = z
        aux["temporal_attn"] = temporal_attn
        aux["channel_pool_attn"] = channel_pool_attn

        if channel_mha is not None:
            aux["channel_mha_attn"] = channel_mha

        return z, aux


if __name__ == "__main__":
    torch.manual_seed(7)

    encoder = EEGSegmentEncoder(
        C=32,
        sampling_rate=128,
        window_sec=5.0,
        modelsize="lite",
    )

    x = torch.randn(4, 32, 640)
    z, aux = encoder(x, return_attn=True)

    print("z:", z.shape)
    print("temporal_attn:", aux["temporal_attn"].shape)
    print("channel_pool_attn:", aux["channel_pool_attn"].shape)
