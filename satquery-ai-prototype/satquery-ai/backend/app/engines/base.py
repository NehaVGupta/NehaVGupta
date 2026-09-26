"""Model interfaces. Any real model (YOLO, SegFormer, Siamese U-Net, GeoChat...) implements these."""
from abc import ABC, abstractmethod

import numpy as np


class BaseModel(ABC):
    name = "base"
    label = ""          # shown in the UI
    is_demo = True      # True => NOT a trained model
    status = "active"


class ObjectDetectionModel(BaseModel):
    supported_classes: list = []

    @abstractmethod
    def predict(self, image_bgr: np.ndarray) -> list[dict]:
        """Return [{class, confidence, bbox:[x1,y1,x2,y2], area_px}]"""


class SegmentationModel(BaseModel):
    classes: list = []

    @abstractmethod
    def predict(self, image_bgr: np.ndarray, cls: str) -> dict:
        """Return {mask: uint8 HxW (0/1), confidence: float}"""


class ChangeDetectionModel(BaseModel):
    @abstractmethod
    def predict(self, before_bgr: np.ndarray, after_bgr: np.ndarray) -> dict:
        """Return {mask, regions:[...], registration:{...}, diff_threshold}"""


class VisionLanguageModel(BaseModel):
    @abstractmethod
    def describe(self, evidence: dict) -> str:
        """Produce text ONLY from structured evidence."""
