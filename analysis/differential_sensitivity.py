"""Sensitivity of the differential generators: does each hand-written fault diverge from the reference?

Usage: .venv/Scripts/python -m analysis.differential_sensitivity [--tasks T07-password-policy ...] [--n 400]
Output: data/processed/differential_sensitivity.csv
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from analysis.differential import STUDY, WORKER


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=400)
    ap.add_argument("--tasks", nargs="*", default=None)
    a = ap.parse_args()
    worker = STUDY / "analysis" / "_diff_worker.py"
    worker.write_text(WORKER, encoding="utf-8")
    tasks = a.tasks or sorted(p.name for p in (STUDY / "tasks").glob("T*") if p.is_dir())
    rows = []
    for t in tasks:
        ref = STUDY / "tasks" / t / "reference" / "solution.py"
        src = ref.read_text(encoding="utf-8")
        for f in json.loads((STUDY / "tasks" / t / "faults.json").read_text(encoding="utf-8")):
            mutated = src
            for e in f.get("edits") or [{"find": f["find"], "replace": f["replace"]}]:
                mutated = mutated.replace(e["find"], e["replace"], 1)
            with tempfile.TemporaryDirectory() as d:
                p = Path(d) / "solution.py"
                p.write_text(mutated, encoding="utf-8")
                r = subprocess.run([sys.executable, str(worker), t, str(ref), str(p), str(a.n), "20261114"],
                                   capture_output=True, text=True, timeout=300)
            try:
                res = json.loads(r.stdout.strip().splitlines()[-1])
            except Exception:  # noqa: BLE001
                res = {"divergent": None, "error": r.stderr[-300:]}
            rows.append({"task": t, "fault": f["id"], "divergent": res.get("divergent"), "error": res.get("error", "")})
            print(t, f["id"], res.get("divergent"), res.get("error", "")[:120], flush=True)
    import pandas as pd
    df = pd.DataFrame(rows)
    out = STUDY / "data" / "processed" / "differential_sensitivity.csv"
    if a.tasks and out.exists():
        old = pd.read_csv(out)
        df = pd.concat([old[~old["task"].isin(tasks)], df], ignore_index=True)
    df.to_csv(out, index=False)
    print(f"detected {int((df['divergent'] > 0).sum())} of {len(df)} faults")


if __name__ == "__main__":
    main()
