from app.query_plan import QueryPlan
from app.retrieve import apply_rules, build_where, normalize_plan
from app.schema import Dish

VOCAB = {"categories": ["Desserts", "Starters"], "tags": ["vegan", "vegetarian"]}


def dish(name, **kw):
    return Dish(id=name, name=name, category="Starters", description="x", **kw)


def test_where_combines_category_and_price():
    plan = QueryPlan(semantic_query="x", category="Starters", max_price=8)
    assert build_where(plan) == {"$and": [{"category": "Starters"}, {"price_eur": {"$lte": 8}}]}
    assert build_where(QueryPlan(semantic_query="x")) is None


def test_vegan_counts_as_vegetarian():
    plan = QueryPlan(semantic_query="x", require_tags=["vegetarian"])
    matches, _ = apply_rules([dish("A", dietary_tags=["vegan"])], plan)
    assert [d.name for d in matches] == ["A"]


def test_allergen_rules():
    plan = QueryPlan(semantic_query="x", exclude_allergens=["nuts"])
    safe = dish("Safe", allergens=["dairy"], allergens_stated=True)
    bad = dish("Bad", allergens=["nuts"], allergens_stated=True)
    unk = dish("Unknown")                     # allergens_stated=False
    matches, unknown = apply_rules([safe, bad, unk], plan)
    assert [d.name for d in matches] == ["Safe"]
    assert [d.name for d in unknown] == ["Unknown"]


def test_unsupported_tag_and_category_casing():
    plan = QueryPlan(semantic_query="x", category="starters", require_tags=["Halal", "vegan"])
    plan, unsupported = normalize_plan(plan, VOCAB)
    assert plan.category == "Starters" and plan.require_tags == ["vegan"]
    assert unsupported == ["halal"]