"""Synthetic demo dataset generator.

ALL images produced here are SYNTHETIC illustrations drawn with OpenCV/NumPy. They are NOT real satellite
imagery and the UI labels them as such. Run:  python -m app.services.demo_data
"""
import cv2
import numpy as np

from app.config.settings import settings

W, H = 960, 640
# BGR colours
LAWN, ROAD = (62, 138, 72), (72, 72, 76)
ROOF_L, ROOF_L2, ROOF_T = (214, 214, 220), (198, 200, 206), (70, 100, 190)
WATER, SOIL = (170, 112, 42), (52, 92, 128)
RED, WHITE, YELLOW = (30, 30, 200), (240, 240, 240), (40, 200, 230)


def _canvas(seed, base=LAWN):
    rng = np.random.default_rng(seed)
    img = np.full((H, W, 3), base, np.uint8).astype(np.float32)
    tex = cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 9) * 18
    img[..., 1] += tex
    return img, rng


def _finish(img, rng):
    img = img + rng.normal(0, 2.5, img.shape).astype(np.float32)
    return np.clip(img, 0, 255).astype(np.uint8)


def _rect(img, x, y, w, h, c):
    cv2.rectangle(img, (x, y), (x + w - 1, y + h - 1), c, -1, cv2.LINE_8)


def _urban_roads(img):
    for y in (200, 420):
        _rect(img, 0, y, W, 26, ROAD)
    for x in (290, 640):
        _rect(img, x, 0, 26, H, ROAD)


URBAN_BUILDINGS = [(40, 40, 70, 50, ROOF_L), (150, 60, 60, 60, ROOF_T), (340, 30, 80, 55, ROOF_L), (470, 70, 60, 45, ROOF_L2),
                   (700, 50, 90, 60, ROOF_T), (830, 40, 60, 80, ROOF_L), (50, 260, 80, 70, ROOF_L), (170, 300, 70, 60, ROOF_T),
                   (360, 270, 75, 80, ROOF_L), (720, 280, 90, 70, ROOF_T), (380, 490, 90, 60, ROOF_L2), (520, 500, 70, 70, ROOF_T)]


def urban():
    img, rng = _canvas(1)
    _urban_roads(img)
    cv2.ellipse(img, (810, 540), (110, 60), 0, 0, 360, WATER, -1)
    for b in URBAN_BUILDINGS:
        _rect(img, *b)
    _rect(img, 100, 207, 30, 12, RED)
    _rect(img, 500, 428, 30, 12, WHITE)
    _rect(img, 297, 120, 12, 30, YELLOW)
    return _finish(img, rng)


def water():
    img, rng = _canvas(2)
    m = np.zeros((H, W), np.uint8)
    for c, a in [((330, 300), (230, 130)), ((520, 330), (150, 110)), ((250, 380), (130, 90))]:
        cv2.ellipse(m, c, a, 15, 0, 360, 1, -1)
    cv2.polylines(m, [np.array([(520, 330), (650, 400), (760, 470), (960, 520)])], False, 1, 34)
    img[m > 0] = WATER
    for x, y in [(230, 280), (380, 320), (300, 400), (480, 330)]:
        _rect(img, x, y, 38, 13, WHITE)
    for b in [(700, 90, 80, 55, ROOF_L), (820, 200, 70, 60, ROOF_T), (90, 90, 75, 55, ROOF_L2)]:
        _rect(img, *b)
    _rect(img, 40, 500, 200, 90, SOIL)
    return _finish(img, rng)


def agriculture():
    img, rng = _canvas(3)
    greens = [(60, 150, 80), (55, 135, 95), (70, 160, 100), (50, 125, 70)]
    k = 0
    for gx in range(0, W, 240):
        for gy in range(0, H, 213):
            c = SOIL if (gx // 240 + gy // 213) % 4 == 1 else greens[k % 4]
            k += 1
            _rect(img, gx + 6, gy + 6, 228, 201, c)
    _rect(img, 0, 300, W, 16, ROAD)
    cv2.ellipse(img, (840, 560), (60, 35), 0, 0, 360, WATER, -1)
    for x, y in [(90, 90), (560, 120), (330, 460)]:
        _rect(img, x, y, 34, 22, ROOF_T if x != 560 else ROOF_L)
    return _finish(img, rng)


def _outskirts(seed, base_buildings):
    img, rng = _canvas(seed)
    for y in (230,):
        _rect(img, 0, y, W, 24, ROAD)
    _rect(img, 460, 0, 24, H, ROAD)
    for b in base_buildings:
        _rect(img, *b)
    return img, rng


BA_BUILDINGS = [(60, 60, 80, 60, ROOF_L), (200, 90, 70, 60, ROOF_T), (560, 60, 80, 55, ROOF_L2),
                (100, 320, 70, 65, ROOF_T), (620, 320, 80, 60, ROOF_L), (760, 460, 70, 60, ROOF_T)]
NEW_BUILDINGS = [(240, 350, 70, 60, ROOF_L), (680, 110, 75, 60, ROOF_T), (540, 470, 80, 65, ROOF_L2)]
VEG_LOSS = [(330, 60, 60, 45), (780, 320, 55, 40), (60, 470, 60, 40), (380, 520, 55, 45)]
SMALL = [(20, 170), (150, 200), (330, 200), (410, 320), (500, 300), (600, 200), (700, 240), (820, 170), (880, 420), (300, 580), (140, 570)]


def before_after():
    before, rng = _outskirts(4, BA_BUILDINGS)
    ra = np.random.default_rng(5)
    after = before.copy()
    for b in NEW_BUILDINGS:
        _rect(after, *b)
    for x, y, w, h in VEG_LOSS:
        _rect(after, x, y, w, h, SOIL)
    for i, (x, y) in enumerate(SMALL):
        _rect(after, x, y, 14, 14, SOIL if i % 2 == 0 else (150, 150, 155) if i % 3 else RED)
    return _finish(before, rng), _finish(after, ra)


def disaster():
    def scene(seed, width):
        img, rng = _canvas(seed)
        _rect(img, 0, 90, W, 22, ROAD)
        pts = np.array([(0, 330), (250, 310), (500, 350), (740, 320), (960, 340)])
        cv2.polylines(img, [pts], False, WATER, width)
        for b in [(80, 200, 70, 55, ROOF_L), (300, 190, 65, 55, ROOF_T), (520, 200, 70, 60, ROOF_L2), (760, 190, 70, 55, ROOF_T),
                  (120, 500, 75, 60, ROOF_L), (450, 510, 70, 55, ROOF_T), (700, 500, 80, 60, ROOF_L2)]:
            _rect(img, *b)
        return img, rng

    (b, rb), (a, ra) = scene(6, 40), scene(6, 230)
    return _finish(b, rb), _finish(a, ra)


Q_URBAN = ["How many buildings are visible?", "Show me the detected buildings.", "Which detected regions have low confidence?",
           "What percentage of the image is vegetation?", "Show me the water bodies.", "Where are the roads?", "What evidence supports this answer?"]
Q_CHANGE = ["What changed between these two images?", "Where are the major change regions?", "How many buildings changed?",
            "Which ones are new?", "Show them.", "Highlight areas where vegetation decreased."]

DATASETS = {
    "urban": {"title": "Urban block", "category": "urban", "description": "Synthetic town: 12 buildings, road grid, 3 vehicles, pond, parkland.",
              "files": [("urban_scene.png", "a")], "suggested": Q_URBAN, "gsd": 1.0, "bounds": [77.1000, 28.5000, 77.1086, 28.5058]},
    "water": {"title": "Lake & river", "category": "water", "description": "Synthetic lake with river, 4 vessels, shoreline buildings, bare soil.",
              "files": [("water_scene.png", "a")], "suggested": ["Show me the water bodies.", "What objects are present in this image?", "What percentage of the image is vegetation?", "Are there any aircraft?"],
              "gsd": 1.0, "bounds": [77.2000, 28.6000, 77.2086, 28.6058]},
    "agriculture": {"title": "Farmland", "category": "agriculture", "description": "Synthetic field mosaic: crops, bare soil, farm track, 3 farm structures, pond.",
                    "files": [("agri_scene.png", "a")], "suggested": ["How much vegetation is present?", "Show me bare soil.", "What objects are present in this image?", "Explain this image."],
                    "gsd": 1.0, "bounds": [77.3000, 28.7000, 77.3086, 28.7058]},
    "before-after": {"title": "Urban growth (before / after)", "category": "change", "description": "Synthetic pair: 3 new buildings, 4 vegetation-loss patches, 11 minor surface changes.",
                     "files": [("before.png", "a"), ("after.png", "b")], "suggested": Q_CHANGE, "gsd": 1.0, "bounds": [77.4000, 28.8000, 77.4086, 28.8058]},
    "disaster": {"title": "Flood event (before / after)", "category": "disaster", "description": "Synthetic pair: river widens and inundates farmland and buildings.",
                 "files": [("before.png", "a"), ("after.png", "b")], "suggested": ["Show me regions affected by flooding.", "What changed between these two images?", "Explain why you think this region changed."],
                 "gsd": 1.0, "bounds": [77.5000, 28.9000, 77.5086, 28.9058]},
}


def build_all(root=None):
    root = root or settings.demo_dir
    out = {"urban": [urban()], "water": [water()], "agriculture": [agriculture()], "before-after": list(before_after()), "disaster": list(disaster())}
    for name, imgs in out.items():
        for img, (fname, _) in zip(imgs, DATASETS[name]["files"]):
            d = root / name
            d.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(d / fname), img)
    return root


def ensure_demo_data():
    if not all((settings.demo_dir / n / f).exists() for n, d in DATASETS.items() for f, _ in d["files"]):
        build_all()


if __name__ == "__main__":
    print("Generated synthetic demo data in", build_all())
