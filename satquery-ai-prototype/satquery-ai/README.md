# SatQuery AI

**An evidence-grounded, natural-language assistant for satellite/remote-sensing imagery.**
Smart India Hackathon 2026 · Problem Statement **SIH26167** · Theme: Space Technology · Team **Cipher**

> Ask "How many buildings are visible?" or "What changed between these two images?" and get an answer
> that is composed only from measured evidence — segmentation masks, bounding boxes, coordinates, change
> regions and confidence scores. If the evidence is weak, SatQuery AI says so explicitly:
> *"Insufficient visual evidence for a reliable conclusion."* — that's a feature, not a bug.

---

## Contents

- [Problem & solution](#problem--solution)
- [Features](#features)
- [Architecture](#architecture)
- [Tech stack](#tech-stack)
- [Quick start](#quick-start)
- [Docker](#docker)
- [Demo walkthrough](#demo-walkthrough)
- [API](#api)
- [What is real vs. prototype](#what-is-real-vs-prototype)
- [Testing](#testing)
- [Limitations](#limitations)
- [Team](#team)

## Problem & solution

Government departments, disaster managers, urban planners, farmers and researchers all need to ask
plain questions of satellite imagery, but existing tools require GIS expertise and produce results with
no visible evidence trail. SatQuery AI routes a natural-language question to the right specialist
computer-vision analysis (object detection, land-cover segmentation, or before/after change detection),
then generates an answer **only** from that analysis's structured output — with the supporting masks,
boxes, coordinates and confidence always shown alongside the text.

## Features

- **Conversational workspace** — upload one or two images (or load a synthetic demo dataset), ask
  follow-up questions, see the answer reasoning trace.
- **Object detection** — buildings, vehicles, ships, agricultural structures; bounding boxes + confidence.
- **Land-cover segmentation** — water, vegetation, built-up, roads, bare soil; pixel masks + area (km²
  when georeferenced).
- **Change detection** — co-registered before/after comparison, significance thresholding, change typing
  (new construction, vegetation loss/gain, water increase/decrease…), building-level cross-checking.
- **Evidence panel** — answer, confidence badge, evidence count, model used, and an expandable
  step-by-step "How did SatQuery AI reach this answer?" trace.
- **Grounding rule** — every analysis is validated (image quality, evidence count, class support) before
  a confidence is assigned; low confidence always yields the fixed insufficient-evidence sentence.
- **Judge Demo Mode** — a scripted, clickable 4-minute walkthrough of every capability.
- **GeoTIFF support** — real CRS/bounds/transform/band extraction via Rasterio, graceful pixel-coordinate
  fallback for plain images.
- **Downloadable report & GeoJSON export** for any answer with spatial evidence.
- **Dashboard** of recent analyses, and a **Model monitoring** page showing live call counts/latency for
  active engines plus the roadmap of planned real-model adapters.

## Architecture

```
User → SatQuery AI UI (React/Leaflet) → FastAPI
     → Query Understanding → Agentic Model Router
     → Specialist Models (object detection · segmentation · change detection · image understanding)
     → Evidence Aggregation → Validation/Confidence → Grounded Response → Visual Evidence + Map
```

Full detail, including exactly what is a trained model vs. classical-CV prototype inference, is in
[`docs/architecture.md`](docs/architecture.md).

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React, Tailwind CSS, Leaflet |
| Backend | Python, FastAPI |
| Image processing | OpenCV, Rasterio/GDAL, Pillow, NumPy |
| AI (planned real models) | PyTorch, Hugging Face Transformers — YOLO/Faster R-CNN, U-Net/SegFormer, Siamese U-Net |
| Database (production-ready schema) | PostgreSQL + PostGIS |
| Storage / cache | MinIO/S3-compatible (adapter), Redis (with in-memory fallback) |
| File formats | GeoTIFF, GeoJSON, PNG, JSON |
| Deployment | Docker, Nginx |

## Quick start

Requires Python 3.11+ and Node 18+.

```bash
# 1. Backend
cd backend
pip install -r requirements.txt
cp ../.env.example ../.env    # optional — sane defaults work without it
python -m uvicorn app.main:app --reload --port 8000

# 2. Frontend (new terminal)
cd frontend
npm install
npm run dev     # http://localhost:5173, proxies /api to :8000
```

Open `http://localhost:5173`, click **Demo Mode**, and follow [`docs/demo-script.md`](docs/demo-script.md).

The synthetic demo dataset is generated on first use (or run
`python -m app.services.demo_data` inside `backend/` to pre-generate it).

### Environment variables

See [`.env.example`](.env.example) — every variable has a working default; nothing must be set to run
the prototype locally.

## Docker

```bash
docker compose up --build
# frontend → http://localhost:5173   backend → http://localhost:8000
```

`docker-compose.yml` also defines an optional `full` profile (PostgreSQL/PostGIS, MinIO) for the
production-ready path — not required to run or judge the prototype:

```bash
docker compose --profile full up --build
```

## Demo walkthrough

See [`docs/demo-script.md`](docs/demo-script.md) for the scripted ~4-minute flow, which is also available
as clickable steps inside the app (Analysis workspace → "Show judge demo script").

## API

See [`docs/api.md`](docs/api.md) for the full endpoint reference and response shapes.

## What is real vs. prototype

**Real, working end-to-end:** file upload/validation/quality checks, GeoTIFF metadata extraction, the
natural-language intent router, the agentic orchestration pipeline, all three specialist analyses running
real computer-vision code (OpenCV) against real pixels, the evidence/validation/grounding logic, follow-up
conversation handling, GeoJSON/report export, and the full React/Leaflet UI.

**Prototype / demo inference, clearly labelled in the UI as such:** the object detector, segmenter and
change detector use classical computer-vision heuristics (HSV/Lab colour space, connected components,
phase correlation), not trained deep-learning models — so the prototype runs on any laptop with no GPU.
Real-model adapters (YOLO, SegFormer, Siamese U-Net, a GeoChat-style vision-language model) are scaffolded
in `backend/app/engines/adapters.py` behind the exact same interfaces, ready to be implemented. Demo
dataset imagery is synthetically generated, not real satellite imagery, and is labelled as such everywhere
it appears.

Full breakdown: [`docs/architecture.md`](docs/architecture.md#what-is-real-in-this-prototype).

## Testing

```bash
# Backend (21 tests: routing, validation, all three analyses, follow-ups, errors, security)
cd backend && pip install -r requirements.txt pytest httpx && cd .. && pytest tests -q

# Frontend (unit tests for confidence tiers and coordinate math)
cd frontend && npm test
```

## Limitations

- Demo engines are unvalidated heuristics, not benchmarked trained models — confidence scores are
  informative but not calibrated probabilities.
- No authentication layer (out of scope for the hackathon prototype).
- PostgreSQL/PostGIS, Redis and MinIO are optional; the prototype defaults to local JSON storage and an
  in-memory cache so it runs with zero external services.
- Synthetic demo imagery is illustrative only, and never presented as real satellite data.

## Team

**Team Cipher** — Smart India Hackathon 2026, Problem Statement SIH26167 (SatQuery AI, Space Technology,
Software).
