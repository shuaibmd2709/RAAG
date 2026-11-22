from pydantic import BaseModel, Field


class Dish(BaseModel):
    id: str
    name: str
    category: str
    description: str
    price_eur: float | None = None
    dietary_tags: list[str] = Field(default_factory=list)
    allergens: list[str] = Field(default_factory=list)
    allergens_stated: bool = False

    def to_text(self) -> str:
        """Text that gets embedded. Kept readable so semantic search works on natural questions."""
        parts = [f"{self.name} ({self.category}). {self.description}"]
        if self.price_eur is not None:
            parts.append(f"Price: {self.price_eur:.2f} EUR.")
        if self.dietary_tags:
            parts.append("Dietary: " + ", ".join(self.dietary_tags) + ".")
        if self.allergens_stated:
            parts.append("Allergens: " + (", ".join(self.allergens) or "none listed") + ".")
        else:
            parts.append("Allergen information not provided for this dish.")
        return " ".join(parts)


class Menu(BaseModel):
    restaurant: str
    currency: str = "EUR"
    dishes: list[Dish]