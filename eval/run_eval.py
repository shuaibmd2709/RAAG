import argparse
import json
import time
from collections import defaultdict
from pathlib import Path

from app import store
from app.generate import _llm_answer, answer
from app.query_plan import QueryPlan
from app.retrieve import Retrieval


def baseline_answer(question: str) -> str:
    """Naive RAG: top-3 similarity hits, no planner, no filters, no rules. Same generator prompt."""
    hits = store.search(question, k=3)
    r = Retrieval(QueryPlan(semantic_query=question), matches=[h["dish"] for h in hits])
    return _llm_answer(question, r)


def check(text: str, case: dict) -> list[str]:
    t = text.lower()
    fails = [f"missing '{s}'" for s in case.get("include", []) if s.lower() not in t]
    fails += [f"forbidden '{s}'" for s in case.get("exclude", []) if s.lower() in t]
    anys = case.get("include_any")
    if anys and not any(s.lower() in t for s in anys):
        fails.append("none of the expected phrases found")
    return fails


def run_one(fn, question: str, case: dict) -> dict:
    try:
        text = fn(question)
    except Exception as e:
        return {"pass": False, "fails": [f"error: {e}"], "answer": ""}
    fails = check(text, case)
    return {"pass": not fails, "fails": fails, "answer": text}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev", choices=["dev", "test", "post", "all"])
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--no-baseline", action="store_true")
    args = ap.parse_args()

    lines = Path("eval/golden.jsonl").read_text(encoding="utf-8").splitlines()
    cases = [json.loads(l) for l in lines if l.strip()]
    if args.split != "all":
        cases = [c for c in cases if c["split"] == args.split]

    systems = {"system": lambda q: answer(q)["answer"]}
    if not args.no_baseline:
        systems["baseline"] = baseline_answer

    runs = []
    for case in cases:
        for rep in range(args.repeats):
            row = {"id": case["id"], "type": case["type"], "question": case["question"], "rep": rep}
            for name, fn in systems.items():
                row[name] = run_one(fn, case["question"], case)
            runs.append(row)
            flags = "  ".join(f"{n}={'PASS' if row[n]['pass'] else 'FAIL'}" for n in systems)
            print(f"{case['id']} [{case['type']}] {flags}")
            for n in systems:
                for f in row[n]["fails"]:
                    print(f"      {n}: {f}")

    print("\n=== SUMMARY ===")
    for n in systems:
        ok = sum(r[n]["pass"] for r in runs)
        print(f"{n}: {ok}/{len(runs)} runs passed ({100 * ok / len(runs):.0f}%)")

    print("\nBy question type:")
    by_type = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for r in runs:
        for n in systems:
            by_type[r["type"]][n][0] += r[n]["pass"]
            by_type[r["type"]][n][1] += 1
    for t, d in sorted(by_type.items()):
        print(f"  {t:12s} " + "  ".join(f"{n}={d[n][0]}/{d[n][1]}" for n in systems))

    out_dir = Path("eval/results")
    out_dir.mkdir(exist_ok=True)
    out = out_dir / f"{args.split}_{int(time.time())}.json"
    out.write_text(json.dumps(runs, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nFull answers saved to {out}")


if __name__ == "__main__":
    main()