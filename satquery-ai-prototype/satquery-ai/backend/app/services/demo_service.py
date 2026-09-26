from app.config.settings import settings

from .demo_data import DATASETS, ensure_demo_data


class DemoService:
    def __init__(self, images):
        self.images = images

    def list(self):
        ensure_demo_data()
        return [{"id": k, "title": d["title"], "category": d["category"], "description": d["description"], "images": len(d["files"]),
                 "suggested_questions": d["suggested"], "synthetic": True} for k, d in DATASETS.items()]

    def load(self, name):
        from app.utils.errors import UserError

        if name not in DATASETS:
            raise UserError("Unknown demo dataset.", "not_found", 404)
        ensure_demo_data()
        d, out = DATASETS[name], []
        for fname, role in d["files"]:
            geo = {"georeferenced": True, "illustrative": True, "crs": "EPSG:4326 (illustrative)", "bounds": d["bounds"], "transform": None, "bands": 3,
                   "gsd_m": d["gsd"], "note": "SYNTHETIC demo image — illustrative georeference and 1 m/px scale; not a real location or real satellite imagery."}
            data = (settings.demo_dir / name / fname).read_bytes()
            rec = self.images.ingest(data, fname, image_id=f"demo-{name}-{role}", synthetic=True, geo_override=geo,
                                     note="Synthetic demo image (not real satellite imagery)")
            rec["role"] = role
            out.append(rec)
        return {"dataset": {"id": name, "title": d["title"], "description": d["description"], "suggested_questions": d["suggested"]}, "images": out}
