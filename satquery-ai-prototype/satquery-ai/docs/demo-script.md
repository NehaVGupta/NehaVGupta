# SatQuery AI — 4-minute judge demo script

Prerequisites: backend running on `:8000`, frontend on `:5173` (or the combined Docker Compose stack).
Open the app, sign in to the prototype gate, and choose **Demo** in the workspace navigation, or go
straight to `/demo`.

## 1. Object detection & explainability (60s)

1. The Demo workspace auto-loads the **Urban block** dataset.
2. Ask: **"How many buildings are visible?"** → 12 buildings, boxes drawn, confidence badge.
3. Ask: **"Which detected regions have low confidence?"** → follow-up using conversation context, no
   new model call — point out the pipeline trace ("How did SatQuery AI reach this answer?").

## 2. Segmentation (45s)

4. Ask: **"What percentage of the image is vegetation?"** → mask overlay + area in %, and km² if
   georeferenced.
5. Ask: **"Show me the water bodies."** → switch to Segmentation tab to see the mask.

## 3. Change detection (90s)

6. In the left panel, load the **Urban growth (before/after)** dataset.
7. Ask: **"What changed between these two images?"** → Change tab shows Before / After / Change map
   (red = significant, amber = minor), with a spoken count.
8. Ask: **"How many buildings changed?"** → cross-checked answer (object detector run on both images,
   corroborated against change regions).
9. Ask: **"Which ones are new?"** then **"Show them."** → follow-ups, highlighted on the map.

## 4. Grounding & honesty (45s)

10. Switch back to the Urban dataset. Ask: **"Are there any aircraft?"** → the detector doesn't support
    the class, so the answer is explicitly **"Insufficient visual evidence for a reliable conclusion."**
    — call this out as a deliberate product feature, not a bug.
11. Open the Evidence tab / "How did SatQuery AI reach this answer?" on any earlier answer to show the
    full pipeline trace and the evidence table with coordinates.

## 5. Wrap-up (30s)

12. Visit **Architecture** — show the pipeline diagram and the explicit "what is real vs. demo" lists.
13. Visit **Model monitoring** — show live call counts/latency for the active session, and the list of
    planned real-model adapters (YOLO, SegFormer, Siamese U-Net, GeoChat-style VLM).
14. Optional: download a report (`Download report` button) or the GeoJSON for an answer with spatial
    evidence.

Everything above is scripted in the in-app **judge demo script** panel (left sidebar of the Analysis
workspace) — each step is a clickable button that loads the right dataset and asks the right question.
