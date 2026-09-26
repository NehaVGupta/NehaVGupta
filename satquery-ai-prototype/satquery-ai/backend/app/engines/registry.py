"""Model registry: selects engines and records real latency / call metrics for the monitoring page."""
import logging
import time
from collections import defaultdict

from app.config.settings import settings

from . import adapters
from .demo import DemoChangeDetectionModel, DemoObjectDetectionModel, DemoSceneCaptioner, DemoSegmentationModel

log = logging.getLogger("satquery.engines")


class ModelRegistry:
    def __init__(self):
        self.models = {
            "object_detection": self._pick(settings.detector, DemoObjectDetectionModel(), adapters.YOLOObjectDetectionModel()),
            "segmentation": self._pick(settings.segmenter, DemoSegmentationModel(), adapters.SegFormerSegmentationModel()),
            "change_detection": self._pick(settings.change_detector, DemoChangeDetectionModel(), adapters.SiameseUNetChangeDetectionModel()),
            "vision_language": DemoSceneCaptioner(),
        }
        self.planned = [adapters.YOLOObjectDetectionModel(), adapters.SegFormerSegmentationModel(),
                        adapters.SiameseUNetChangeDetectionModel(), adapters.HFVisionLanguageModel(),
                        adapters.OpticalSARFusionModel()]
        self.metrics = defaultdict(lambda: {"calls": 0, "errors": 0, "total_ms": 0.0, "last_ms": None})

    @staticmethod
    def _pick(choice, demo, real):
        if choice != "demo":
            try:
                real.predict  # noqa: B018
                if real.status != "planned":
                    return real
            except Exception:  # noqa: BLE001
                pass
            log.warning("Requested engine %r is not available; falling back to the demo engine.", choice)
        return demo

    def get(self, kind):
        return self.models[kind]

    def run(self, kind, *args):
        model, m = self.models[kind], self.metrics[kind]
        t = time.perf_counter()
        try:
            return model.describe(*args) if kind == "vision_language" else model.predict(*args)
        except Exception:
            m["errors"] += 1
            raise
        finally:
            ms = (time.perf_counter() - t) * 1000
            m["calls"] += 1
            m["total_ms"] += ms
            m["last_ms"] = round(ms, 1)

    def describe(self):
        rows = []
        for kind, model in self.models.items():
            m = self.metrics[kind]
            rows.append({"kind": kind, "name": model.name, "label": model.label, "is_demo": model.is_demo,
                         "status": "active", "calls": m["calls"], "errors": m["errors"],
                         "avg_latency_ms": round(m["total_ms"] / m["calls"], 1) if m["calls"] else None,
                         "last_latency_ms": m["last_ms"]})
        for p in self.planned:
            rows.append({"kind": "planned", "name": p.name, "label": p.label, "is_demo": False, "status": "planned",
                         "calls": 0, "errors": 0, "avg_latency_ms": None, "last_latency_ms": None})
        return rows
