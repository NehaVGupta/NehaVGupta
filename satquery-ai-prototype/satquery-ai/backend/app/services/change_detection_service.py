import base64

import cv2
import numpy as np


class ChangeDetectionService:
    def __init__(self, registry, images, cache):
        self.reg, self.images, self.cache = registry, images, cache

    def analyze(self, a_id, b_id):
        key = f"chg:{self.reg.get('change_detection').name}:{a_id}:{b_id}"
        hit = self.cache.get(key)
        if hit is not None:
            return hit
        r = self.reg.run("change_detection", self.images.load_bgr(a_id), self.images.load_bgr(b_id))
        mask, regions = r["mask"], r["regions"]
        h, w = mask.shape
        sig, minor = np.zeros((h, w), np.uint8), np.zeros((h, w), np.uint8)
        for reg in regions:  # colour by significance
            x1, y1, x2, y2 = reg["bbox"]
            sub = mask[y1:y2, x1:x2]
            (sig if reg["significant"] else minor)[y1:y2, x1:x2] |= sub
        both = np.zeros((h, w, 4), np.uint8)
        both[minor > 0] = (36, 191, 251, 120)
        both[sig > 0] = (68, 68, 239, 150)
        ok, buf = cv2.imencode(".png", both)
        out = {"regions": regions, "changed_px": int(mask.sum()), "changed_pct": round(float(mask.mean()) * 100, 2),
               "mask_png": "data:image/png;base64," + base64.b64encode(buf.tobytes()).decode(),
               "registration": r["registration"], "diff_threshold": r["diff_threshold"], "notes": r["notes"],
               "significant_min_area_px": r["significant_min_area_px"]}
        self.cache.set(key, out)
        return out
