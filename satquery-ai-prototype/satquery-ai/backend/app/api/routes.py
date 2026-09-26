import re

from fastapi import APIRouter, File, Response, UploadFile
from fastapi.responses import HTMLResponse

from app import deps
from app.config.settings import settings
from app.schemas.api import AnalysisRecord, AnalyzeRequest, QueryRequest
from app.services import metadata_service, report_service
from app.services.demo_data import DATASETS
from app.services.query_router import Intent
from app.utils.errors import UserError

router = APIRouter(prefix="/api")
_ID = re.compile(r"^[A-Za-z0-9\-]{3,48}$")


def _id(v):
    if not _ID.match(v):
        raise UserError("Invalid id.", "invalid_id")
    return v


@router.get("/health")
def health():
    return {"status": "ok", "version": settings.version, "cache": deps.cache.backend, "storage": settings.storage_backend,
            "rasterio": metadata_service.HAS_RASTERIO, "engines": {k: m.name for k, m in deps.registry.models.items()}}


@router.post("/upload")
def upload(file: UploadFile = File(...)):
    data = file.file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    return deps.images.ingest(data, file.filename or "upload")


@router.get("/image/{image_id}")
def image(image_id: str):
    return Response(deps.images.png_bytes(_id(image_id)), media_type="image/png", headers={"Cache-Control": "public, max-age=3600"})


@router.get("/image/{image_id}/meta")
def image_meta(image_id: str):
    return deps.images.meta(_id(image_id))


@router.get("/demo/datasets")
def demo_datasets():
    return deps.demo.list()


@router.post("/demo/load/{name}")
def demo_load(name: str):
    return deps.demo.load(name)


@router.post("/query", response_model=AnalysisRecord)
def query(req: QueryRequest):
    return deps.orchestrator.handle(req.query, req.image_id, req.image_b_id, req.session_id)


def _analyze(req: AnalyzeRequest, intent: Intent, label: str):
    return deps.orchestrator.handle(label, req.image_id, req.image_b_id, req.session_id, forced=intent)


@router.post("/analyze", response_model=AnalysisRecord)
def analyze(req: AnalyzeRequest):
    t = req.analysis_type
    if t == "object_detection":
        return analyze_detect(req)
    if t == "segmentation":
        return analyze_segment(req)
    if t == "change_detection":
        return analyze_change(req)
    return _analyze(req, Intent("image_understanding", 1, "scene_summary"), "Explain this image.")


@router.post("/analyze/detect", response_model=AnalysisRecord)
def analyze_detect(req: AnalyzeRequest):
    classes = [req.target] if req.target else []
    return _analyze(req, Intent("object_detection", 1, "object_detection", {"classes": classes}), f"Detect {req.target or 'objects'}")


@router.post("/analyze/segment", response_model=AnalysisRecord)
def analyze_segment(req: AnalyzeRequest):
    cls = req.target or "vegetation"
    if cls not in ("water", "vegetation", "built_up", "roads", "bare_soil"):
        raise UserError("Unsupported segmentation class. Choose water, vegetation, built_up, roads or bare_soil.", "unsupported_class")
    return _analyze(req, Intent("segmentation", 1, "land_cover_segmentation", {"class": cls}), f"Segment {cls}")


@router.post("/analyze/change", response_model=AnalysisRecord)
def analyze_change(req: AnalyzeRequest):
    return _analyze(req, Intent("change_detection", 2, "temporal_comparison", {}), "Analyze changes between the two images")


@router.get("/analysis/{analysis_id}", response_model=AnalysisRecord)
def get_analysis(analysis_id: str):
    return deps.repo.get("analysis", _id(analysis_id))


@router.get("/analysis/{analysis_id}/geojson")
def geojson(analysis_id: str):
    rec = deps.repo.get("analysis", _id(analysis_id))
    return report_service.to_geojson(rec, deps.images.meta(rec["image_ids"]["b"] if rec["visualization"].get("view") == "B" and rec["image_ids"]["b"] else rec["image_ids"]["a"]))


@router.get("/report/{analysis_id}", response_class=HTMLResponse)
def report(analysis_id: str):
    rec = deps.repo.get("analysis", _id(analysis_id))
    iid = rec["image_ids"]["b"] if rec["visualization"].get("view") == "B" and rec["image_ids"]["b"] else rec["image_ids"]["a"]
    uri = report_service.render_evidence_image(deps.images.load_bgr(iid), rec["visualization"])
    return HTMLResponse(report_service.build_html(rec, uri), headers={"Content-Disposition": f'attachment; filename="satquery-report-{analysis_id}.html"'})


@router.get("/history")
def history(limit: int = 50):
    return deps.repo.list("analysis_index")[: max(1, min(limit, 200))]


@router.get("/stats")
def stats():
    idx = deps.repo.list("analysis_index")
    confs = [i["confidence"] for i in idx if i.get("confidence") is not None and i["status"] in ("high", "moderate")]
    imgs = {v for i in idx for v in i["image_ids"].values() if v}
    det, chg = {}, {}  # count each image (pair) once, so repeated questions don't inflate totals
    for i in idx:
        k = (i["image_ids"]["a"], i["image_ids"]["b"])
        det[k] = max(det.get(k, 0), i.get("objects_detected", 0))
        chg[k] = max(chg.get(k, 0), i.get("changes_detected", 0))
    return {"images_analyzed": len(imgs), "queries_executed": len(idx), "objects_detected": sum(det.values()), "changes_detected": sum(chg.values()),
            "avg_confidence": round(sum(confs) / len(confs), 3) if confs else None, "datasets": len(DATASETS),
            "uploads": len([m for m in deps.repo.list("image_meta") if not m.get("synthetic")])}


@router.get("/models")
def models():
    return {"models": deps.registry.describe(), "cache": deps.cache.backend, "storage": settings.storage_backend}
