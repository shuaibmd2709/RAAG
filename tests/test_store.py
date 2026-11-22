from app import embedder, store
from app.schema import Dish, Menu


def fake_embed(texts):
    return [[float(len(t) % 7), 1.0, 0.5] for t in texts]


def make_menu(*names, **dish_kw):
    return Menu(restaurant="R", dishes=[
        Dish(id=f"d{i}", name=n, category="Mains", description="x", **dish_kw)
        for i, n in enumerate(names)
    ])


def test_new_upload_replaces_old_menu(tmp_path, monkeypatch):
    monkeypatch.setattr(embedder, "embed", fake_embed)
    c = store._client(tmp_path)
    store.replace_menu(make_menu("A", "B"), c)
    assert store.replace_menu(make_menu("C"), c) == 1
    assert [h["dish"].name for h in store.search("anything", k=5, client=c)] == ["C"]


def test_metadata_flags_and_unknown_price(tmp_path, monkeypatch):
    monkeypatch.setattr(embedder, "embed", fake_embed)
    c = store._client(tmp_path)
    store.replace_menu(
        make_menu("A", dietary_tags=["vegan"], allergens=["nuts"], allergens_stated=True), c
    )
    md = c.get_collection("menu", embedding_function=None).get(ids=["d0"])["metadatas"][0]
    assert md["tag_vegan"] is True and md["allergen_nuts"] is True
    assert "price_eur" not in md