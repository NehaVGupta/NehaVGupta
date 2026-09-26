"""Pixel <-> geographic helpers. Falls back to pixel coordinates when no georeferencing exists."""


def pixel_to_geo(geo, w, h, x, y):
    """Linear interpolation across the image bounds (north-up rasters). Returns None if not georeferenced."""
    if not geo or not geo.get("bounds"):
        return None
    l, b, r, t = geo["bounds"]
    return [round(l + (x / w) * (r - l), 6), round(t - (y / h) * (t - b), 6)]


def bbox_to_geo(geo, w, h, bbox):
    p1 = pixel_to_geo(geo, w, h, bbox[0], bbox[1])
    p2 = pixel_to_geo(geo, w, h, bbox[2], bbox[3])
    return [p1, p2] if p1 and p2 else None
