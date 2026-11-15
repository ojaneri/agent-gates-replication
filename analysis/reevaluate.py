"""Recompute the final evaluation of stored runs from their final code.

Use after any change to an oracle or to the fault list, so all runs are scored the same way.
Keys kept in meta.json:
  evaluation_original  the harness's evaluation under the frozen oracle (set once, never overwritten)
  evaluation_previous  the evaluation just before this re-run
  --keep-as NAME       additionally store the evaluation just before this re-run under NAME
Usage: .venv/Scripts/python -m analysis.reevaluate [--task T05-rate-limiter] [--keep-as evaluation_int_inputs]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json

from harness.run import RAW, STUDY, final_evaluation


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", default=None)
    ap.add_argument("--keep-as", default=None)
    a = ap.parse_args()
    n = 0
    for m in sorted(RAW.glob("*/meta.json")):
        meta = json.loads(m.read_text(encoding="utf-8"))
        if meta.get("harness_error") or (a.task and meta["task"] != a.task):
            continue
        if "evaluation_original" not in meta:
            meta["evaluation_original"] = meta.get("evaluation_previous", meta.get("evaluation"))
        if "evaluation" in meta:
            meta["evaluation_previous"] = meta["evaluation"]
            if a.keep_as:
                meta[a.keep_as] = meta["evaluation"]
        meta["evaluation"] = final_evaluation(STUDY / "tasks" / meta["task"], m.parent / "final")
        meta["evaluated_at"] = dt.datetime.now().isoformat(timespec="seconds")
        m.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        n += 1
        print(meta["run_id"], "escaped:", meta["evaluation"]["escaped_defect"])
    print(f"re-evaluated {n} runs")


if __name__ == "__main__":
    main()
