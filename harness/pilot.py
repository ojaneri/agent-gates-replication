"""Pilot matrix (protocol section 6): tasks x conditions x reps, run sequentially in random order.

Skips units that already have a completed run in data/raw. Stops when the total cost cap is reached.
Usage: .venv/Scripts/python -m harness.pilot [--cap-usd 20]
"""
from __future__ import annotations

import argparse
import json
import random

from harness.run import RAW, run_unit

TASKS = ["T01-coupons", "T02-booking", "T03-product-search"]
CONDITIONS = ["C0", "C1", "C2"]


def done_units() -> tuple[set, float]:
    done, spent = set(), 0.0
    for m in RAW.glob("*/meta.json"):
        meta = json.loads(m.read_text(encoding="utf-8"))
        spent += meta.get("total_cost_usd") or 0
        if not meta.get("harness_error"):
            done.add((meta["task"], meta["condition"], meta["rep"], meta["model"]))
    return done, spent


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cap-usd", type=float, default=20.0)
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--seed", type=int, default=20261114)
    ap.add_argument("--model", default="claude-sonnet-5-5")
    ap.add_argument("--tasks", nargs="*", default=TASKS)
    ap.add_argument("--conditions", nargs="*", default=CONDITIONS)
    ap.add_argument("--max-iters", type=int, default=3)
    a = ap.parse_args()
    units = [(t, c, r) for t in a.tasks for c in a.conditions for r in range(1, a.reps + 1)]
    random.Random(a.seed).shuffle(units)
    for t, c, r in units:
        done, spent = done_units()
        if (t, c, r, a.model) in done:
            continue
        if spent >= a.cap_usd:
            print(f"cost cap reached: {spent:.2f} USD")
            break
        m = run_unit(t, c, r, a.model, max_iters=a.max_iters, budget_per_call=1.50)
        ev = m.get("evaluation", {})
        print(json.dumps({"unit": [t, c, r], "delivered": m["delivered"], "rounds": m["rounds"],
                          "cost": m["total_cost_usd"], "escaped": ev.get("escaped_defect"),
                          "detect": ev.get("seeded_detection_rate"), "err": m["harness_error"]}), flush=True)
    print("pilot finished; total spent %.2f USD" % done_units()[1])


if __name__ == "__main__":
    main()
