#!/usr/bin/env python3
"""
Audit local project setup.

This script checks:
- Python version
- PyTorch / CUDA / GPU availability
- Project paths
- Importability of the three EEG model classes
- A small GPU/CPU forward-pass smoke test
"""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path


def run_cmd(cmd: list[str]) -> str:
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
        return out.strip()
    except Exception as exc:
        return f"ERROR: {exc}"


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    src_root = project_root / "src"

    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))

    print("==== Local Setup Audit ====")
    print(f"project_root: {project_root}")
    print(f"python: {sys.version.split()[0]}")
    print(f"python_executable: {sys.executable}")
    print(f"platform: {platform.platform()}")
    print(f"git_version: {run_cmd(['git', '--version'])}")
    print(f"git_branch: {run_cmd(['git', 'branch', '--show-current'])}")

    print("\n==== Paths ====")
    paths = {
        "deap_root": Path("/mnt/HDD/AliWorks/DEAP"),
        "idare_root": Path("/mnt/HDD/AliWorks/I-DARE"),
        "src_root": src_root,
        "models_root": src_root / "emotion_deap_idare" / "models",
    }
    for name, path in paths.items():
        print(f"{name}: {path} | exists={path.exists()} | is_dir={path.is_dir()}")

    print("\n==== PyTorch / CUDA ====")
    import torch

    print(f"torch: {torch.__version__}")
    print(f"cuda_available: {torch.cuda.is_available()}")
    print(f"torch_cuda_version: {torch.version.cuda}")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda":
        print(f"gpu_name: {torch.cuda.get_device_name(0)}")
        print(f"gpu_count: {torch.cuda.device_count()}")

    print("\n==== Model Imports ====")
    from emotion_deap_idare.models.eeg_segment_encoder import EEGSegmentEncoder
    from emotion_deap_idare.models.eeg_segment_classifier import EEGSegmentClassifier
    from emotion_deap_idare.models.old_style_eeg_classifier import OldStyleEEGClassifier

    print(f"imported: {EEGSegmentEncoder.__name__}")
    print(f"imported: {EEGSegmentClassifier.__name__}")
    print(f"imported: {OldStyleEEGClassifier.__name__}")

    print("\n==== Forward Smoke Test ====")
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
    ).to(device)

    x = torch.randn(8, 32, 640, device=device)

    with torch.no_grad():
        logits, aux = model(x, return_attn=True)

    num_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

    print(f"device: {device}")
    print(f"input_shape: {tuple(x.shape)}")
    print(f"logits_shape: {tuple(logits.shape)}")
    print(f"z_shape: {tuple(aux['z'].shape)}")
    print(f"z_proj_shape: {tuple(aux['z_proj'].shape)}")
    print(f"temporal_attn_shape: {tuple(aux['temporal_attn'].shape)}")
    print(f"channel_pool_attn_shape: {tuple(aux['channel_pool_attn'].shape)}")
    print(f"num_params: {num_params}")
    print(f"trainable_params: {trainable_params}")
    print("smoke_test: OK")


if __name__ == "__main__":
    main()
