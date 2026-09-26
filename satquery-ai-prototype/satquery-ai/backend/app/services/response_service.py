"""Grounded response generation: text is composed ONLY from structured evidence (no free-form LLM)."""
from app.utils.confidence import INSUFFICIENT, PRELIMINARY, pct

PLURAL = {"building": "buildings", "vehicle": "vehicles", "ship": "ships", "agricultural_structure": "agricultural structures", "aircraft": "aircraft"}
LAND = {"water": "Water", "vegetation": "Vegetation", "built_up": "Built-up area", "roads": "Roads", "bare_soil": "Bare soil"}
TYPE_TXT = {"new_construction": "new construction", "vegetation_loss": "vegetation loss", "vegetation_gain": "vegetation gain", "water_increase": "water increase",
            "water_decrease": "water decrease", "structure_removed": "structure removed", "surface_change": "other surface change"}


def _plural(k, n):
    return f"{n} {PLURAL.get(k, k + 's')}" if n != 1 else f"1 {k.replace('_', ' ')}"


def _caveat(v):
    if v["status"] == "moderate":
        return f" Model confidence is moderate ({pct(v['confidence'])}) — manual review recommended."
    return f" Model confidence: {pct(v['confidence'])}."


def detection(ev, v):
    un, want = ev.get("unsupported_classes"), ev.get("requested_classes") or []
    if un:
        return f"The active prototype engine does not support detecting {', '.join(un)}. {INSUFFICIENT}"
    if not ev["items"]:
        what = ", ".join(PLURAL.get(c, c) for c in want) or "objects"
        return f"No {what} were detected by the prototype detector. {INSUFFICIENT}"
    if v["status"] == "insufficient":
        return f"{ev['count']} candidate objects were found but confidence is too low. {INSUFFICIENT}"
    counts = ev["class_counts"]
    if len(counts) == 1:
        (k, n), = counts.items()
        head = f"{_plural(k, n)} {'was' if n == 1 else 'were'} detected"
    else:
        head = "Detected " + ", ".join(_plural(k, n) for k, n in counts.items())
    extra = " (largest quartile by area)" if ev.get("size_filter") else ""
    return f"{head}{extra} with an average model confidence of {pct(v['confidence'])}.{'' if v['status'] == 'high' else ' Moderate confidence — manual review recommended.'}"


def segmentation(ev, v, flood=False):
    s, name = ev["stats"], LAND.get(ev["seg_class"], ev["seg_class"])
    if v["status"] == "insufficient" or not ev["items"]:
        return f"No reliable {name.lower()} regions were segmented. {INSUFFICIENT}"
    area = f" (≈ {s['area_km2']} km² at {s['gsd_m']} m/px)" if s.get("area_km2") is not None else ""
    if flood:
        return (f"The analysis identified regions with visual characteristics consistent with water presence, covering {s['area_pct']}% of the image{area}. "
                f"A single image cannot show whether this is flooding — load a before/after pair to assess change.{_caveat(v)} {PRELIMINARY}")
    return f"{name} covers {s['area_pct']}% of the image{area} across {s['regions']} region(s).{_caveat(v)}"


def change(ev, v, target=None):
    s = ev["stats"]
    if v["status"] == "insufficient" or (not ev["items"] and s["total_regions"] == 0):
        return f"No significant differences were found between the images. {INSUFFICIENT}" if s["total_regions"] == 0 else INSUFFICIENT
    if target:
        return (f"{len(ev['items'])} significant region(s) show {TYPE_TXT.get(target, target)}, covering ≈ {s['shown_pct']}% of the image.{_caveat(v)}")
    if ev.get("only_significant"):
        return (f"The {len(ev['items'])} major (significant) change regions, out of {s['total_regions']} detected, cover ≈ {s['shown_pct']}% of the image"
                f". Largest: {ev['items'][0]['id']} ({TYPE_TXT.get(ev['items'][0]['label'], ev['items'][0]['label'])}).{_caveat(v)}")
    types = ", ".join(f"{n} {TYPE_TXT.get(t, t)}" for t, n in s["significant_types"].items())
    km = f" (≈ {s['affected_km2']} km²)" if s.get("affected_km2") is not None else ""
    return (f"Detected {s['total_regions']} change regions, {s['significant_regions']} of them significant" + (f" ({types})" if types else "") +
            f". Changed area ≈ {s['changed_pct']}% of the image{km}.{_caveat(v)}")


def building_change(ev, v):
    s = ev["stats"]
    if not ev["items"]:
        return f"No buildings appear only in one image (before: {s['before_count']}, after: {s['after_count']}). {INSUFFICIENT if v['status'] == 'insufficient' else ''}".strip()
    corr = sum(1 for i in ev["items"] if i.get("corroborated"))
    return (f"{s['new']} building(s) appear only in the later image (before: {s['before_count']}, after: {s['after_count']}); "
            f"{corr} of {len(ev['items'])} are corroborated by an independent change region.{_caveat(v)}")


def flood(ev, v):
    s = ev["stats"]
    if not ev["items"]:
        return f"No regions of increased water extent were found between the images. {INSUFFICIENT}"
    km = f" (≈ {s['affected_km2']} km²)" if s.get("affected_km2") is not None else ""
    return (f"The analysis identified {len(ev['items'])} region(s) whose visual characteristics changed to be consistent with water presence, "
            f"covering ≈ {s['shown_pct']}% of the image{km}. Model confidence: {pct(v['confidence'])}. Expert verification is recommended. {PRELIMINARY}")


def scene(ev, v, caption):
    return f"{caption}{_caveat(v)}"
