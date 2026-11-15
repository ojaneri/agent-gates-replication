"""Task validity checks (protocol section 3) and fault/operator overlap check (section 9).

Usage (from study root):  .venv/Scripts/python -m tasks.validate_tasks [TASK_ID ...]
Writes tasks/validation_report.json and exits non-zero if any check fails.
"""
from __future__ import annotations

import ast
import json
import shutil
import sys
import tempfile
from pathlib import Path

from gates.gate import run_tests, run_bandit
from gates.mutate import find_sites, mutant_source, run_mutation

TASKS = Path(__file__).resolve().parent


def load_faults(task: Path) -> list[dict]:
    faults = json.loads((task / "faults.json").read_text(encoding="utf-8"))
    for f in faults:
        if "edits" not in f:
            f["edits"] = [{"find": f["find"], "replace": f["replace"]}]
    return faults


def apply_fault(reference: str, fault: dict) -> str:
    src = reference
    for e in fault["edits"]:
        n = src.count(e["find"])
        if n != 1:
            raise ValueError(f"{fault['id']}: search text found {n} times (must be exactly 1): {e['find']!r}")
        src = src.replace(e["find"], e["replace"])
    return src


def _norm(src: str) -> str:
    return ast.unparse(ast.parse(src))


def oracle_run(task: Path, solution_src: str) -> dict:
    d = Path(tempfile.mkdtemp(prefix="oracle_"))
    try:
        (d / "solution.py").write_text(solution_src, encoding="utf-8")
        shutil.copytree(task / "oracle", d / "tests")
        return run_tests(str(d))
    finally:
        shutil.rmtree(d, ignore_errors=True)


def validate(task: Path) -> dict:
    ref = (task / "reference" / "solution.py").read_text(encoding="utf-8")
    rep = {"task": task.name, "checks": {}, "faults": []}
    r = oracle_run(task, ref)
    rep["checks"]["reference_passes_oracle"] = r["passed"]
    if not r["passed"]:
        rep["reference_failure"] = r["tail"]

    d = Path(tempfile.mkdtemp(prefix="bandit_"))
    (d / "solution.py").write_text(ref, encoding="utf-8")
    issues = [i for i in run_bandit(str(d)) if i["issue_severity"] in ("MEDIUM", "HIGH", "ERROR")]
    shutil.rmtree(d, ignore_errors=True)
    rep["checks"]["reference_passes_security_gate"] = not issues
    rep["reference_bandit_issues"] = issues

    mutants = {_norm(mutant_source(ref, s)): s.description for s in find_sites(ref)}
    all_detected = True
    for f in load_faults(task):
        entry = {"id": f["id"], "class": f.get("class"), "note": f.get("note")}
        try:
            faulty = apply_fault(ref, f)
        except ValueError as e:
            entry.update(applies=False, error=str(e))
            all_detected = False
            rep["faults"].append(entry)
            continue
        res = oracle_run(task, faulty)
        entry.update(applies=True, detected_by_oracle=not res["passed"],
                     same_as_gate_mutant=mutants.get(_norm(faulty)))
        all_detected &= entry["detected_by_oracle"]
        rep["faults"].append(entry)
    rep["checks"]["every_fault_applies_and_is_detected"] = all_detected

    # Oracle strength: mutation score of the hidden oracle against the reference (reported, not a gate)
    d = Path(tempfile.mkdtemp(prefix="ostr_"))
    try:
        (d / "solution.py").write_text(ref, encoding="utf-8")
        shutil.copytree(task / "oracle", d / "tests")
        m = run_mutation(str(d), workers=4)
        rep["oracle_strength"] = {"mutation_score": m["score"], "total": m["total"], "survived": m["survived"],
                                  "survivors": [f"line {s['lineno']}: {s['description']} | {s['code']}"
                                                for s in m["survivors"]]}
    finally:
        shutil.rmtree(d, ignore_errors=True)
    rep["valid"] = all(rep["checks"].values())
    return rep


def main(argv: list[str]) -> int:
    tasks = [TASKS / t for t in argv] if argv else sorted(p for p in TASKS.iterdir() if (p / "faults.json").exists())
    reports = [validate(t) for t in tasks]
    (TASKS / "validation_report.json").write_text(json.dumps(reports, indent=2), encoding="utf-8")
    for r in reports:
        print(f"{r['task']}: {'VALID' if r['valid'] else 'INVALID'}  {r['checks']}")
        for f in r["faults"]:
            flag = "detected" if f.get("detected_by_oracle") else "NOT DETECTED"
            ov = f" | same as gate mutant: {f['same_as_gate_mutant']}" if f.get("same_as_gate_mutant") else ""
            print(f"   {f['id']} {flag}{ov}" + (f"  ERROR {f['error']}" if f.get("error") else ""))
        o = r["oracle_strength"]
        print(f"   oracle mutation score: {o['mutation_score']} ({o['total'] - o['survived']}/{o['total']})")
        for s in o["survivors"]:
            print("     survivor:", s)
        if not r["checks"]["reference_passes_oracle"]:
            print(r.get("reference_failure", ""))
        for i in r["reference_bandit_issues"]:
            print("   bandit:", i)
    return 0 if all(r["valid"] for r in reports) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
