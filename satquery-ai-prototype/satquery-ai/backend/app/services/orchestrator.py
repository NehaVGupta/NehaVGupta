"""Agentic analysis pipeline.

USER QUERY -> intent parser -> modality detection -> model selection -> specialist model(s)
-> evidence extraction -> validation -> response generation -> visualization
Each stage is recorded in a trace that the UI shows under "How did SatQuery AI reach this answer?".
"""
import copy
import time
import uuid
from datetime import datetime, timezone

from app.engines.features import CLASSES
from app.utils.confidence import INSUFFICIENT, PRELIMINARY, pct, tier

from . import evidence_service as evs
from . import response_service as rsp
from .query_router import Intent

GUIDE = ("I can answer questions that map to a supported analysis: object detection (\"How many buildings?\"), "
         "land-cover segmentation (\"Show me the water bodies\"), change detection (\"What changed?\", needs two images) "
         "and scene summaries (\"Explain this image\").")
SUGGEST = {
    "object_detection": ["Which detected regions have low confidence?", "What evidence supports this answer?"],
    "segmentation": ["What evidence supports this answer?", "Where are the roads?"],
    "change_detection": ["How many buildings changed?", "Which ones are new?"],
    "building_change": ["Which ones are new?", "Show them.", "What evidence supports this answer?"],
    "followup_new_items": ["Show them.", "What evidence supports this answer?"],
    "flood_assessment": ["What evidence supports this answer?"],
}


class Trace:
    def __init__(self):
        self.steps, self.exec_ms = [], 0.0

    def add(self, stage, detail, ms):
        self.steps.append({"stage": stage, "detail": detail, "ms": round(ms, 1)})


def _iou(a, b):
    ix, iy = max(0, min(a[2], b[2]) - max(a[0], b[0])), max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / u if u else 0.0


class Orchestrator:
    def __init__(self, images, repo, cache, registry, router, det, seg, chg):
        self.images, self.repo, self.cache, self.reg, self.router = images, repo, cache, registry, router
        self.det, self.seg, self.chg = det, seg, chg

    # ---- helpers ----------------------------------------------------------------------------
    def _run(self, tr, fn, *a):
        t = time.perf_counter()
        try:
            return fn(*a)
        finally:
            tr.exec_ms += (time.perf_counter() - t) * 1000

    def _plan(self, i):
        m = {"object_detection": ["object_detection"], "segmentation": ["segmentation"], "change_detection": ["change_detection"],
             "flood_assessment": ["change_detection"], "image_understanding": ["segmentation", "object_detection", "vision_language"]}
        if i.intent == "change_detection" and i.entities.get("target") == "building":
            return ["change_detection", "object_detection"]
        if i.intent == "flood_assessment":
            return ["change_detection"]
        return m.get(i.intent, [])

    def _root(self, prev):
        rid = prev.get("root_id")
        if rid and rid != prev["id"]:
            try:
                return self.repo.get("analysis", rid)
            except Exception:  # noqa: BLE001
                pass
        return prev

    def _prev(self, ctx):
        if ctx and ctx.get("last_analysis_id"):
            try:
                return self.repo.get("analysis", ctx["last_analysis_id"])
            except Exception:  # noqa: BLE001
                return None
        return None

    # ---- public -----------------------------------------------------------------------------
    def handle(self, query, image_id, image_b_id=None, session_id=None, forced: Intent | None = None):
        tr, t0 = Trace(), time.perf_counter()
        A = self.images.meta(image_id)
        B = self.images.meta(image_b_id) if image_b_id else None
        ctx = self.cache.get(f"session:{session_id}") if session_id else None
        prev = self._prev(ctx)

        t = time.perf_counter()
        intent = forced or self.router.route(query, B is not None, prev is not None)
        tr.add("Query / intent parsing", f"intent = {intent.intent}; analysis = {intent.analysis_type or '—'}; entities = {intent.entities or '{}'}", (time.perf_counter() - t) * 1000)
        tr.add("Required modality detection", f"needs {intent.required_images} image(s); {1 + (B is not None)} provided", 0.1)

        if intent.intent == "unknown":
            return self._finish(tr, query, intent, A, B, session_id, self._empty("none"), {}, answer=f"I couldn't map that question to a supported analysis. {GUIDE}",
                                status="unsupported", conf=None, val=None)
        if intent.required_images == 2 and B is None:
            return self._finish(tr, query, intent, A, B, session_id, self._empty("change_detection"), {},
                                answer="Change detection needs two images. Upload a second image (Image B) or load the before/after demo dataset, then ask again.",
                                status="needs_input", conf=None, val=None)
        plan = self._plan(intent)
        names = [self.reg.get(k).name for k in plan]
        tr.add("Agentic model selection", " → ".join(names) if names else "conversation context (no model call)", 0.2)

        t = time.perf_counter()
        root = None
        if intent.followup:
            if prev is None:
                return self._finish(tr, query, intent, A, B, session_id, self._empty("none"), {}, answer=f"There is no earlier analysis to refer to. {INSUFFICIENT}",
                                    status="insufficient", conf=0.0, val=None)
            root = self._root(prev)
            ev, viz, answer = self._followup(intent, prev, root)
            val = {"status": tier(ev.get("confidence")), "confidence": ev.get("confidence") or 0.0, "reasons": [f"Derived from analysis {prev['id']}; no new model call."]}
        else:
            ev, viz = getattr(self, "_h_" + intent.intent)(tr, intent, A, B, query)
            answer, val = None, None
        total = (time.perf_counter() - t) * 1000
        tr.add("Specialist model execution", ", ".join(names) or "—", tr.exec_ms)
        tr.add("Evidence extraction", f"{ev.get('count', 0)} evidence item(s) with coordinates ({ev['coordinates']['mode']})" if ev.get("coordinates") else "no spatial evidence", max(total - tr.exec_ms, 0.1))
        return self._finish(tr, query, intent, A, B, session_id, ev, viz, answer=answer, status=None, conf=None, val=val, root_id=root["id"] if root else None)

    # ---- specialist handlers ------------------------------------------------------------------
    def _empty(self, kind):
        return {"analysis_type": kind, "engine": {"name": "—", "label": "No model executed", "is_demo": False}, "items": [], "count": 0, "confidence": None,
                "coordinates": None, "warnings": [], "stats": {}}

    def _viz_masks(self, seg):
        return [{"label": seg["class"], "mask_png": seg["mask_png"], "color": seg["color"]}]

    def _h_object_detection(self, tr, i, A, B, q):
        raw = self._run(tr, self.det.analyze, A["id"])
        model = self.reg.get("object_detection")
        classes = i.entities.get("classes") or []
        un = [c for c in classes if c not in model.supported_classes]
        sel = [o for o in raw["objects"] if not classes or o["class"] in classes]
        size = False
        if i.entities.get("size") == "large" and sel:
            thr = sorted(o["area_px"] for o in sel)[int(len(sel) * 0.75)]
            sel, size = [o for o in sel if o["area_px"] >= thr], True
        ev = evs.from_detection(model, A, sel, classes, un if len(un) == len(classes) else [])
        ev["size_filter"] = size
        if un and len(un) != len(classes):
            ev["warnings"].append(f"Not supported by the active engine and skipped: {', '.join(un)}.")
        viz = {"boxes": [{"id": o["id"], "label": o["class"], "confidence": o["confidence"], "bbox": o["bbox"]} for o in sel], "view": "A"}
        return ev, viz

    def _h_segmentation(self, tr, i, A, B, q, flood=False):
        cls = i.entities.get("class", "vegetation")
        seg = self._run(tr, self.seg.analyze, A["id"], cls)
        ev = evs.from_segmentation(self.reg.get("segmentation"), A, seg, A["geo"].get("gsd_m"))
        ev["flood_wording"] = flood
        viz = {"masks": self._viz_masks(seg), "polygons": [{"id": x["id"], "points": x["polygon"], "label": x["label"]} for x in ev["items"]], "view": "A"}
        return ev, viz

    def _chg_viz(self, chg, regions, view="change"):
        return {"change_mask_png": chg["mask_png"], "change_regions": [{"id": r["id"], "bbox": r["bbox"], "label": r["label"], "confidence": r["confidence"], "significant": r["significant"]} for r in regions], "view": view}

    def _h_change_detection(self, tr, i, A, B, q):
        tgt, d, ent = i.entities.get("target"), i.entities.get("direction"), i.entities
        if tgt == "building":
            return self._building_change(tr, A, B)
        chg = self._run(tr, self.chg.analyze, A["id"], B["id"])
        regs, target = chg["regions"], None
        want = {"vegetation": "vegetation_gain" if d == "increase" else "vegetation_loss", "water": "water_decrease" if d == "decrease" else "water_increase"}.get(tgt)
        if want:
            regs, target = [r for r in regs if r["type"] == want and r["significant"]], want
        elif ent.get("only_significant"):
            regs = [r for r in regs if r["significant"]]
        ev = evs.from_change(self.reg.get("change_detection"), A, chg, regs, A["geo"].get("gsd_m"), target=target)
        ev["only_significant"] = bool(ent.get("only_significant")) and not want
        return ev, self._chg_viz(chg, ev["items"])

    def _building_change(self, tr, A, B):
        dA = self._run(tr, self.det.analyze, A["id"])["objects"]
        dB = self._run(tr, self.det.analyze, B["id"])["objects"]
        chg = self._run(tr, self.chg.analyze, A["id"], B["id"])
        bA, bB = [o for o in dA if o["class"] == "building"], [o for o in dB if o["class"] == "building"]
        new = [o for o in bB if max((_iou(o["bbox"], x["bbox"]) for x in bA), default=0) < 0.2]
        removed = [o for o in bA if max((_iou(o["bbox"], x["bbox"]) for x in bB), default=0) < 0.2]
        regs = [r for r in chg["regions"] if r["type"] == "new_construction" and r["significant"]]
        out = []
        for o in new:
            hit = next((r for r in regs if _iou(o["bbox"], r["bbox"]) > 0.3), None)
            out.append({**o, "corroborated": bool(hit), "corroborated_by": hit["id"] if hit else None, "confidence": round(o["confidence"] * (1 if hit else 0.8), 3)})
        conf = round(sum(o["confidence"] for o in out) / len(out), 3) if out else (0.0 if not bB else 0.9)
        ev = evs.from_building_change(self.reg.get("object_detection"), A, out, removed, len(bA), len(bB), conf)
        viz = {"boxes": [{"id": x["id"], "label": "new building", "confidence": x["confidence"], "bbox": x["bbox"]} for x in ev["items"]],
               "change_mask_png": chg["mask_png"], "change_regions": [], "view": "B"}
        return ev, viz

    def _h_flood_assessment(self, tr, i, A, B, q):
        if B is None:
            return self._h_segmentation(tr, Intent("segmentation", 1, "", {"class": "water"}), A, B, q, flood=True)
        chg = self._run(tr, self.chg.analyze, A["id"], B["id"])
        regs = [r for r in chg["regions"] if r["type"] == "water_increase" and r["significant"]]
        ev = evs.from_change(self.reg.get("change_detection"), A, chg, regs, A["geo"].get("gsd_m"), target="water_increase")
        ev["flood"] = True
        return ev, self._chg_viz(chg, ev["items"], "B")

    def _h_image_understanding(self, tr, i, A, B, q):
        segs = {c: self._run(tr, self.seg.analyze, A["id"], c) for c in CLASSES}
        objs = self._run(tr, self.det.analyze, A["id"])["objects"]
        cov = {c: s["area_pct"] for c, s in segs.items()}
        counts = {}
        for o in objs:
            counts[o["class"]] = counts.get(o["class"], 0) + 1
        caption = self._run(tr, lambda: self.reg.run("vision_language", {"coverage": cov, "counts": counts}))
        used = [s["confidence"] for c, s in segs.items() if cov[c] >= 1] + [o["confidence"] for o in objs]
        conf = round(sum(used) / len(used), 3) if used else 0.0
        ev = {"analysis_type": "image_understanding", "engine": {"name": "Segmentation + detection + template captioner", "label": self.reg.get("vision_language").label, "is_demo": True},
              "items": [], "count": 0, "confidence": conf, "coordinates": {"mode": "pixel", "available": True}, "warnings": [],
              "stats": {"coverage_pct": cov, "object_counts": counts}, "caption": caption}
        viz = {"masks": [{"label": c, "mask_png": s["mask_png"], "color": s["color"]} for c, s in segs.items() if cov[c] >= 1], "view": "A"}
        return ev, viz

    # ---- follow-ups -----------------------------------------------------------------------------
    def _followup(self, i, prev, root):
        ev, viz = copy.deepcopy(prev["evidence"]), copy.deepcopy(prev["visualization"])
        items, kind = ev.get("items", []), ev.get("analysis_type")
        if i.followup == "show_focus":
            ids = ev.get("focus_ids") or [x["id"] for x in items]
            viz["highlight_ids"] = ids
            ev["focus_ids"] = ids
            return ev, viz, f"Highlighting {len(ids)} region(s) from the previous analysis on the map." if ids else f"The previous analysis has no spatial regions to show. {INSUFFICIENT}"
        if i.followup == "new_items":
            sel = items if kind == "building_change" else [x for x in items if x.get("label") == "new_construction" and x.get("significant")] if kind == "change_detection" else []
            if not sel:
                ev.update(items=[], count=0, confidence=0.0, focus_ids=[])
                return ev, viz, f"No temporal comparison with new structures is available in the current context. Ask what changed between two images first. {INSUFFICIENT}"
            ev.update(items=sel, count=len(sel), focus_ids=[x["id"] for x in sel], confidence=round(sum(x["confidence"] for x in sel) / len(sel), 3))
            viz["highlight_ids"] = ev["focus_ids"]
            n = len(sel)
            txt = (f"{n} detected building region(s) appear only in the later image." if kind == "building_change"
                   else f"{n} significant region(s) show new construction, i.e. structures present only in the later image.")
            return ev, viz, f"{txt} Model confidence: {pct(ev['confidence'])}."
        if i.followup == "low_confidence":
            if not items:
                return ev, viz, f"The previous analysis has no individual regions to rank. {INSUFFICIENT}"
            low = sorted([x for x in items if x["confidence"] < 0.8], key=lambda x: x["confidence"]) or sorted(items, key=lambda x: x["confidence"])[:3]
            top = sorted(items, key=lambda x: x["confidence"])[:3]
            below = [x for x in items if x["confidence"] < 0.8]
            ev.update(focus_ids=[x["id"] for x in low], confidence=round(sum(x["confidence"] for x in low) / len(low), 3))
            viz["highlight_ids"] = ev["focus_ids"]
            if below:
                listing = ", ".join(f"{x['id']} ({pct(x['confidence'])})" for x in below[:6])
                return ev, viz, f"{len(below)} of {len(items)} regions fall below the 80% high-confidence threshold: {listing}. Manual review recommended."
            listing = ", ".join(f"{x['id']} ({pct(x['confidence'])})" for x in top)
            return ev, viz, f"No region falls below the 80% high-confidence threshold. The lowest are {listing}."
        # explain: always describe the ROOT analysis (the one that ran models), not a chain of follow-ups
        rev, e = root["evidence"], root["evidence"].get("engine", {})
        txt = (f"The answer to “{root['query']}” was produced by intent “{root['intent']['intent']}” using {e.get('name', 'no model')} ({e.get('label', '')}). "
               f"It rests on {rev.get('count', 0)} measured evidence item(s) with an average model confidence of {pct(rev.get('confidence'))}.")
        ch = [x for x in rev.get("items", []) if x.get("kind") == "change_region"]
        if ch:
            x = max(ch, key=lambda r: r["area_px"])
            txt += (f" Example — region {x['id']}: the dominant surface changed from {x['from_class'].replace('_', ' ')} to {x['to_class'].replace('_', ' ')}, "
                    f"mean colour difference {x['mean_diff']} (Lab units), area {x['area_px']} px, classified as {x['label'].replace('_', ' ')}.")
        if rev.get("analysis_type") == "building_change":
            n = len(rev["items"])
            ok = sum(1 for x in rev["items"] if x.get("corroborated"))
            txt += (f" Buildings were detected independently in both images; a building counts as new only if it overlaps no earlier building (IoU < 0.2). "
                    f"Each was then cross-checked against significant new-construction change regions — {ok} of {n} corroborated (uncorroborated ones are down-weighted).")
        txt += " This is heuristic prototype analysis; expert verification is required."
        viz["highlight_ids"] = viz.get("highlight_ids", [])
        ev["explained_root"] = root["id"]
        return ev, viz, txt

    # ---- validation, response, persistence ---------------------------------------------------------
    def _finish(self, tr, query, intent, A, B, session_id, ev, viz, answer, status, conf, val, root_id=None):
        t = time.perf_counter()
        quality = min(A["quality"]["score"], B["quality"]["score"] if B else 1.0)
        synthetic = A["synthetic"] and (B["synthetic"] if B else True)
        if val is None and status is None:
            val = evs.validate(ev, quality, synthetic)
        tr.add("Validation & confidence", (f"status = {val['status']}; confidence = {pct(val['confidence'])}; " + " ".join(val["reasons"])).strip() if val else "no evidence to validate", (time.perf_counter() - t) * 1000)
        t = time.perf_counter()
        if answer is None:
            k = ev["analysis_type"]
            if k == "object_detection": answer = rsp.detection(ev, val)
            elif k == "segmentation": answer = rsp.segmentation(ev, val, ev.get("flood_wording", False))
            elif k == "building_change": answer = rsp.building_change(ev, val)
            elif k == "change_detection": answer = rsp.flood(ev, val) if ev.get("flood") else rsp.change(ev, val, self._tgt(intent))
            elif k == "image_understanding": answer = rsp.scene(ev, val, ev["caption"])
        if val and val["status"] == "insufficient" and INSUFFICIENT not in answer:
            answer += f" {INSUFFICIENT}"
        tr.add("Grounded response generation", "template composed from structured evidence only (no free-form generation)", (time.perf_counter() - t) * 1000)
        viz = {"boxes": [], "polygons": [], "masks": [], "change_regions": [], "change_mask_png": None, "highlight_ids": [], "view": "A", **viz}
        tr.add("Visualization", f"{len(viz['boxes'])} box(es), {len(viz['polygons'])} polygon(s), {len(viz['masks'])} mask(s), {len(viz['change_regions'])} change region(s)", 0.1)
        conf_final = val["confidence"] if val else conf
        st = status or (val["status"] if val else "insufficient")
        warnings = list(dict.fromkeys(ev.get("warnings", []) + A["quality"]["warnings"] + (B["quality"]["warnings"] if B else [])))
        if not synthetic:
            warnings.append("Prototype heuristics have not been validated on real imagery.")
        rec = {"id": uuid.uuid4().hex[:12], "created": datetime.now(timezone.utc).isoformat(), "query": query, "intent": intent.dict(), "answer": answer,
               "confidence": conf_final, "confidence_tier": tier(conf_final) if conf_final is not None else "insufficient", "status": st, "evidence": ev,
               "visualization": viz, "pipeline": tr.steps, "image_ids": {"a": A["id"], "b": B["id"] if B else None},
               "engine_label": ev["engine"]["label"], "is_demo": bool(ev["engine"].get("is_demo", True)), "disclaimer": PRELIMINARY,
               "warnings": warnings, "root_id": None, "suggestions": SUGGEST.get(intent.intent if intent.intent.startswith("followup") else ev["analysis_type"] if ev["analysis_type"] in SUGGEST else intent.intent, []),
               "validation": val}
        rec.pop("validation")
        rec["root_id"] = root_id or rec["id"]
        self.repo.put("analysis", rec["id"], rec)
        detected = ev["count"] if ev["analysis_type"] in ("object_detection", "building_change") and not intent.followup else 0
        changed = ev["stats"].get("significant_regions", 0) if ev["analysis_type"] == "change_detection" and not intent.followup else 0
        self.repo.put("analysis_index", rec["id"], {"id": rec["id"], "created": rec["created"], "query": query, "intent": intent.intent, "answer": answer, "confidence": conf_final,
                                                    "status": st, "image_ids": rec["image_ids"], "objects_detected": detected, "changes_detected": changed, "is_demo": rec["is_demo"]})
        if session_id:
            self.cache.set(f"session:{session_id}", {"last_analysis_id": rec["id"]})
        return rec

    @staticmethod
    def _tgt(intent):
        e = intent.entities
        if e.get("target") == "vegetation":
            return "vegetation_gain" if e.get("direction") == "increase" else "vegetation_loss"
        if e.get("target") == "water":
            return "water_decrease" if e.get("direction") == "decrease" else "water_increase"
        return None
