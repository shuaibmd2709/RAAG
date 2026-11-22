import chromadb
from app import embedder
from app.config import CHROMA_DIR
from app.schema import Dish, Menu
from functools import lru_cache

COLLECTION = "menu"

@lru_cache(maxsize=4)
def _client(path=None):
    return chromadb.PersistentClient(path=str(path or CHROMA_DIR))


def _metadata(d: Dish) -> dict:
    """Chroma metadata must be flat scalars, so lists become one boolean flag per value."""
    md = {
        "name": d.name,
        "category": d.category,
        "allergens_stated": d.allergens_stated,
        "dish_json": d.model_dump_json(),   # full record, so retrieval returns the exact card
    }
    if d.price_eur is not None:             # unknown price = no key, never a fake number
        md["price_eur"] = d.price_eur
    for t in d.dietary_tags:
        md[f"tag_{t}"] = True
    for a in d.allergens:
        md[f"allergen_{a}"] = True
    return md


def replace_menu(menu: Menu, client=None) -> int:
    """A new upload replaces the old menu: an outdated dish must never be served."""
    client = client or _client()
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass
    col = client.create_collection(COLLECTION, metadata={"hnsw:space": "cosine"}, embedding_function=None)
    docs = [d.to_text() for d in menu.dishes]
    col.add(
        ids=[d.id for d in menu.dishes],
        documents=docs,
        embeddings=embedder.embed(docs),
        metadatas=[_metadata(d) for d in menu.dishes],
    )
    return col.count()


def search(query: str, k: int = 4, where: dict | None = None, client=None) -> list[dict]:
    client = client or _client()
    col = client.get_collection(COLLECTION, embedding_function=None)
    n = min(k, col.count())
    if n == 0:
        return []
    res = col.query(query_embeddings=embedder.embed([query]), n_results=n, where=where)
    return [
        {"dish": Dish.model_validate_json(md["dish_json"]), "distance": dist}
        for md, dist in zip(res["metadatas"][0], res["distances"][0])
    ]

def vocab(client=None) -> dict:
    client = client or _client()
    col = client.get_collection(COLLECTION, embedding_function=None)
    dishes = [Dish.model_validate_json(m["dish_json"]) for m in col.get(include=["metadatas"])["metadatas"]]
    return {
        "categories": sorted({d.category for d in dishes}),
        "tags": sorted({t for d in dishes for t in d.dietary_tags}),
    }

def all_dishes(client=None) -> list[Dish]:
    client = client or _client()
    col = client.get_collection(COLLECTION, embedding_function=None)
    dishes = [Dish.model_validate_json(m["dish_json"]) for m in col.get(include=["metadatas"])["metadatas"]]
    return sorted(dishes, key=lambda d: d.id)