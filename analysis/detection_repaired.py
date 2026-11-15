"""Repaired fault detection for runs whose tests fail on the reference (post-run check).

Detection is undefined for such runs, and excluding them conditions on a post-treatment outcome. Here
each such suite is run on the reference, the test cases that fail there are recorded, and fault
detection is re-measured with only those cases deselected. Runs whose suite cannot be collected on the
reference (e.g. imports of private helpers) stay undefined.

Usage: .venv/Scripts/python -m analysis.detection_repaired
Output: data/processed/detection_repaired.csv
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

STUDY = Path(__file__).resolve().parents[1]
RAW = STUDY / "data" / "raw"
sys.path.insert(0, str(STUDY))
from harness.run import apply_fault, load_faults  # noqa: E402

PLUGIN = r'''
import os
MODE, PATH = os.environ["REPAIR_MODE"], os.environ["REPAIR_FILE"]
def pytest_collection_modifyitems(config, items):
    if MODE == "deselect":
        bad = set(open(PATH, encoding="utf-8").read().split("\x00")) - {""}
        keep = [i for i in items if i.nodeid not in bad]
        config.hook.pytest_deselected(items=[i for i in items if i.nodeid in bad])
        items[:] = keep
def pytest_runtest_logreport(report):
    if MODE == "record" and report.failed:
        with open(PATH, "a", encoding="utf-8") as fh:
            fh.write(report.nodeid + "\x00")
'''


def run(src: str, tests: Path, mode: str, listfile: Path) -> tuple[int, str]:
    d = Path(tempfile.mkdtemp(prefix="rep_"))
    try:
        (d / "solution.py").write_text(src, encoding="utf-8")
        shutil.copytree(tests, d / "tests", ignore=shutil.ignore_patterns("__pycache__"))
        (d / "repair_plugin.py").write_text(PLUGIN, encoding="utf-8")
        env = {**os.environ, "REPAIR_MODE": mode, "REPAIR_FILE": str(listfile), "PYTHONPATH": str(d)}
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-p", "repair_plugin",
                            "tests"], cwd=d, capture_output=True, text=True, timeout=300, env=env)
        return r.returncode, r.stdout[-400:]
    finally:
        shutil.rmtree(d, ignore_errors=True)


def main() -> None:
    rows = []
    for m in sorted(RAW.glob("*/meta.json")):
        meta = json.loads(m.read_text(encoding="utf-8"))
        ev = meta.get("evaluation", {})
        if not ev.get("tests_reject_reference"):
            continue
        task_dir = STUDY / "tasks" / meta["task"]
        ref = (task_dir / "reference" / "solution.py").read_text(encoding="utf-8")
        tests = m.parent / "final" / "tests"
        with tempfile.TemporaryDirectory() as td:
            lf = Path(td) / "failing.txt"
            lf.write_text("", encoding="utf-8")
            code, tail = run(ref, tests, "record", lf)
            failing = [x for x in lf.read_text(encoding="utf-8").split("\x00") if x]
            # 2 = interrupted (collection error), 5 = nothing collected
            code2, _ = run(ref, tests, "deselect", lf)
            usable = code2 == 0 and code != 2
            det, missed = None, None
            if usable:
                fl = load_faults(task_dir)
                hits = [run(apply_fault(ref, f), tests, "deselect", lf)[0] != 0 for f in fl]
                det = round(sum(hits) / len(hits), 4)
                missed = ",".join(f["id"] for f, h in zip(fl, hits) if not h)
        rows.append({"run_id": meta["run_id"], "task": meta["task"], "condition": meta["condition"],
                     "model": meta["model"], "n_failing_on_ref": len(failing), "usable": usable,
                     "detect_repaired": det, "missed_repaired": missed})
        print(meta["run_id"], len(failing), usable, det, flush=True)
    import pandas as pd
    pd.DataFrame(rows).to_csv(STUDY / "data" / "processed" / "detection_repaired.csv", index=False)
    print(f"{len(rows)} runs; usable {sum(r['usable'] for r in rows)}")


if __name__ == "__main__":
    main()
