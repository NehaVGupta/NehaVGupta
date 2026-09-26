import re

from fastapi import APIRouter, File, Request, Response, UploadFile
from fastapi.responses import HTMLResponse

from app import deps
from app.config.settings import settings
from app.schemas.api import AnalysisRecord, AnalyzeRequest, QueryRequest
from app.services import metadata_service, report_service
from app.services.demo_data import DATASETS
from app.services.query_router import Intent
from app.utils.errors import UserError

router = APIRouter(prefix="/api")
public_router = APIRouter(prefix="/api")
_ID = re.compile(r"^[A-Za-z0-9\-]{3,48}$")


def _id(v):
    if not _ID.match(v):
        raise UserError("Invalid id.", "invalid_id")
    return v


def _user_id(request):
    return request.state.auth_user["id"]


def _image_for_user(image_id, user_id):
    image = deps.images.meta(_id(image_id))
    if image.get("synthetic") is not True and image.get("owner_user_id") != user_id:
        raise UserError("The requested image was not found.", "not_found", 404)
    return image


def _analysis_for_user(analysis_id, user_id):
    analysis_id = _id(analysis_id)
    if not deps.repo.exists("analysis_index", analysis_id):
        raise UserError("The requested analysis was not found.", "not_found", 404)
    index = deps.repo.get("analysis_index", analysis_id)
    if index.get("owner_user_id") != user_id:
        raise UserError("The requested analysis was not found.", "not_found", 404)
    return deps.repo.get("analysis", analysis_id)


def _record_owner(record, user_id):
    index = deps.repo.get("analysis_index", record["id"])
    index["owner_user_id"] = user_id
    deps.repo.put("analysis_index", record["id"], index)
    return record


@public_router.get("/health")
def health():
    return {"status": "ok", "version": settings.version, "cache": deps.cache.backend, "storage": settings.storage_backend,
            "rasterio": metadata_service.HAS_RASTERIO, "engines": {k: m.name for k, m in deps.registry.models.items()}}


@router.post("/upload")
def upload(request: Request, file: UploadFile = File(...)):
    data = file.file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    image = deps.images.ingest(data, file.filename or "upload")
    image["owner_user_id"] = _user_id(request)
    deps.repo.put("image_meta", image["id"], image)
    return {key: value for key, value in image.items() if key != "owner_user_id"}


@router.get("/image/{image_id}")
def image(image_id: str, request: Request):
    _image_for_user(image_id, _user_id(request))
    return Response(deps.images.png_bytes(_id(image_id)), media_type="image/png", headers={"Cache-Control": "private, no-store"})


@router.get("/image/{image_id}/meta")
def image_meta(image_id: str, request: Request):
    image = _image_for_user(image_id, _user_id(request))
    return {key: value for key, value in image.items() if key != "owner_user_id"}


@router.get("/demo/datasets")
def demo_datasets():
    return deps.demo.list()


@router.post("/demo/load/{name}")
def demo_load(name: str):
    return deps.demo.load(name)


@router.post("/query", response_model=AnalysisRecord)
def query(req: QueryRequest, request: Request):
    user_id = _user_id(request)
    _image_for_user(req.image_id, user_id)
    if req.image_b_id:
        _image_for_user(req.image_b_id, user_id)
    record = deps.orchestrator.handle(req.query, req.image_id, req.image_b_id, req.session_id)
    return _record_owner(record, user_id)


def _analyze(req: AnalyzeRequest, intent: Intent, label: str, request: Request):
    user_id = _user_id(request)
    _image_for_user(req.image_id, user_id)
    if req.image_b_id:
        _image_for_user(req.image_b_id, user_id)
    record = deps.orchestrator.handle(label, req.image_id, req.image_b_id, req.session_id, forced=intent)
    return _record_owner(record, user_id)


@router.post("/analyze", response_model=AnalysisRecord)
def analyze(req: AnalyzeRequest, request: Request):
    t = req.analysis_type
    if t == "object_detection":
        return analyze_detect(req, request)
    if t == "segmentation":
        return analyze_segment(req, request)
    if t == "change_detection":
        return analyze_change(req, request)
    return _analyze(req, Intent("image_understanding", 1, "scene_summary"), "Explain this image.", request)


@router.post("/analyze/detect", response_model=AnalysisRecord)
def analyze_detect(req: AnalyzeRequest, request: Request):
    classes = [req.target] if req.target else []
    return _analyze(req, Intent("object_detection", 1, "object_detection", {"classes": classes}), f"Detect {req.target or 'objects'}", request)


@router.post("/analyze/segment", response_model=AnalysisRecord)
def analyze_segment(req: AnalyzeRequest, request: Request):
    cls = req.target or "vegetation"
    if cls not in ("water", "vegetation", "built_up", "roads", "bare_soil"):
        raise UserError("Unsupported segmentation class. Choose water, vegetation, built_up, roads or bare_soil.", "unsupported_class")
    return _analyze(req, Intent("segmentation", 1, "land_cover_segmentation", {"class": cls}), f"Segment {cls}", request)


@router.post("/analyze/change", response_model=AnalysisRecord)
def analyze_change(req: AnalyzeRequest, request: Request):
    return _analyze(req, Intent("change_detection", 2, "temporal_comparison", {}), "Analyze changes between the two images", request)


@router.get("/analysis/{analysis_id}", response_model=AnalysisRecord)
def get_analysis(analysis_id: str, request: Request):
    return _analysis_for_user(analysis_id, _user_id(request))


@router.get("/analysis/{analysis_id}/geojson")
def geojson(analysis_id: str, request: Request):
    rec = _analysis_for_user(analysis_id, _user_id(request))
    return report_service.to_geojson(rec, deps.images.meta(rec["image_ids"]["b"] if rec["visualization"].get("view") == "B" and rec["image_ids"]["b"] else rec["image_ids"]["a"]))


@router.get("/report/{analysis_id}", response_class=HTMLResponse)
def report(analysis_id: str, request: Request):
    rec = _analysis_for_user(analysis_id, _user_id(request))
    iid = rec["image_ids"]["b"] if rec["visualization"].get("view") == "B" and rec["image_ids"]["b"] else rec["image_ids"]["a"]
    uri = report_service.render_evidence_image(deps.images.load_bgr(iid), rec["visualization"])
    return HTMLResponse(report_service.build_html(rec, uri), headers={"Content-Disposition": f'attachment; filename="satquery-report-{analysis_id}.html"'})


@router.get("/history")
def history(request: Request, limit: int = 50, include_demo: bool = True):
    user_id = _user_id(request)
    items = [item for item in deps.repo.list("analysis_index") if item.get("owner_user_id") == user_id]
    if not include_demo:
        items = _without_demo_data(items)
    return [{key: value for key, value in item.items() if key != "owner_user_id"}
            for item in items[: max(1, min(limit, 200))]]


def _without_demo_data(items):
    demo_image_ids = {item["id"] for item in deps.repo.list("image_meta") if item.get("synthetic")}
    return [item for item in items if not item.get(
        "includes_demo_data",
        any(image_id in demo_image_ids for image_id in item.get("image_ids", {}).values() if image_id),
    )]


@router.get("/stats")
def stats(request: Request, include_demo: bool = True):
    user_id = _user_id(request)
    idx = [item for item in deps.repo.list("analysis_index") if item.get("owner_user_id") == user_id]
    if not include_demo:
        idx = _without_demo_data(idx)
    confs = [i["confidence"] for i in idx if i.get("confidence") is not None and i["status"] in ("high", "moderate")]
    imgs = {v for i in idx for v in i["image_ids"].values() if v}
    det, chg = {}, {}  # count each image (pair) once, so repeated questions don't inflate totals
    for i in idx:
        k = (i["image_ids"]["a"], i["image_ids"]["b"])
        det[k] = max(det.get(k, 0), i.get("objects_detected", 0))
        chg[k] = max(chg.get(k, 0), i.get("changes_detected", 0))

    owned_images = [image for image in deps.repo.list("image_meta") if image.get("owner_user_id") == user_id and not image.get("synthetic")]
    return {"images_analyzed": len(imgs), "queries_executed": len(idx), "objects_detected": sum(det.values()), "changes_detected": sum(chg.values()),
            "avg_confidence": round(sum(confs) / len(confs), 3) if confs else None, "datasets": len(DATASETS), "uploads": len(owned_images)}


@router.get("/models")
def models():
    return {"models": deps.registry.describe(), "cache": deps.cache.backend, "storage": settings.storage_backend}
