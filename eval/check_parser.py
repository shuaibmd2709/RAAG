import json
from pathlib import Path

truth = {d["name"]: d for d in json.loads(Path("data/sample_menu.json").read_text(encoding="utf-8"))["dishes"]}
got = {d["name"]: d for d in json.loads(Path("data/parsed_menu.json").read_text(encoding="utf-8"))["dishes"]}

errors = 0
for name in truth.keys() | got.keys():
    if name not in got:
        print("MISSING:", name); errors += 1; continue
    if name not in truth:
        print("EXTRA:", name); errors += 1; continue
    t, g = truth[name], got[name]
    for f in ("category", "price_eur", "allergens_stated"):
        if t[f] != g[f]:
            print(f"{name}: {f} expected {t[f]!r}, got {g[f]!r}"); errors += 1
    for f in ("dietary_tags", "allergens"):
        if set(t[f]) != set(g[f]):
            print(f"{name}: {f} expected {sorted(t[f])}, got {sorted(g[f])}"); errors += 1

print(f"{len(truth)} dishes in truth, {errors} field errors")