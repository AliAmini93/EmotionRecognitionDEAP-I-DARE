"""
Old-style EEG classifier wrapper.

This file contains:
    - OldStyleEEGClassifier

Use this class when you want to wrap an existing / previous EEG encoder
with a classification head for a clean baseline.
"""

from __future__ import annotations

from typing import Dict, Tuple

import torch
import torch.nn as nn


class OldStyleEEGClassifier(nn.Module):
    """
    Minimal classifier wrapper around an existing / old EEG encoder.

    Use this for the R0 baseline:
        old EEG encoder + classifier head

    The old encoder must return an embedding tensor:
        z = old_encoder(x_eeg)
        z shape: [B, d_embed]
    """

    def __init__(
        self,
        old_encoder: nn.Module,
        d_embed: int,
        n_classes: int = 2,
        head_dropout: float = 0.3,
    ):
        super().__init__()
        self.enc = old_encoder

        self.head = nn.Sequential(
            nn.LayerNorm(d_embed),
            nn.Linear(d_embed, 128),
            nn.ELU(),
            nn.Dropout(head_dropout),
            nn.Linear(128, n_classes),
        )

    def forward(self, x_eeg: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        z = self.enc(x_eeg)
        logits = self.head(z)

        return logits, {
            "z": z,
            "logits": logits,
        }


if __name__ == "__main__":
    torch.manual_seed(7)

    class DummyOldEncoder(nn.Module):
        def __init__(self, d_embed: int = 128):
            super().__init__()
            self.pool = nn.AdaptiveAvgPool1d(1)
            self.proj = nn.Linear(32, d_embed)

        def forward(self, x_eeg: torch.Tensor) -> torch.Tensor:
            # x_eeg: [B, C, T]
            x = self.pool(x_eeg).squeeze(-1)
            return self.proj(x)

    old_encoder = DummyOldEncoder(d_embed=128)
    model = OldStyleEEGClassifier(old_encoder=old_encoder, d_embed=128, n_classes=2)

    x = torch.randn(4, 32, 640)
    logits, aux = model(x)

    print("logits:", logits.shape)
    print("z:", aux["z"].shape)
