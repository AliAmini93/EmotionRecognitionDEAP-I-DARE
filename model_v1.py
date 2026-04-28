import math
        if self.projection is not None:
            z_proj = F.normalize(self.projection(z), dim=-1)
            aux["z_proj"] = z_proj

        return logits, aux


class OldStyleEEGClassifier(nn.Module):
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
        return logits, {"z": z, "logits": logits}


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

    x = torch.randn(8, 32, 640)
    logits, aux = model(x, return_attn=True)
    print("logits:", logits.shape)
    print("z:", aux["z"].shape)
    print("temporal attn:", aux["temporal_attn"].shape)
    print("channel pool attn:", aux["channel_pool_attn"].shape)

    spec_model = EEGSegmentClassifier(
        C=32,
        sampling_rate=128,
        window_sec=5.0,
        n_classes=2,
        modelsize="lite",
        use_spectral_branch=True,
        num_spectral_bands=5,
        spectral_fusion="concat",
    )
    x_spec = torch.randn(8, 32, 5)
    logits2, aux2 = spec_model(x, x_spec=x_spec)
    print("logits with spec:", logits2.shape)
