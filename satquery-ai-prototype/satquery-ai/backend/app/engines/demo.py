"""DEMO / PROTOTYPE engines.

These implement the model interfaces with classical computer-vision heuristics (colour-space
segmentation, connected components, Lab-space differencing). They are deterministic, need no GPU and
run on any laptop. They are NOT trained deep-learning models and are labelled as such in the UI.
"""
import cv2
import numpy as np

from .base import ChangeDetectionModel, ObjectDetectionModel, SegmentationModel, VisionLanguageModel
from .features import class_masks

LABEL = "Prototype inference · classical CV heuristics (not a trained model)"
MIN_BLOB = 250
K3 = np.ones((3, 3), np.uint8)


class DemoObjectDetectionModel(ObjectDetectionModel):
    name = "DemoObjectDetectionModel"
    label = LABEL
    supported_classes = ["building", "vehicle", "ship", "agricultural_structure"]

    def predict(self, bgr):
        H, W = bgr.shape[:2]
        m = class_masks(bgr)
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        n, lab, st, _ = cv2.connectedComponentsWithStats(m["built_up"], connectivity=8)
        objs = []
        for i in range(1, n):
            x, y, w, h, area = (int(v) for v in st[i])
            if area < MIN_BLOB:
                continue
            x0, y0, x1, y1 = max(0, x - 14), max(0, y - 14), min(W, x + w + 14), min(H, y + h + 14)
            blob = (lab[y0:y1, x0:x1] == i).astype(np.uint8)
            ring = (cv2.dilate(blob, np.ones((15, 15), np.uint8)) > 0) & (blob == 0)
            rs = max(int(ring.sum()), 1)
            f_water = (m["water"][y0:y1, x0:x1] & ring).sum() / rs
            f_road = (m["roads"][y0:y1, x0:x1] & ring).sum() / rs
            if f_water > 0.5 and area < 6000:
                cls = "ship"
            elif area < 1000 and f_road > 0.3:
                cls = "vehicle"
            elif area < 1000:
                cls = "agricultural_structure"
            else:
                cls = "building"
            cs, _ = cv2.findContours(blob, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            c = max(cs, key=cv2.contourArea)
            (_, _), (rw, rh), _ = cv2.minAreaRect(c)
            rect = float(np.clip(cv2.contourArea(c) / max(rw * rh, 1), 0, 1))
            g = gray[y0:y1, x0:x1]
            contrast = abs(float(g[blob > 0].mean()) - float(g[ring].mean())) / 255.0 if ring.any() else 0.0
            conf = 0.42 + 0.33 * rect + 0.22 * min(1.0, contrast * 3)
            if x <= 1 or y <= 1 or x + w >= W - 1 or y + h >= H - 1:
                conf *= 0.9  # truncated by image border
            objs.append({"class": cls, "confidence": round(float(min(conf, 0.97)), 3),
                         "bbox": [x, y, x + w, y + h], "area_px": area, "rectangularity": round(rect, 3)})
        objs.sort(key=lambda o: (o["bbox"][1], o["bbox"][0]))
        for k, o in enumerate(objs):
            o["id"] = f"det-{k + 1}"
        return objs


class DemoSegmentationModel(SegmentationModel):
    name = "DemoSegmentationModel"
    label = LABEL
    classes = ["water", "vegetation", "built_up", "roads", "bare_soil"]

    def predict(self, bgr, cls):
        mask = class_masks(bgr)[cls]
        area = int(mask.sum())
        if area == 0:
            return {"mask": mask, "confidence": 0.0}
        edge = int(cv2.morphologyEx(mask, cv2.MORPH_GRADIENT, K3).sum())
        conf = float(np.clip(0.98 - 0.6 * edge / area, 0.3, 0.97))  # mask-consistency score, uncalibrated
        return {"mask": mask, "confidence": round(conf, 3)}


def _dominant(masks, region):
    best, frac = "other", 0.4
    tot = max(int(region.sum()), 1)
    for k, m in masks.items():
        f = float((m.astype(bool) & region).sum()) / tot
        if f > frac:
            best, frac = k, f
    return best


def _change_type(a, b):
    if b == "water" and a != "water":
        return "water_increase"
    if a == "water" and b != "water":
        return "water_decrease"
    if b == "built_up" and a != "built_up":
        return "new_construction"
    if a == "built_up" and b != "built_up":
        return "structure_removed"
    if a == "vegetation" and b != "vegetation":
        return "vegetation_loss"
    if b == "vegetation" and a != "vegetation":
        return "vegetation_gain"
    return "surface_change"


class DemoChangeDetectionModel(ChangeDetectionModel):
    name = "DemoChangeDetectionModel"
    label = LABEL

    def predict(self, a, b):
        H, W = a.shape[:2]
        notes = []
        if b.shape[:2] != (H, W):
            b = cv2.resize(b, (W, H), interpolation=cv2.INTER_AREA)
            notes.append("Images had different dimensions; the second image was resampled.")
        reg = {"dx": 0.0, "dy": 0.0, "response": 0.0, "applied": False}
        ga, gb = (cv2.cvtColor(x, cv2.COLOR_BGR2GRAY).astype(np.float32) for x in (a, b))
        (dx, dy), resp = cv2.phaseCorrelate(ga, gb)
        reg.update(dx=round(float(dx), 2), dy=round(float(dy), 2), response=round(float(resp), 3))
        if resp > 0.3 and 0.5 < max(abs(dx), abs(dy)) <= 20:
            b = cv2.warpAffine(b, np.float32([[1, 0, -dx], [0, 1, -dy]]), (W, H), borderMode=cv2.BORDER_REPLICATE)
            reg["applied"] = True
            notes.append(f"Translation co-registration applied ({dx:.1f}px, {dy:.1f}px).")
        la = cv2.cvtColor(cv2.GaussianBlur(a, (5, 5), 0), cv2.COLOR_BGR2LAB).astype(np.float32)
        lb = cv2.cvtColor(cv2.GaussianBlur(b, (5, 5), 0), cv2.COLOR_BGR2LAB).astype(np.float32)
        diff = np.linalg.norm(la - lb, axis=2)
        med = float(np.median(diff))
        mad = float(np.median(np.abs(diff - med)))
        thr = float(np.clip(med + 4 * 1.4826 * mad, 22.0, 40.0))  # robust to large-scale change
        mask = (diff > thr).astype(np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, K3)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        ma, mb = class_masks(a), class_masks(b)
        min_area, sig_area = max(120, int(0.0002 * H * W)), int(0.001 * H * W)
        n, lab, st, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
        regions = []
        for i in range(1, n):
            x, y, w, h, area = (int(v) for v in st[i])
            if area < min_area:
                mask[lab == i] = 0
                continue
            region = lab == i
            md = float(diff[region].mean())
            fa, fb = _dominant(ma, region), _dominant(mb, region)
            conf = (0.45 + 0.5 * min(1.0, md / (3 * thr))) * (0.85 + 0.15 * min(1.0, area / 600))
            conf = float(min(conf, 0.96))
            if not reg["applied"] and resp < 0.05:
                conf *= 0.95
            regions.append({"bbox": [x, y, x + w, y + h], "area_px": area, "mean_diff": round(md, 1),
                            "from_class": fa, "to_class": fb, "type": _change_type(fa, fb),
                            "confidence": round(conf, 3), "significant": bool(area >= sig_area and conf >= 0.6)})
        regions.sort(key=lambda r: -r["area_px"])
        for k, r in enumerate(regions):
            r["id"] = f"chg-{k + 1}"
        return {"mask": mask, "regions": regions, "registration": reg, "diff_threshold": round(thr, 1), "notes": notes,
                "significant_min_area_px": sig_area}


class DemoSceneCaptioner(VisionLanguageModel):
    """NOT a vision-language model. Template captioner over structured evidence."""
    name = "DemoSceneCaptioner"
    label = "Template captioner over measured evidence (not a VLM)"

    def describe(self, ev):
        parts = [f"{k.replace('_', ' ')} {v:.0f}%" for k, v in sorted(ev["coverage"].items(), key=lambda kv: -kv[1]) if v >= 1]
        objs = [f"{n} {k.replace('_', ' ')}{'s' if n != 1 else ''}" for k, n in ev["counts"].items() if n]
        s = "Measured scene composition: " + (", ".join(parts) if parts else "no dominant land-cover class")
        s += ". Detected objects: " + (", ".join(objs) if objs else "none above the detection threshold") + "."
        return s
