"""Geospatial metadata extraction (Rasterio when available) with graceful pixel-coordinate fallback."""
import io

import numpy as np

try:
    import rasterio
    from rasterio.io import MemoryFile

    HAS_RASTERIO = True
except Exception:  # noqa: BLE001
    HAS_RASTERIO = False

PIXEL_ONLY = {"georeferenced": False, "crs": None, "bounds": None, "transform": None, "bands": None, "gsd_m": None,
              "illustrative": False, "note": "No geographic metadata found — using pixel coordinates."}


def read_geotiff(data: bytes):
    """Return (rgb uint8 HxWx3, geo dict). Raises on unreadable input."""
    if not HAS_RASTERIO:
        from PIL import Image

        im = Image.open(io.BytesIO(data)).convert("RGB")
        return np.array(im), {**PIXEL_ONLY, "note": "Rasterio not installed — GeoTIFF read as a plain image; georeferencing ignored."}
    with MemoryFile(data) as mf, mf.open() as ds:
        n = ds.count
        idx = [1, 2, 3] if n >= 3 else [1, 1, 1]
        arr = ds.read(idx).astype(np.float32)
        out = np.zeros_like(arr)
        for i in range(3):
            b = arr[i]
            if ds.dtypes[idx[i] - 1] == "uint8":
                out[i] = b
            else:
                lo, hi = np.percentile(b, (2, 98))
                out[i] = np.clip((b - lo) / max(hi - lo, 1e-6), 0, 1) * 255
        rgb = np.transpose(out, (1, 2, 0)).astype(np.uint8)
        geo = dict(PIXEL_ONLY)
        geo.update(bands=n)
        if ds.crs and ds.transform and not ds.transform.is_identity:
            l, b_, r, t = ds.bounds
            gsd = abs(ds.transform.a)
            if ds.crs.is_geographic:
                gsd = gsd * 111320.0 * float(np.cos(np.radians((t + b_) / 2)))
            geo.update(georeferenced=True, crs=str(ds.crs), bounds=[l, b_, r, t], transform=list(ds.transform)[:6],
                       gsd_m=round(float(gsd), 4), note="Georeferenced GeoTIFF.")
        return rgb, geo
