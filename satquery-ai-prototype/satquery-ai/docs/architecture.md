# SatQuery AI — Architecture

## Pipeline

```
USER QUERY
  → Query / Intent Parser        (app/services/query_router.py)
  → Required Modality Detection  (1 image vs 2, follow-up vs new)
  → Agentic Model Selection      (app/services/orchestrator.py::_plan)
  → Specialist Model Execution   (app/engines/*)
  → Evidence Extraction          (app/services/evidence_service.py)
  → Validation / Confidence      (app/utils/confidence.py, evidence_service.validate)
  → Grounded Response Generation (app/services/response_service.py)
  → Visualization                (boxes / masks / change regions returned to the frontend)
```

Every stage is timed and recorded in a `pipeline` trace attached to the analysis record, shown in the
UI under **"How did SatQuery AI reach this answer?"**.

## Specialist models

| Capability | Interface | Demo implementation | Real-model adapter (planned) |
|---|---|---|---|
| Object detection | `ObjectDetectionModel` | `DemoObjectDetectionModel` — HSV/shape heuristics over connected components | `YOLOObjectDetectionModel` |
| Segmentation | `SegmentationModel` | `DemoSegmentationModel` — HSV/ExG class masks | `SegFormerSegmentationModel` |
| Change detection | `ChangeDetectionModel` | `DemoChangeDetectionModel` — phase-correlation co-registration + Lab-space differencing | `SiameseUNetChangeDetectionModel` |
| Scene understanding | `VisionLanguageModel` | `DemoSceneCaptioner` — template over measured coverage/counts | `HFVisionLanguageModel` (GeoChat-style) |
| Multi-sensor fusion | `ChangeDetectionModel` | not implemented | `OpticalSARFusionModel` |

All interfaces live in `backend/app/engines/base.py`. The `ModelRegistry`
(`backend/app/engines/registry.py`) selects demo vs. real per capability from environment variables
(`SATQUERY_DETECTOR`, `SATQUERY_SEGMENTER`, `SATQUERY_CHANGE_DETECTOR`) and records real call-count /
latency / error metrics shown on the **Model monitoring** page.

## Why classical CV, not "fake AI"

The brief requires a prototype that runs on a laptop with no GPU. Rather than hard-coding results, the
demo engines compute real outputs from real pixels using OpenCV: HSV/ExG-based land-cover
classification, connected-component blob detection with rectangularity/contrast scoring, phase-correlation
image registration, and Lab-colour-space differencing for change detection. This means:

- The same building really is detected in the same place every time you ask.
- Confidence scores vary with real image properties (contrast, shape regularity, mask consistency) —
  they are not literal random numbers, though they are **not calibrated probabilities** either.
- The orchestrator and evidence pipeline depend only on the abstract interfaces in `base.py`, so a
  trained model can be integrated without changing those layers. The adapter classes are currently
  stubs: inference, weights loading and registry selection still need to be implemented.

The UI always labels this engine as **"Prototype inference · classical CV heuristics (not a trained
model)"** — see `app/engines/demo.py::LABEL` — and the Architecture page lists exactly what is real vs.
demo.

## Grounding & the "insufficient evidence" rule

`response_service.py` never free-form generates text. Each analysis type has a template function that
consumes only the structured `Evidence` object produced by `evidence_service.py`. `evidence_service.validate`
implements the "no evidence → no strong claim" rule:

- Unsupported classes → confidence forced to 0, answer explains the limitation.
- Image quality < 0.4 → confidence capped at 0.5.
- Non-synthetic (i.e. user-uploaded) imagery → confidence discounted, because the prototype heuristics
  are only tuned against the synthetic demo dataset.
- Zero detections/segments → confidence capped at 0.3.
- Confidence < 0.60 → the fixed phrase **"Insufficient visual evidence for a reliable conclusion."** is
  appended, and the UI flags it in the confidence badge, not hidden as an error.

## Conversational follow-ups

`Orchestrator._followup` handles context-dependent questions ("Which ones are new?", "Show them.",
"Which detected regions have low confidence?", "What evidence supports this answer?") by re-deriving a new
view over the **previous analysis's evidence** — no new model call — and always traces "explain" back to
the original (root) analysis that actually ran a model, even through a chain of follow-ups.

## Data model (production-ready)

`backend/app/models/db.py` defines the target PostgreSQL/PostGIS schema (User, Dataset, Image, Analysis,
Query, Detection, Segmentation, ChangeRegion, Evidence) using SQLAlchemy + GeoAlchemy2. **It is not used at
runtime by the prototype** — persistence today is JSON documents via `Repository` over `StorageService`
(`backend/app/services/repository.py`, `storage_service.py`), which keeps the demo dependency-free.
Swapping `Repository` for a SQLAlchemy-backed implementation against this schema is the production
migration path; both share the same evidence/analysis JSON shape.

## Storage, cache

- `StorageService` (`storage_service.py`): `LocalStorageService` is default; `S3StorageService` is a
  documented placeholder for MinIO/AWS S3 (`requirements-ml.txt` → `boto3`).
- Cache: Redis if `REDIS_URL` is set and reachable, otherwise an in-memory dict — never fatal
  (`cache_service.py::make_cache`).

## Integrating a real model

1. `pip install -r backend/requirements-ml.txt` and obtain/download weights yourself (never done
   automatically).
2. Implement `predict`/`describe` in the relevant class in `backend/app/engines/adapters.py`.
3. Set the matching env var, e.g. `SATQUERY_DETECTOR=yolo`, and extend `ModelRegistry._pick` if you add a
   new name.
4. Nothing else changes — `Orchestrator`, `evidence_service` and `response_service` are model-agnostic.

## Known limitations

- Demo engines are classical CV, not trained deep networks; they work well on the bundled synthetic
  imagery and reasonably on clean real imagery, but are not validated against benchmark datasets.
- No authentication/authorization layer (out of scope for a hackathon prototype; `models/db.py` includes
  a `User`/`role` model as the extension point).
- SQLite/Postgres, Redis and MinIO are not required to run the prototype and are optional profiles in
  `docker-compose.yml`.
