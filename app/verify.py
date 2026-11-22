import re
import unicodedata
from app.schema import Dish


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).lower().strip()


def price_variants(p: float) -> set[str]:
    a = f"{p:.2f}"                      # 7.50
    variants = {a, a.replace(".", ",")}  # 7,50
    if a.endswith("0"):
        b = a[:-1]                       # 7.5
        variants |= {b, b.replace(".", ",")}
    return variants


def verify_dishes(dishes: list[Dish], source_text: str) -> tuple[list[Dish], list[str]]:
    """Drop dishes not found in the source; null unverifiable prices; undo unsupported allergen claims."""
    src = norm(source_text)
    has_allergen_word = "allerg" in src
    kept, warnings = [], []

    for d in dishes:
        if norm(d.name) not in src:
            warnings.append(f"DROPPED '{d.name}': name not found in the PDF text")
            continue
        if d.price_eur is not None and not any(v in src for v in price_variants(d.price_eur)):
            warnings.append(f"'{d.name}': price {d.price_eur} not found in text, set to unknown")
            d.price_eur = None
        if d.allergens_stated and not has_allergen_word:
            warnings.append(f"'{d.name}': allergens claimed but the menu never mentions allergens, reset to unknown")
            d.allergens, d.allergens_stated = [], False
        kept.append(d)

    return kept, warnings