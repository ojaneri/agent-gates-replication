"""Cross-check the in-house mutation engine (gates/mutate.py) against cosmic-ray (protocol section 9, todo t-0005).

For every stored run, the agent's final code and tests are scored by both tools. Reports the
per-run scores and their Spearman correlation.
Usage: .venv/Scripts/python -m analysis.mutation_crosscheck
Outputs: data/processed/mutation_crosscheck.csv, analysis/mutation_crosscheck.md
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr

from gates.mutate import run_mutation

STUDY = Path(__file__).resolve().parents[1]
RAW = STUDY / "data" / "raw"
CR = str(Path(sys.executable).parent / "cosmic-ray.exe")

CFG = """[cosmic-ray]
module-path = "solution.py"
timeout = 20.0
excluded-modules = []
test-command = "{py} -m pytest -q -x -p no:cacheprovider tests"

[cosmic-ray.distributor]
name = "local"
"""


def cosmic_ray_score(src_dir: Path) -> dict:
    d = Path(tempfile.mkdtemp(prefix="cr_"))
    try:
        shutil.copy2(src_dir / "solution.py", d / "solution.py")
        shutil.copytree(src_dir / "tests", d / "tests", ignore=shutil.ignore_patterns("__pycache__"))
        (d / "cr.toml").write_text(CFG.format(py=sys.executable.replace("\\", "/")), encoding="utf-8")
        run = lambda *a: subprocess.run([CR, *a], cwd=d, capture_output=True, text=True, timeout=3600)
        run("init", "cr.toml", "s.sqlite")
        run("exec", "cr.toml", "s.sqlite")
        dump = run("dump", "s.sqlite").stdout
        killed = survived = incompetent = 0
        for line in dump.splitlines():
            try:
                _item, result = json.loads(line)
            except (ValueError, TypeError):
                continue
            outcome = (result or {}).get("test_outcome")
            if outcome == "killed":
                killed += 1
            elif outcome == "survived":
                survived += 1
            else:
                incompetent += 1
        total = killed + survived
        return {"cr_killed": killed, "cr_survived": survived, "cr_incompetent": incompetent,
                "cr_score": round(killed / total, 4) if total else None}
    finally:
        shutil.rmtree(d, ignore_errors=True)


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=str(RAW), help="folder of run folders (default data/raw)")
    ap.add_argument("--rep", type=int, default=None, help="only runs with this repetition number (sampling)")
    ap.add_argument("--tag", default="", help="suffix for the output files")
    a = ap.parse_args()
    rows = []
    for m in sorted(Path(a.source).glob("*/meta.json")):
        meta = json.loads(m.read_text(encoding="utf-8"))
        if meta.get("harness_error") or (a.rep is not None and meta.get("rep") != a.rep):
            continue
        final = m.parent / "final"
        if not any((final / "tests").rglob("test*.py")):
            continue  # CN deliveries have no tests to score
        ours = run_mutation(str(final), workers=4)
        cr = cosmic_ray_score(final)
        row = {"run_id": meta["run_id"], "task": meta["task"], "condition": meta["condition"],
               "model": meta["model"], "ours_total": ours["total"], "ours_score": ours["score"], **cr}
        rows.append(row)
        print(json.dumps(row), flush=True)
    df = pd.DataFrame(rows)
    out = STUDY / "data" / "processed" / f"mutation_crosscheck{a.tag}.csv"
    df.to_csv(out, index=False)
    ok = df.dropna(subset=["ours_score", "cr_score"])
    rho, p = spearmanr(ok["ours_score"], ok["cr_score"]) if len(ok) > 2 else (float("nan"), float("nan"))
    md = ["# Mutation engine cross-check (gates/mutate.py vs cosmic-ray 8.4.1)", "",
          f"Source: {a.source}", "",
          f"Runs compared: {len(ok)}. Spearman rho = {rho:.3f} (p = {p:.3g}).",
          f"Mean score: ours {ok['ours_score'].mean():.3f}, cosmic-ray {ok['cr_score'].mean():.3f}. "
          f"Mean mutants per run: ours {ok['ours_total'].mean():.1f}, cosmic-ray {(ok['cr_killed'] + ok['cr_survived']).mean():.1f}.",
          "", ok.to_markdown(index=False), ""]
    (STUDY / "analysis" / f"mutation_crosscheck{a.tag}.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md[:4]))


if __name__ == "__main__":
    main()
