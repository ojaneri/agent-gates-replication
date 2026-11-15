"""Measure the wall-clock time of each C2 gate on the stored final C2 deliveries (RQ4, gate compute).

Offline: no agent is called. Each gate runs exactly as in the harness (mutation with 4 workers).
Usage: .venv/Scripts/python -m analysis.gate_timing
Output: data/processed/gate_timing.csv
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd

from gates.gate import run_tests, run_coverage, run_crap, run_bandit, TARGET
from gates.mutate import run_mutation, default_test_cmd

STUDY = Path(__file__).resolve().parents[1]
RAW = STUDY / "data" / "raw"


def timed(fn, *a, **k):
    t0 = time.perf_counter()
    r = fn(*a, **k)
    return r, time.perf_counter() - t0


def main() -> None:
    rows = []
    for m in sorted(RAW.glob("*/meta.json")):
        meta = json.loads(m.read_text(encoding="utf-8"))
        if meta["condition"] != "C2":
            continue
        d = str(m.parent / "final")
        _, t_tests = timed(run_tests, d)
        cov, t_cov = timed(run_coverage, d)
        _, t_crap = timed(run_crap, d, cov)
        mut, t_mut = timed(run_mutation, d, TARGET, default_test_cmd(), workers=4)
        _, t_sast = timed(run_bandit, d)
        rows.append({"run_id": meta["run_id"], "task": meta["task"], "model": meta["model"],
                     "mutants": mut["total"], "t_tests": t_tests, "t_coverage": t_cov, "t_crap": t_crap,
                     "t_mutation": t_mut, "t_security": t_sast,
                     "t_total": t_tests + t_cov + t_crap + t_mut + t_sast})
        print(json.dumps(rows[-1]), flush=True)
    out = STUDY / "data" / "processed" / "gate_timing.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    print("wrote", out)


if __name__ == "__main__":
    main()
