"""Dataset loaders for EmotionRecognitionDEAP-I-DARE."""

from .idare_loader import (
    IDAREPaths,
    IDARETrialDataset,
    build_idare_dataframe,
    labels_from_scores,
    normalize_label_policy,
    summarize_dataset,
)

__all__ = [
    "IDAREPaths",
    "IDARETrialDataset",
    "build_idare_dataframe",
    "labels_from_scores",
    "normalize_label_policy",
    "summarize_dataset",
]
