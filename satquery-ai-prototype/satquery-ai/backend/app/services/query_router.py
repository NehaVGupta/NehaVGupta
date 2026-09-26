"""Deterministic natural-language intent router.

The `Router` interface is what an LLM-backed router would implement later (same output schema).
"""
import re
from dataclasses import asdict, dataclass, field

SEG_CLASSES = {
    "water": ["water", "lake", "river", "pond", "waterbod", "reservoir", "flood"],
    "vegetation": ["vegetation", "green", "forest", "tree", "crop", "field", "farmland", "canopy"],
    "built_up": ["built-up", "built up", "builtup", "urban area", "settlement"],
    "roads": ["road", "highway", "street", "path"],
    "bare_soil": ["soil", "barren", "bare"],
}
DET_CLASSES = {
    "building": ["building", "house", "structure", "roof"],
    "vehicle": ["vehicle", "car", "truck", "bus"],
    "ship": ["ship", "boat", "vessel"],
    "aircraft": ["aircraft", "plane", "airplane", "helicopter"],
    "agricultural_structure": ["barn", "agricultural structure", "farm structure", "greenhouse"],
}


@dataclass
class Intent:
    intent: str
    required_images: int = 1
    analysis_type: str = ""
    entities: dict = field(default_factory=dict)
    followup: str | None = None
    matched: list = field(default_factory=list)

    def dict(self):
        return asdict(self)


class Router:  # interface
    def route(self, query: str, has_second_image: bool, has_context: bool) -> Intent:
        raise NotImplementedError


def _find(q, table):
    return [k for k, words in table.items() if any(w in q for w in words)]


class RuleBasedRouter(Router):
    def route(self, query, has_second_image=False, has_context=False):
        q = re.sub(r"\s+", " ", query.lower().strip())
        ent, m = {}, []

        if has_context:
            fu = [("show_focus", r"\b(show|highlight|display|mark) (them|those|these|it)\b"),
                  ("new_items", r"\b(which|what) (ones|of them|are|is)? ?(are |is )?(new|newly|added|recent)|\bnew ones\b|which ones are new"),
                  ("low_confidence", r"low[- ]confidence|least confident|uncertain|unsure|weak"),
                  ("explain", r"\b(why|explain|evidence|how did|how do you know|support|justify)\b")]
            for name, pat in fu:
                if re.search(pat, q):
                    if name == "explain" and re.search(r"explain (this|the) (image|scene)|describe", q):
                        break
                    return Intent(f"followup_{name}", 0, "conversation_context", {}, name, [name])

        det = _find(q, DET_CLASSES)
        seg = _find(q, SEG_CLASSES)
        is_change = bool(re.search(r"\b(chang|compar|differen|before|after|between|new|grow|growth|expan|decreas|increas|loss|lost|cleared|deforest|construct|built since|appeared|disappear)", q))
        flood = bool(re.search(r"flood|inundat", q))

        if flood:
            return Intent("flood_assessment", 1, "water_extent_or_temporal", {"target": "water"}, None, ["flood"])
        if is_change and "how many" not in q.replace("changed", "") or re.search(r"how many .*(chang|new)", q):
            tgt = det[0] if det else (seg[0] if seg else None)
            if tgt:
                ent["target"] = {"building": "building", "vegetation": "vegetation", "water": "water"}.get(tgt, tgt)
            if re.search(r"major|significant|main|biggest|largest", q):
                ent["only_significant"] = True
            if re.search(r"decreas|loss|lost|cleared|deforest|reduc", q):
                ent["direction"] = "decrease"
            elif re.search(r"increas|grow|expan|gain", q):
                ent["direction"] = "increase"
            if re.search(r"chang|compar|differen|new|grow|decreas|increas|loss|cleared|construct", q):
                return Intent("change_detection", 2, "temporal_comparison", ent, None, ["change"] + ([tgt] if tgt else []))
        if re.search(r"\b(percent|percentage|how much|coverage|area of|extent)\b", q) and seg:
            return Intent("segmentation", 1, "land_cover_segmentation", {"class": seg[0]}, None, ["segment", seg[0]])
        if re.search(r"\b(where|show|highlight|map|locate)\b", q) and seg and not det:
            return Intent("segmentation", 1, "land_cover_segmentation", {"class": seg[0]}, None, ["segment", seg[0]])
        if det or re.search(r"how many|count|detect|objects?|large|big", q):
            if re.search(r"\b(large|big|largest|biggest)\b", q):
                ent["size"] = "large"
            ent["classes"] = det
            return Intent("object_detection", 1, "object_detection", ent, None, ["detect"] + det)
        if seg:
            return Intent("segmentation", 1, "land_cover_segmentation", {"class": seg[0]}, None, ["segment", seg[0]])
        if re.search(r"explain|describe|what is|what's|summar|overview|caption|tell me about", q):
            return Intent("image_understanding", 1, "scene_summary", {}, None, ["scene"])
        return Intent("unknown", 0, "none", {}, None, [])
