import base64

import cv2
import numpy as np

from app.engines.features import mask_to_polygons

COLORS = {"water": (56, 189, 248), "vegetation": (74, 222, 128), "built_up": (251, 146, 60), "roads": (250, 204, 21), "bare_soil": (180, 130, 90)}


def mask_png(mask, rgb, alpha=140):
    rgba = np.zeros((*mask.shape, 4), np.uint8)
    rgba[mask > 0] = (*rgb[::-1], alpha)  # BGRA for cv2
    ok, buf = cv2.imencode(".png", rgba)
    return "data:image/png;base64," + base64.b64encode(buf.tobytes()).decode()


class SegmentationService:
    def __init__(self, registry, images, cache):
        self.reg, self.images, self.cache = registry, images, cache

    def analyze(self, image_id, cls):
        key = f"seg:{self.reg.get('segmentation').name}:{image_id}:{cls}"
        hit = self.cache.get(key)
        if hit is not None:
            return hit
        r = self.reg.run("segmentation", self.images.load_bgr(image_id), cls)
        mask = r["mask"]
        out = {"class": cls, "area_px": int(mask.sum()), "area_pct": round(float(mask.mean()) * 100, 2), "confidence": r["confidence"],
               "polygons": mask_to_polygons(mask), "mask_png": mask_png(mask, COLORS[cls]), "color": "#%02x%02x%02x" % COLORS[cls]}
        self.cache.set(key, out)
        return out
