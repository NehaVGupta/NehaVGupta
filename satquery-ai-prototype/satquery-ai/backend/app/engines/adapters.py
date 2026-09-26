"""Adapters for REAL models. They are intentionally NOT installed or downloaded by default.

To integrate a real model: `pip install -r requirements-ml.txt`, download weights yourself, implement
`predict` below, then set SATQUERY_DETECTOR=yolo (etc.). See docs/architecture.md.
"""
from .base import ChangeDetectionModel, ObjectDetectionModel, SegmentationModel, VisionLanguageModel


class _Planned:
    is_demo = False
    status = "planned"
    label = "Real model adapter (not installed)"

    def _todo(self):
        raise NotImplementedError(f"{self.name} is a planned adapter. See docs/architecture.md for integration steps.")


class YOLOObjectDetectionModel(_Planned, ObjectDetectionModel):
    name = "YOLO (ultralytics) — planned"
    supported_classes = ["building", "vehicle", "ship", "aircraft"]

    def predict(self, image_bgr):  # e.g. ultralytics.YOLO('weights.pt')(image)[0].boxes
        self._todo()


class SegFormerSegmentationModel(_Planned, SegmentationModel):
    name = "SegFormer / U-Net — planned"

    def predict(self, image_bgr, cls):  # e.g. transformers.SegformerForSemanticSegmentation
        self._todo()


class SiameseUNetChangeDetectionModel(_Planned, ChangeDetectionModel):
    name = "Siamese U-Net / transformer CD — planned"

    def predict(self, before_bgr, after_bgr):
        self._todo()


class HFVisionLanguageModel(_Planned, VisionLanguageModel):
    name = "GeoChat-style remote-sensing VLM — planned"

    def describe(self, evidence):
        self._todo()


class OpticalSARFusionModel(_Planned, ChangeDetectionModel):
    name = "Optical/SAR fusion — planned"

    def predict(self, before_bgr, after_bgr):
        self._todo()
