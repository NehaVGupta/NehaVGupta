"""Turns raw engine outputs into a standard, structured Evidence object, and validates it."""
from app.utils.confidence import HIGH, MODERATE, tier
from app.utils.geo import bbox_to_geo


def _engine(model):
    return {"name": model.name, "label": model.label, "is_demo": model.is_demo}


def _coord_mode(geo):
    return "geographic (illustrative)" if geo and geo.get("illustrative") else "geographic" if geo and geo.get("georeferenced") else "pixel"


def _base(kind, model, img, items, conf, warnings=None, **extra):
    return {"analysis_type": kind, "engine": _engine(model), "items": items, "count": len(items), "confidence": conf,
            "coordinates": {"mode": _coord_mode(img["geo"]), "available": True}, "warnings": warnings or [], **extra}


def from_detection(model, img, objs, classes, unsupported):
    items = [{"id": o["id"], "kind": "detection", "label": o["class"], "confidence": o["confidence"], "bbox": o["bbox"], "area_px": o["area_px"],
              "geo_bbox": bbox_to_geo(img["geo"], img["width"], img["height"], o["bbox"])} for o in objs]
    counts = {}
    for o in objs:
        counts[o["class"]] = counts.get(o["class"], 0) + 1
    conf = round(sum(o["confidence"] for o in objs) / len(objs), 3) if objs else 0.0
    return _base("object_detection", model, img, items, conf, class_counts=counts, requested_classes=classes, unsupported_classes=unsupported,
                 stats={"avg_confidence": conf, "min_confidence": min((o["confidence"] for o in objs), default=None)})


def from_segmentation(model, img, seg, gsd):
    items = []
    for k, poly in enumerate(seg["polygons"][:25]):
        xs, ys = [p[0] for p in poly], [p[1] for p in poly]
        bb = [min(xs), min(ys), max(xs), max(ys)]
        items.append({"id": f"seg-{k + 1}", "kind": "segment", "label": seg["class"], "confidence": seg["confidence"], "bbox": bb, "polygon": poly,
                      "geo_bbox": bbox_to_geo(img["geo"], img["width"], img["height"], bb)})
    km2 = round(seg["area_px"] * (gsd ** 2) / 1e6, 4) if gsd else None
    return _base("segmentation", model, img, items, seg["confidence"], seg_class=seg["class"], color=seg["color"],
                 stats={"class": seg["class"], "area_px": seg["area_px"], "area_pct": seg["area_pct"], "area_km2": km2, "gsd_m": gsd, "regions": len(seg["polygons"])})


def from_change(model, img, chg, regions, gsd, total=None, **extra):
    items = [{"id": r["id"], "kind": "change_region", "label": r["type"], "confidence": r["confidence"], "bbox": r["bbox"], "area_px": r["area_px"],
              "significant": r["significant"], "from_class": r["from_class"], "to_class": r["to_class"], "mean_diff": r["mean_diff"],
              "geo_bbox": bbox_to_geo(img["geo"], img["width"], img["height"], r["bbox"])} for r in regions]
    allr = chg["regions"]
    sig = [r for r in allr if r["significant"]]
    types = {}
    for r in sig:
        types[r["type"]] = types.get(r["type"], 0) + 1
    pool = [r["confidence"] for r in (regions or allr)]
    conf = round(sum(pool) / len(pool), 3) if pool else 0.0
    km2 = round(sum(r["area_px"] for r in regions) * (gsd ** 2) / 1e6, 4) if gsd else None
    warns = list(chg["notes"])
    if not chg["registration"]["applied"] and abs(chg["registration"]["dx"]) + abs(chg["registration"]["dy"]) > 0.5:
        warns.append("Small misalignment between images detected; some changes may be false positives.")
    return _base("change_detection", model, img, items, conf, warns,
                 stats={"total_regions": len(allr), "significant_regions": len(sig), "significant_types": types, "shown_regions": len(regions),
                        "changed_pct": chg["changed_pct"], "shown_pct": round(sum(r["area_px"] for r in regions) / (img["width"] * img["height"]) * 100, 2), "affected_km2": km2, "registration": chg["registration"], "diff_threshold": chg["diff_threshold"]}, **extra)


def from_building_change(model, img, new, removed, before_n, after_n, conf):
    items = [{**o, "id": f"new-{k + 1}", "kind": "detection", "label": "new building",
              "geo_bbox": bbox_to_geo(img["geo"], img["width"], img["height"], o["bbox"])} for k, o in enumerate(new)]
    return _base("building_change", model, img, items, conf,
                 stats={"before_count": before_n, "after_count": after_n, "new": len(new), "removed": len(removed), "avg_confidence": conf},
                 cross_check="building detector on both images + change-detection regions")


def validate(ev, quality, synthetic):
    """No evidence -> no strong claim. Returns {status, confidence, reasons}."""
    reasons, conf = [], ev.get("confidence") or 0.0
    if ev.get("unsupported_classes"):
        reasons.append(f"Class not supported by the active engine: {', '.join(ev['unsupported_classes'])}.")
        conf = 0.0
    if quality < 0.4:
        conf = min(conf, 0.5); reasons.append("Image quality is too low for reliable analysis.")
    elif quality < 0.7:
        conf *= 0.9; reasons.append("Reduced image quality lowered confidence.")
    if not synthetic:
        conf *= 0.85; reasons.append("Prototype heuristics are unvalidated on real imagery; confidence discounted.")
    if ev["analysis_type"] in ("object_detection", "segmentation") and not ev["items"]:
        conf = min(conf, 0.3); reasons.append("No supporting regions were found.")
    conf = round(conf, 3)
    return {"status": tier(conf), "confidence": conf, "reasons": reasons}
