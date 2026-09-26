"""Ingestion, validation, quality checking and loading of images."""
import io
import re
import uuid
from collections import OrderedDict
from datetime import datetime, timezone

import cv2
import numpy as np
from PIL import Image, ImageOps

from app.config.settings import settings
from app.utils.errors import UserError

from . import metadata_service as meta

MAGIC = {".png": [b"\x89PNG"], ".jpg": [b"\xff\xd8"], ".jpeg": [b"\xff\xd8"], ".tif": [b"II*\x00", b"MM\x00*", b"II+\x00"], ".tiff": [b"II*\x00", b"MM\x00*", b"II+\x00"]}


def safe_filename(name: str) -> str:
    name = (name or "upload").replace("\\", "/").split("/")[-1]
    name = re.sub(r"[^A-Za-z0-9._\-]", "_", name)[:80]
    return name or "upload"


def quality_check(rgb):
    """Basic quality gate. Returns {score, warnings, stats}."""
    h, w = rgb.shape[:2]
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    std, mean = float(g.std()), float(g.mean())
    lap = float(cv2.Laplacian(g, cv2.CV_64F).var())
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    cloud = float(((hsv[..., 2] > 235) & (hsv[..., 1] < 25)).mean())
    warns, score = [], 1.0
    if min(h, w) < 256:
        warns.append("Image resolution is low. Analysis confidence may be reduced."); score -= 0.25
    if std < 8:
        warns.append("Very low contrast — the image may be blank, hazy or corrupted."); score -= 0.5
    if mean < 20 or mean > 240:
        warns.append("Image is almost entirely dark or bright — little usable detail."); score -= 0.4
    if lap < 5 and std >= 8:
        warns.append("Image appears blurry or heavily smoothed."); score -= 0.15
    if cloud > 0.25:
        warns.append(f"Possible cloud/haze cover ({cloud * 100:.0f}% of pixels). Cloud masking is planned but not implemented."); score -= 0.2
    return {"score": round(max(score, 0.0), 2), "warnings": warns,
            "stats": {"contrast_std": round(std, 1), "mean_brightness": round(mean, 1), "sharpness": round(lap, 1), "bright_low_sat_fraction": round(cloud, 3)}}


class ImageService:
    def __init__(self, storage, repo):
        self.storage, self.repo = storage, repo
        self._lru: OrderedDict = OrderedDict()

    def ingest(self, data: bytes, filename: str, image_id=None, synthetic=False, geo_override=None, note=None):
        if len(data) > settings.max_upload_mb * 1024 * 1024:
            raise UserError(f"File is too large (limit {settings.max_upload_mb} MB).", "file_too_large", 413)
        if not data:
            raise UserError("The uploaded file is empty.", "empty_file")
        name = safe_filename(filename)
        ext = "." + name.rsplit(".", 1)[-1].lower() if "." in name else ""
        if ext not in settings.allowed_ext:
            raise UserError("Unsupported file type. Please upload PNG, JPG or GeoTIFF.", "unsupported_type", 415)
        if not any(data.startswith(m) for m in MAGIC[ext]):
            raise UserError("The file content does not match its extension, or the image is corrupt.", "invalid_image", 422)
        try:
            if ext in (".tif", ".tiff"):
                rgb, geo = meta.read_geotiff(data)
            else:
                im = Image.open(io.BytesIO(data))
                im.verify()
                im = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")
                rgb, geo = np.array(im), dict(meta.PIXEL_ONLY)
        except UserError:
            raise
        except Exception as e:  # noqa: BLE001
            raise UserError("Could not read this image. It may be corrupt or in an unsupported variant.", "invalid_image", 422) from e
        oh, ow = rgb.shape[:2]
        if oh < 16 or ow < 16:
            raise UserError("Image is too small to analyse.", "image_too_small", 422)
        scale = 1.0
        if max(oh, ow) > settings.max_dim:
            scale = max(oh, ow) / settings.max_dim
            rgb = cv2.resize(rgb, (round(ow / scale), round(oh / scale)), interpolation=cv2.INTER_AREA)
        h, w = rgb.shape[:2]
        if geo_override:
            geo = geo_override
        elif geo.get("gsd_m"):
            geo["gsd_m"] = round(geo["gsd_m"] * scale, 4)
        iid = image_id or uuid.uuid4().hex[:16]
        ok, png = cv2.imencode(".png", cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
        self.storage.save(f"images/{iid}.png", png.tobytes())
        rec = {"id": iid, "name": name, "created": datetime.now(timezone.utc).isoformat(), "width": w, "height": h,
               "orig_width": ow, "orig_height": oh, "scale": round(scale, 3), "format": ext.lstrip(".").upper(),
               "size_bytes": len(data), "synthetic": synthetic, "geo": geo, "quality": quality_check(rgb),
               "url": f"/api/image/{iid}", "note": note}
        self.repo.put("image_meta", iid, rec)
        self._lru.pop(iid, None)
        return rec

    def meta(self, iid):
        return self.repo.get("image_meta", self._valid(iid))

    def png_bytes(self, iid):
        return self.storage.load(f"images/{self._valid(iid)}.png")

    def load_bgr(self, iid):
        iid = self._valid(iid)
        if iid in self._lru:
            self._lru.move_to_end(iid)
            return self._lru[iid]
        arr = cv2.imdecode(np.frombuffer(self.png_bytes(iid), np.uint8), cv2.IMREAD_COLOR)
        if arr is None:
            raise UserError("Stored image could not be decoded.", "invalid_image", 422)
        self._lru[iid] = arr
        while len(self._lru) > 8:
            self._lru.popitem(last=False)
        return arr

    @staticmethod
    def _valid(iid):
        if not re.fullmatch(r"[A-Za-z0-9\-]{3,48}", iid or ""):
            raise UserError("Invalid image id.", "invalid_id")
        return iid
