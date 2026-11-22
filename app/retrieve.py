from dataclasses import dataclass, field

from app import store
from app.query_plan import QueryPlan, understand
from app.schema import Dish

import re

UNSUPPORTED_LABELS = ["halal", "kosher", "koscher", "keto", "paleo", "organic"]

@dataclass
class Retrieval:
    plan: QueryPlan
    matches: list[Dish] = field(default_factory=list)
    unknown_allergen: list[Dish] = field(default_factory=list)
    unsupported: list[str] = field(default_factory=list)
    off_topic: bool = False


def normalize_plan(plan: QueryPlan, vocab: dict) -> tuple[QueryPlan, list[str]]:
    """Resolve the category to the stored spelling; report tags the menu never marks."""
    cats = {c.lower(): c for c in vocab["categories"]}
    plan.category = cats.get(plan.category.lower()) if plan.category else None
    tags = set(vocab["tags"])
    supported, unsupported = [], []
    for t in (x.lower().strip() for x in plan.require_tags):
        ok = t in tags or (t == "vegetarian" and "vegan" in tags)
        (supported if ok else unsupported).append(t)
    plan.require_tags = supported
    plan.exclude_allergens = [a.lower().strip() for a in plan.exclude_allergens]
    return plan, unsupported


def build_where(plan: QueryPlan) -> dict | None:
    conds = []
    if plan.category:
        conds.append({"category": plan.category})
    if plan.max_price is not None:
        conds.append({"price_eur": {"$lte": plan.max_price}})
    if plan.min_price is not None:
        conds.append({"price_eur": {"$gte": plan.min_price}})
    if not conds:
        return None
    return conds[0] if len(conds) == 1 else {"$and": conds}


def _has_tag(d: Dish, tag: str) -> bool:
    return tag in d.dietary_tags or (tag == "vegetarian" and "vegan" in d.dietary_tags)


def apply_rules(dishes: list[Dish], plan: QueryPlan) -> tuple[list[Dish], list[Dish]]:
    matches, unknown = [], []
    for d in dishes:
        if not all(_has_tag(d, t) for t in plan.require_tags):
            continue
        if plan.exclude_allergens:
            if not d.allergens_stated:
                unknown.append(d)          # cannot be proven safe
                continue
            if set(plan.exclude_allergens) & set(d.allergens):
                continue
        matches.append(d)
    return matches, unknown


RELEVANCE_MARGIN = 0.06   # heuristic, to be tuned in the eval


def cut_by_margin(hits: list[dict], margin: float = RELEVANCE_MARGIN) -> list[dict]:
    """Keep only hits close to the best one (hits are sorted by distance, ascending)."""
    if not hits:
        return hits
    best = hits[0]["distance"]
    return [h for h in hits if h["distance"] <= best + margin]


def _semantic_only(plan: QueryPlan) -> bool:
    return not (plan.category or plan.max_price is not None or plan.min_price is not None
                or plan.require_tags or plan.exclude_allergens)


def labels_in_question(question: str, vocab: dict) -> list[str]:
    q = question.lower()
    return [l for l in UNSUPPORTED_LABELS
            if re.search(rf"\b{l}\b", q) and l not in vocab["tags"]]

def retrieve(question: str, k: int = 6, client=None) -> Retrieval:
    v = store.vocab(client)
    plan = understand(question, v)
    forced = labels_in_question(question, v)
    if not plan.is_menu_question and not forced:
        return Retrieval(plan, off_topic=True)
    plan, unsupported = normalize_plan(plan, v)
    unsupported = sorted(set(unsupported) | set(forced))
    if unsupported:
        return Retrieval(plan, unsupported=unsupported)   # fail closed
    hits = store.search(plan.semantic_query, k=50, where=build_where(plan), client=client)
    if _semantic_only(plan):
        hits = cut_by_margin(hits)
    matches, unknown = apply_rules([h["dish"] for h in hits], plan)
    return Retrieval(plan, matches[:k], unknown[:k])


if __name__ == "__main__":
    import sys

    r = retrieve(" ".join(sys.argv[1:]))
    print("PLAN:       ", r.plan.model_dump(exclude_defaults=True))
    print("MATCHES:    ", [f"{d.name} ({d.price_eur})" for d in r.matches])
    print("UNKNOWN:    ", [d.name for d in r.unknown_allergen])
    print("UNSUPPORTED:", r.unsupported)