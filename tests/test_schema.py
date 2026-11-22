import json
from pathlib import Path
from app.schema import Menu


def test_sample_menu_validates():
    data = json.loads(Path("data/sample_menu.json").read_text(encoding="utf-8"))
    menu = Menu(**data)
    assert len(menu.dishes) == 11
    assert len({d.id for d in menu.dishes}) == 11   # ids are unique


def test_unknown_allergens_are_not_reported_as_none():
    data = json.loads(Path("data/sample_menu.json").read_text(encoding="utf-8"))
    espresso = next(d for d in Menu(**data).dishes if d.id == "dr01")
    assert "not provided" in espresso.to_text()