import io

import numpy as np
import pytest
from PIL import Image

from app.services.query_router import RuleBasedRouter
from conftest import ask

BA, BB = "demo-before-after-a", "demo-before-after-b"


def _png(arr):
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, "PNG")
    return buf.getvalue()


def test_health(client):
    j = client.get("/api/health").json()
    assert j["status"] == "ok" and j["cache"] in ("memory", "redis")


def test_demo_datasets_listed(client):
    ids = {d["id"] for d in client.get("/api/demo/datasets").json()}
    assert {"urban", "water", "agriculture", "before-after", "disaster"} <= ids


@pytest.mark.parametrize("q,intent,n", [
    ("What objects are visible?", "object_detection", 1), ("How much vegetation is present?", "segmentation", 1),
    ("Where is the water?", "segmentation", 1), ("What changed?", "change_detection", 2), ("How many buildings?", "object_detection", 1),
    ("Compare these images.", "change_detection", 2), ("Explain this image.", "image_understanding", 1), ("Show me regions affected by flooding.", "flood_assessment", 1),
])
def test_query_routing(q, intent, n):
    i = RuleBasedRouter().route(q, True, False)
    assert i.intent == intent and (i.required_images == n or intent == "flood_assessment")


def test_upload_validation(client):
    assert client.post("/api/upload", files={"file": ("a.txt", b"hi", "text/plain")}).json()["error"]["code"] == "unsupported_type"
    assert client.post("/api/upload", files={"file": ("a.png", b"not a png", "image/png")}).json()["error"]["code"] == "invalid_image"
    ok = client.post("/api/upload", files={"file": ("../../evil name.png", _png(np.random.randint(0, 255, (300, 300, 3), np.uint8)), "image/png")})
    assert ok.status_code == 200 and "/" not in ok.json()["name"] and ok.json()["geo"]["georeferenced"] is False


def test_geotiff_metadata(client):
    rasterio = pytest.importorskip("rasterio")
    from rasterio.io import MemoryFile
    from rasterio.transform import from_bounds
    arr = np.random.randint(0, 255, (3, 200, 300), np.uint8)
    with MemoryFile() as mf:
        with mf.open(driver="GTiff", height=200, width=300, count=3, dtype="uint8", crs="EPSG:4326", transform=from_bounds(77, 28, 77.1, 28.05, 300, 200)) as d:
            d.write(arr)
        data = mf.read()
    r = client.post("/api/upload", files={"file": ("geo.tif", data, "image/tiff")}).json()
    assert r["geo"]["georeferenced"] and r["geo"]["crs"] == "EPSG:4326" and r["geo"]["bounds"][0] == pytest.approx(77)


def test_object_detection(client):
    r = ask(client, "How many buildings are visible?")
    assert r["intent"]["intent"] == "object_detection" and r["evidence"]["count"] == 12 and len(r["visualization"]["boxes"]) == 12
    assert r["is_demo"] and "Prototype" in r["engine_label"] and r["confidence_tier"] == "high" and "12 buildings" in r["answer"]


def test_segmentation(client):
    r = ask(client, "What percentage of the image is vegetation?")
    assert r["evidence"]["stats"]["area_pct"] > 50 and r["visualization"]["masks"][0]["mask_png"].startswith("data:image/png")
    assert ask(client, "Show me the water bodies.")["evidence"]["stats"]["area_pct"] > 1


def test_change_detection(client):
    r = ask(client, "What changed between these two images?", BA, BB)
    s = r["evidence"]["stats"]
    assert (s["total_regions"], s["significant_regions"], s["significant_types"]["new_construction"]) == (18, 7, 3)
    assert r["visualization"]["change_mask_png"]


def test_missing_second_image(client):
    r = ask(client, "What changed?", BA)
    assert r["status"] == "needs_input" and "two images" in r["answer"]


def test_insufficient_evidence(client):
    r = ask(client, "Are there any aircraft?")
    assert r["status"] == "insufficient" and "Insufficient visual evidence" in r["answer"]
    blank = client.post("/api/upload", files={"file": ("blank.png", _png(np.full((300, 300, 3), 128, np.uint8)), "image/png")}).json()
    assert blank["quality"]["warnings"]
    r = ask(client, "How many buildings are visible?", blank["id"])
    assert r["status"] == "insufficient" and "Insufficient visual evidence" in r["answer"]


def test_unknown_query_is_friendly(client):
    r = ask(client, "sing me a song")
    assert r["status"] == "unsupported" and "Traceback" not in r["answer"]


def test_followup_context(client):
    sid = "s-test-followup"
    ask(client, "How many buildings changed?", BA, BB, sid)
    new = ask(client, "Which ones are new?", BA, BB, sid)
    assert new["intent"]["intent"] == "followup_new_items" and new["evidence"]["count"] == 3
    shown = ask(client, "Show them.", BA, BB, sid)
    assert len(shown["visualization"]["highlight_ids"]) == 3
    assert "IoU" in ask(client, "What evidence supports this answer?", BA, BB, sid)["answer"]


def test_history_report_geojson(client):
    r = ask(client, "How many buildings are visible?")
    assert client.get(f"/api/analysis/{r['id']}").json()["id"] == r["id"]
    assert "<h1>" in client.get(f"/api/report/{r['id']}").text
    assert client.get(f"/api/analysis/{r['id']}/geojson").json()["type"] == "FeatureCollection"
    assert client.get("/api/history").json() and client.get("/api/stats").json()["queries_executed"] > 0
    assert any(m["status"] == "planned" for m in client.get("/api/models").json()["models"])


def test_path_traversal_and_bad_ids(client):
    assert client.get("/api/image/..%2F..%2Fetc%2Fpasswd").status_code in (400, 404, 422)
    assert client.post("/api/query", json={"query": "x", "image_id": "../x"}).status_code == 422
