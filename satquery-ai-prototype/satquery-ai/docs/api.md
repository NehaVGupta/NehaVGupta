# SatQuery AI — API reference

Base URL: `http://localhost:8000/api`. All error responses are `{"error": {"code": "...", "message": "..."}}`
with an appropriate HTTP status — the API never returns a raw Python traceback. Except for `/health`
and `/auth/*`, endpoints require a valid session cookie. State-changing authenticated requests also
require the matching `satquery_csrf` cookie and `X-CSRF-Token` header.

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness + active engine/cache/storage info |
| POST | `/auth/register` | Create an account; requires `full_name`, `email`, `password`, `confirm_password` |
| POST | `/auth/login` | Verify credentials, issue HttpOnly session cookie; optional `remember_me` |
| POST | `/auth/logout` | Revoke current session and clear auth cookies |
| GET | `/auth/me` | Current authenticated user's public profile |
| POST | `/auth/forgot-password` | Request a reset link; always returns a generic confirmation |
| POST | `/auth/reset-password` | Redeem a one-time token and set a new password |
| POST | `/upload` (multipart `file`) | Upload PNG/JPG/GeoTIFF, returns image metadata |
| GET | `/image/{id}` | Raw PNG bytes of a stored image |
| GET | `/image/{id}/meta` | Image metadata (dimensions, geo, quality) |
| GET | `/demo/datasets` | List synthetic demo datasets |
| POST | `/demo/load/{name}` | Ingest a demo dataset's image(s), returns their ids |
| POST | `/query` `{query, image_id, image_b_id?, session_id?}` | Natural-language question → grounded `AnalysisRecord` |
| POST | `/analyze` `{analysis_type, image_id, image_b_id?, target?}` | Explicit analysis (routes to one of below) |
| POST | `/analyze/detect` | Explicit object detection |
| POST | `/analyze/segment` `{target: water\|vegetation\|built_up\|roads\|bare_soil}` | Explicit segmentation |
| POST | `/analyze/change` | Explicit change detection (needs `image_b_id`) |
| GET | `/analysis/{id}` | Fetch a stored `AnalysisRecord` |
| GET | `/analysis/{id}/geojson` | Evidence items as a GeoJSON FeatureCollection |
| GET | `/report/{id}` | Downloadable self-contained HTML report |
| GET | `/history?limit=` | Recent analyses (dashboard) |
| GET | `/stats` | Dashboard counters |
| GET | `/models` | Model registry + live latency/error metrics |

Passwords require at least 8 characters, uppercase and lowercase letters, a number, and a special
character. Password reset links expire after `AUTH_RESET_TOKEN_MINUTES` and are invalidated after use.
Configure SMTP in `.env` to deliver them. Session cookies are HttpOnly, SameSite=Lax, and should be
Secure behind HTTPS (`AUTH_COOKIE_SECURE=true`).

## `AnalysisRecord` shape (abridged)

```json
{
  "id": "a1b2c3d4e5f6",
  "query": "How many buildings are visible?",
  "intent": {"intent": "object_detection", "required_images": 1, "analysis_type": "object_detection"},
  "answer": "12 buildings were detected with an average model confidence of 91%.",
  "confidence": 0.91,
  "confidence_tier": "high",
  "status": "high",
  "evidence": {"analysis_type": "object_detection", "count": 12, "items": [{"id": "det-1", "label": "building", "confidence": 0.97, "bbox": [x1,y1,x2,y2], "geo_bbox": [[lon,lat],[lon,lat]]}], "class_counts": {"building": 12}},
  "visualization": {"boxes": [...], "masks": [], "change_regions": []},
  "pipeline": [{"stage": "Query / intent parsing", "detail": "...", "ms": 0.4}, ...],
  "engine_label": "Prototype inference · classical CV heuristics (not a trained model)",
  "is_demo": true,
  "disclaimer": "Preliminary AI analysis — expert verification required.",
  "warnings": []
}
```

Full field definitions: `backend/app/schemas/api.py`.
