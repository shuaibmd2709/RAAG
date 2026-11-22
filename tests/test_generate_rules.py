from app.generate import is_grounded, prices_in
from app.query_plan import QueryPlan
from app.retrieve import Retrieval, cut_by_margin
from app.schema import Dish
from app.generate import SAFETY_CLAIM

def test_prices_in_handles_formats():
    assert prices_in("costs €7.50 or 8,00 EUR and EUR 9") == {7.5, 8.0, 9.0}


def _r():
    d = Dish(id="a", name="A", category="Starters", description="x", price_eur=7.5)
    return Retrieval(QueryPlan(semantic_query="x", max_price=8), matches=[d])


def test_grounded_accepts_real_price_and_customer_limit():
    assert is_grounded("Bruschetta is €7.50, under your €8 limit.", "under 8", _r())


def test_invented_price_is_rejected():
    assert not is_grounded("Bruschetta is €5.00.", "under 8", _r())


def test_cut_by_margin_keeps_only_close_hits():
    hits = [{"distance": 0.60}, {"distance": 0.63}, {"distance": 0.69}]
    assert [h["distance"] for h in cut_by_margin(hits, 0.06)] == [0.60, 0.63]


def test_safety_claim_detected():
    assert SAFETY_CLAIM.search("All three desserts are safe for nut allergies")
    assert not SAFETY_CLAIM.search("No nuts are listed for these desserts")