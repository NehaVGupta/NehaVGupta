import os
import sys
import tempfile
from pathlib import Path

os.environ["SATQUERY_DATA_DIR"] = tempfile.mkdtemp(prefix="satquery_test_")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    c = TestClient(app)
    for d in ("urban", "before-after", "water"):
        assert c.post(f"/api/demo/load/{d}").status_code == 200
    return c


def ask(client, q, a="demo-urban-a", b=None, sid=None):
    body = {"query": q, "image_id": a, **({"image_b_id": b} if b else {}), **({"session_id": sid} if sid else {})}
    r = client.post("/api/query", json=body)
    assert r.status_code == 200, r.text
    return r.json()
