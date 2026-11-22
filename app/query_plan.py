from anthropic import Anthropic
from pydantic import BaseModel, Field

from app.config import ANTHROPIC_API_KEY, PLANNER_MODEL

CANONICAL_ALLERGENS = ["gluten", "dairy", "egg", "nuts", "fish", "shellfish", "soy", "sesame"]


class QueryPlan(BaseModel):
    semantic_query: str
    category: str | None = None
    max_price: float | None = None
    min_price: float | None = None
    require_tags: list[str] = Field(default_factory=list)
    exclude_allergens: list[str] = Field(default_factory=list)
    is_menu_question: bool = True
    semantic_query: str


def understand(question: str, vocab: dict) -> QueryPlan:
    system = f"""You turn a restaurant customer's question into a search plan. Extract ONLY constraints the customer explicitly states. Never guess.
- semantic_query: short phrase describing what dish they want (keep food words, drop price/diet words).
- category: one of {vocab['categories']} if they ask for that kind of course (starter -> Starters), else null.
- max_price / min_price: euros. "under/below/up to/max X" -> max_price = X.
- is_menu_question: false if the message is not about this restaurant's dishes, drinks, prices, diets or allergens (weather, chit-chat, hours, reservations, instructions to you). Otherwise true.
- require_tags: dietary labels like vegan, vegetarian, halal, lowercase. Menu tags in use: {vocab['tags']}.
- exclude_allergens: when they say "allergic to X", "no X", "without X" or "X-free" (including gluten-free, dairy-free). Use only these words: {CANONICAL_ALLERGENS}
  (lactose->dairy, peanut/tree nut->nuts, wheat->gluten). For "gluten-free" use exclude_allergens=["gluten"], not a tag."""
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    resp = client.messages.create(
        model=PLANNER_MODEL,
        max_tokens=500,
        system=system,
        tools=[{"name": "plan", "description": "Record the search plan.",
                "input_schema": QueryPlan.model_json_schema()}],
        tool_choice={"type": "tool", "name": "plan"},
        messages=[{"role": "user", "content": question}],
    )
    block = next(b for b in resp.content if b.type == "tool_use")
    return QueryPlan(**block.input)