"""Inspection of the mutants that survived the C2 gate in the final round (todo t-0006, (post-run check).

Each surviving mutant is rebuilt on the delivered module and classified by two independent checks:
  oracle-killed     the hidden oracle fails on the mutant: a real behaviour change the agent's tests missed
  diff-divergent    the oracle passes, but the differential generators (400 in-domain inputs) find a
                    difference between the mutant and the delivered module
  no-difference     neither check separates them: probably an equivalent mutant
Usage: .venv/Scripts/python -m analysis.survivor_inspection
Output: data/processed/survivor_inspection.csv
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

STUDY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STUDY))
from analysis.differential import WORKER  # noqa: E402
from gates.mutate import Site, mutant_source  # noqa: E402
from harness.run import _with  # noqa: E402

RAW = STUDY / "data" / "raw"


def main() -> None:
    worker = STUDY / "analysis" / "_diff_worker.py"
    worker.write_text(WORKER, encoding="utf-8")
    rows = []
    for run in sorted(p for p in RAW.glob("*_C2_*") if p.is_dir()):
        meta = json.loads((run / "meta.json").read_text(encoding="utf-8"))
        gates = sorted(run.glob("iter*_gate.json"))
        if not gates:
            continue
        mut = (json.loads(gates[-1].read_text(encoding="utf-8")).get("gates") or {}).get("mutation") or {}
        src = (run / "final" / "solution.py").read_text(encoding="utf-8")
        task_dir = STUDY / "tasks" / meta["task"]
        for s in mut.get("survivors") or []:
            site = Site(s["index"], s["variant"], s["lineno"], s["description"])
            msrc = mutant_source(src, site)
            oracle_killed = not _with(msrc, task_dir / "oracle")["ok"]
            divergent = None
            if not oracle_killed:
                with tempfile.TemporaryDirectory() as d:
                    a, b = Path(d) / "orig.py", Path(d) / "mut.py"
                    a.write_text(src, encoding="utf-8")
                    b.write_text(msrc, encoding="utf-8")
                    r = subprocess.run([sys.executable, str(worker), meta["task"], str(a), str(b), "400", "20261114"],
                                       capture_output=True, text=True, timeout=300)
                    try:
                        divergent = json.loads(r.stdout.strip().splitlines()[-1])["divergent"]
                    except Exception:  # noqa: BLE001
                        divergent = None
            cls = ("oracle-killed" if oracle_killed else "diff-divergent" if divergent else
                   "no-difference" if divergent == 0 else "error")
            rows.append({"run_id": meta["run_id"], "task": meta["task"], "model": meta["model"],
                         "line": s["lineno"], "mutation": s["description"], "code": s.get("code", ""),
                         "class": cls})
            print(meta["run_id"], s["lineno"], s["description"], cls, flush=True)
    import pandas as pd
    df = pd.DataFrame(rows)
    df.to_csv(STUDY / "data" / "processed" / "survivor_inspection.csv", index=False)
    print(df["class"].value_counts().to_string())


if __name__ == "__main__":
    main()
