"""Dataset loaders for EmotionRecognitionDEAP-I-DARE."""

from .idare_loader import IDARETrialDataset, IDAREPaths, build_idare_dataframe, summarize_dataset

__all__ = ["IDARETrialDataset", "IDAREPaths", "build_idare_dataframe", "summarize_dataset"]
