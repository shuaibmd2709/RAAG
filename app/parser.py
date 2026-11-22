from anthropic import Anthropic
from pydantic import BaseModel, Field

from app.config import ANTHROPIC_API_KEY, PARSER_MODEL
from app.schema import Dish, Menu
from app.verify import verify_dishes


class ParsedDish(BaseModel):
    name: str
    category: str
    description: str
    price_eur: float | None = None
    dietary_tags: list[str] = Field(default_factory=list)
    allergens: list[str] = Field(default_factory=list)
    allergens_stated: bool = False


class ParsedMenu(BaseModel):
    restaurant: str
    currency: str = "EUR"
    dishes: list[ParsedDish]


SYSTEM = """You convert restaurant menu text into structured records. Rules:
- Copy dish names exactly as written. Never invent dishes, prices, tags or allergens.
- dietary_tags: only tags the menu marks for that dish (decode any legend such as VG=vegan, V=vegetarian, GF=gluten-free). Do NOT infer tags from ingredients.
- allergens: only allergens explicitly listed for that dish. Set allergens_stated=true ONLY if that dish's entry explicitly lists allergens; otherwise allergens=[] and allergens_stated=false.
- price_eur: number only, null if no price is shown.
- Use lowercase, singular, English allergen words (gluten, dairy, egg, nuts, fish, shellfish, soy) for allergens only. Keep category names as written."""


def parse_menu(text: str) -> tuple[Menu, list[str]]:
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    resp = client.messages.create(
        model=PARSER_MODEL,
        max_tokens=8000,
        system=SYSTEM,
        tools=[{
            "name": "record_menu",
            "description": "Record the parsed menu.",
            "input_schema": ParsedMenu.model_json_schema(),
        }],
        tool_choice={"type": "tool", "name": "record_menu"},
        messages=[{"role": "user", "content": f"Menu text:\n\n{text}"}],
    )
    block = next(b for b in resp.content if b.type == "tool_use")
    parsed = ParsedMenu(**block.input)

    dishes = [
        Dish(id=f"d{i:03d}", **{**p.model_dump(), "category": p.category.strip().title()})
        for i, p in enumerate(parsed.dishes, 1)
    ]
    dishes, warnings = verify_dishes(dishes, text)
    if resp.stop_reason == "max_tokens":
        warnings.append("OUTPUT TRUNCATED: menu too long for one call, some dishes may be missing")
    return Menu(restaurant=parsed.restaurant, currency=parsed.currency, dishes=dishes), warnings