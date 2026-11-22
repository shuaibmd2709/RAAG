from app.schema import Dish
from app.verify import verify_dishes

TEXT = "Tiramisu EUR 6.50 Mascarpone cream. Allergens: gluten, egg, dairy"


def dish(**kw):
    base = dict(id="x", name="Tiramisu", category="Desserts", description="d")
    return Dish(**{**base, **kw})


def test_invented_dish_is_dropped():
    kept, warns = verify_dishes([dish(), dish(name="Lobster Thermidor")], TEXT)
    assert [d.name for d in kept] == ["Tiramisu"]
    assert any("DROPPED" in w for w in warns)


def test_wrong_price_becomes_unknown():
    kept, _ = verify_dishes([dish(price_eur=9.99)], TEXT)
    assert kept[0].price_eur is None


def test_price_comma_format_is_accepted():
    kept, _ = verify_dishes([dish(price_eur=6.5)], "Tiramisu 6,50")
    assert kept[0].price_eur == 6.5


def test_allergen_claim_without_allergen_word_is_reset():
    kept, warns = verify_dishes([dish(allergens=["egg"], allergens_stated=True)], "Tiramisu 6.50")
    assert kept[0].allergens_stated is False and kept[0].allergens == []
    assert warns