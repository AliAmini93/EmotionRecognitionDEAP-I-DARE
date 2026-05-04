"""
EEG segment classifier V1.

This file contains:
    - EEGSegmentClassifier

It depends on:
    - eeg_segment_encoder.py

Place this file in the same directory as eeg_segment_encoder.py.
"""

from __future__ import annotations

from typing import Dict, Optional, Sequence, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F

try:
    from .eeg_segment_encoder import EEGSegmentEncoder
except ImportError:
    from eeg_segment_encoder import EEGSegmentEncoder


class EEGSegmentClassifier(nn.Module):
    """
    EEG segment classifier V1.

    Default safe baseline:
        window_sec=5.0
        sampling_rate=128
        modelsize='lite'
        multi-branch temporal stem
        stem_fusion='concat'
        channel_pos_mode='learnable'
        channel_mixer='mha'
        norm_kind='gn'
        spectral branch disabled
    """

    def __init__(
        self,
        C: int = 32,
        sampling_rate: int = 128,
        window_sec: float = 5.0,
        n_classes: int = 2,
        modelsize: str = "lite",
        dropout: float = 0.1,
        head_dropout: float = 0.3,
        norm_kind: str = "gn",
        temporal_kernel_sizes: Optional[Sequence[int]] = None,
        temporal_kernel_durations: Sequence[float] = (0.125, 0.25, 0.5),
        stem_stride: int = 2,
        stem_fusion: str = "concat",
        channel_pos_mode: str = "learnable",
        channel_coord_dim: int = 3,
        channel_coords: Optional[torch.Tensor] = None,
        channel_mixer: str = "mha",
        use_spectral_branch: bool = False,
        num_spectral_bands: int = 5,
        spectral_fusion: str = "concat",
        use_projection_head: bool = True,
        projection_dim: int = 64,
    ):
        super().__init__()

        self.encoder = EEGSegmentEncoder(
            C=C,
            sampling_rate=sampling_rate,
            window_sec=window_sec,
            modelsize=modelsize,
            dropout=dropout,
            norm_kind=norm_kind,
            temporal_kernel_sizes=temporal_kernel_sizes,
            temporal_kernel_durations=temporal_kernel_durations,
            stem_stride=stem_stride,
            stem_fusion=stem_fusion,
            channel_pos_mode=channel_pos_mode,
            channel_coord_dim=channel_coord_dim,
            channel_coords=channel_coords,
            channel_mixer=channel_mixer,
            use_spectral_branch=use_spectral_branch,
            num_spectral_bands=num_spectral_bands,
            spectral_fusion=spectral_fusion,
        )

        D = self.encoder.Dembed

        self.head = nn.Sequential(
            nn.LayerNorm(D),
            nn.Linear(D, 128),
            nn.ELU(),
            nn.Dropout(head_dropout),
            nn.Linear(128, n_classes),
        )

        self.use_projection_head = use_projection_head
        if use_projection_head:
            self.projection = nn.Sequential(
                nn.LayerNorm(D),
                nn.Linear(D, 128),
                nn.GELU(),
                nn.Linear(128, projection_dim),
            )
        else:
            self.projection = None

    def forward(
        self,
        x_eeg: torch.Tensor,
        x_spec: Optional[torch.Tensor] = None,
        channel_coords: Optional[torch.Tensor] = None,
        graph_bias: Optional[torch.Tensor] = None,
        return_attn: bool = False,
    ) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        z, aux = self.encoder(
            x_eeg=x_eeg,
            x_spec=x_spec,
            channel_coords=channel_coords,
            graph_bias=graph_bias,
            return_attn=return_attn,
        )

        logits = self.head(z)

        aux["logits"] = logits
        aux["z"] = z

        if self.projection is not None:
            z_proj = F.normalize(self.projection(z), dim=-1)
            aux["z_proj"] = z_proj

        return logits, aux


if __name__ == "__main__":
    torch.manual_seed(7)

    model = EEGSegmentClassifier(
        C=32,
        sampling_rate=128,
        window_sec=5.0,
        n_classes=2,
        modelsize="lite",
        stem_fusion="concat",
        channel_pos_mode="learnable",
        channel_mixer="mha",
        norm_kind="gn",
        use_spectral_branch=False,
    )

    x = torch.randn(4, 32, 640)
    logits, aux = model(x, return_attn=True)

    print("logits:", logits.shape)
    print("z:", aux["z"].shape)
    print("temporal_attn:", aux["temporal_attn"].shape)
    print("channel_pool_attn:", aux["channel_pool_attn"].shape)
