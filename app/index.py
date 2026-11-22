import argparse
import json
from pathlib import Path

from app import store
from app.schema import Menu

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("menu", nargs="?", default="data/parsed_menu.json")
    ap.add_argument("--query", help="run a test search after indexing")
    args = ap.parse_args()

    menu = Menu(**json.loads(Path(args.menu).read_text(encoding="utf-8")))
    print(f"{store.replace_menu(menu)} dishes indexed")

    if args.query:
        for h in store.search(args.query, k=3):
            d = h["dish"]
            print(f"{h['distance']:.3f}  {d.name} ({d.category}, {d.price_eur} EUR, tags={d.dietary_tags})")