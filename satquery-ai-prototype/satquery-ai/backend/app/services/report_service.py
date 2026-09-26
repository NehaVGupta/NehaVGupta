"""Downloadable HTML report ("Save Findings") and GeoJSON export."""
import base64
import html

import cv2
import numpy as np


def _decode_png(data_url):
    raw = base64.b64decode(data_url.split(",", 1)[1])
    return cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_UNCHANGED)


def render_evidence_image(img_bgr, viz):
    out = img_bgr.copy()
    for m in viz.get("masks", []) + ([{"mask_png": viz["change_mask_png"]}] if viz.get("change_mask_png") else []):
        rgba = _decode_png(m["mask_png"])
        if rgba is not None and rgba.shape[:2] == out.shape[:2]:
            a = rgba[..., 3:4].astype(np.float32) / 255
            out = (out * (1 - a) + rgba[..., :3] * a).astype(np.uint8)
    for b in viz.get("boxes", []) + viz.get("change_regions", []):
        x1, y1, x2, y2 = b["bbox"]
        cv2.rectangle(out, (x1, y1), (x2, y2), (0, 255, 255), 2)
        cv2.putText(out, f"{b['id']} {round(b.get('confidence', 0) * 100)}%", (x1, max(12, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1, cv2.LINE_AA)
    ok, buf = cv2.imencode(".png", out)
    return "data:image/png;base64," + base64.b64encode(buf.tobytes()).decode()


def build_html(rec, img_uri):
    e = html.escape
    ev = rec["evidence"]
    rows = "".join(f"<tr><td>{e(i['id'])}</td><td>{e(str(i['label']))}</td><td>{round(i['confidence'] * 100)}%</td><td>{i['bbox']}</td><td>{e(str(i.get('geo_bbox') or 'pixel coords only'))}</td></tr>" for i in ev.get("items", []))
    steps = "".join(f"<li><b>{e(s['stage'])}</b> — {e(s['detail'])} <i>({s['ms']} ms)</i></li>" for s in rec["pipeline"])
    conf = "n/a" if rec["confidence"] is None else f"{round(rec['confidence'] * 100)}%"
    warn = "".join(f"<li>{e(w)}</li>" for w in rec["warnings"])
    return f"""<!doctype html><meta charset=utf-8><title>SatQuery AI report {rec['id']}</title>
<style>body{{font:15px/1.5 system-ui;max-width:900px;margin:2rem auto;padding:0 1rem;color:#111}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ccc;padding:4px 8px;font-size:13px;text-align:left}}
.box{{background:#fff7e6;border:1px solid #f0c36d;padding:.6rem 1rem;border-radius:6px}}img{{max-width:100%}}</style>
<h1>SatQuery AI — analysis report</h1><p>Analysis <code>{rec['id']}</code> · {e(rec['created'])}</p>
<div class=box><b>{e(rec['disclaimer'])}</b> Engine: {e(rec['engine_label'])}.</div>
<h2>Question</h2><p>{e(rec['query'])}</p><h2>Answer</h2><p>{e(rec['answer'])}</p><p>Model confidence: <b>{conf}</b> ({e(rec['confidence_tier'])}) — not a measured accuracy.</p>
<h2>Visual evidence</h2><img src="{img_uri}" alt="evidence">
<h2>Evidence items ({ev.get('count', 0)})</h2><table><tr><th>ID</th><th>Label</th><th>Confidence</th><th>BBox (px)</th><th>Geo bbox</th></tr>{rows}</table>
<h2>Warnings</h2><ul>{warn or '<li>None</li>'}</ul><h2>How this answer was produced</h2><ol>{steps}</ol>"""


def to_geojson(rec, img):
    feats = []
    w, h, geo = img["width"], img["height"], img["geo"]

    def pt(x, y):
        if geo and geo.get("bounds"):
            l, b, r, t = geo["bounds"]
            return [round(l + x / w * (r - l), 7), round(t - y / h * (t - b), 7)]
        return [x, y]

    for it in rec["evidence"].get("items", []):
        poly = it.get("polygon")
        if poly:
            ring = [pt(*p) for p in poly]
        else:
            x1, y1, x2, y2 = it["bbox"]
            ring = [pt(x1, y1), pt(x2, y1), pt(x2, y2), pt(x1, y2)]
        ring.append(ring[0])
        feats.append({"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [ring]},
                      "properties": {"id": it["id"], "label": it["label"], "confidence": it["confidence"], "kind": it.get("kind")}})
    crs = "geographic (illustrative)" if geo.get("illustrative") else geo.get("crs") if geo.get("georeferenced") else "pixel coordinates"
    return {"type": "FeatureCollection", "properties": {"analysis": rec["id"], "coordinate_system": crs, "note": rec["disclaimer"]}, "features": feats}
