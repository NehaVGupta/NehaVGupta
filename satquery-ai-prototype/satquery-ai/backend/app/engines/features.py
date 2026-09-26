"""Classical colour-space features used by the prototype engines."""
import cv2
import numpy as np

_K3 = np.ones((3, 3), np.uint8)
CLASSES = ["water", "vegetation", "built_up", "roads", "bare_soil"]


def _clean(m, min_area=0):
    m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, _K3)
    if min_area:
        n, lab, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
        keep = np.zeros(n, bool)
        keep[1:] = st[1:, cv2.CC_STAT_AREA] >= min_area
        m = keep[lab].astype(np.uint8)
    return m


def class_masks(bgr):
    """Return {class: uint8 mask} using HSV/ExG heuristics. Deterministic; not a trained model."""
    img = cv2.GaussianBlur(bgr, (3, 3), 0)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h = hsv[..., 0].astype(np.int16)
    s = hsv[..., 1] / 255.0
    v = hsv[..., 2] / 255.0
    b, g, r = (img[..., i].astype(np.int16) for i in range(3))
    water = (h >= 90) & (h <= 130) & (s > 0.2) & (v > 0.12)
    veg = (h >= 38) & (h <= 85) & (s > 0.15) & (g > r) & (g >= b)
    road = (s < 0.18) & (v > 0.12) & (v < 0.55)
    light = (s < 0.2) & (v >= 0.6)
    warm = ((h <= 35) | (h >= 170)) & (s > 0.35) & (v > 0.55)
    bare = (h >= 5) & (h <= 30) & (s >= 0.2) & (s <= 0.75) & (v >= 0.25) & (v < 0.55)
    built = (light | warm) & ~veg & ~water
    return {
        "water": _clean(water, 40),
        "vegetation": _clean(veg, 40),
        "built_up": _clean(built),
        "roads": _clean(road & ~built, 300),
        "bare_soil": _clean(bare, 40),
    }


def mask_to_polygons(mask, min_area=80, max_polys=60, eps=2.5):
    cs, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cs = sorted(cs, key=cv2.contourArea, reverse=True)[:max_polys]
    out = []
    for c in cs:
        if cv2.contourArea(c) < min_area:
            continue
        ap = cv2.approxPolyDP(c, eps, True)
        if len(ap) >= 3:
            out.append([[int(p[0][0]), int(p[0][1])] for p in ap])
    return out
