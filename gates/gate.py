"""Gate pipeline for one working directory.

Layout expected in `workdir`: solution.py and tests/ (pytest).
Conditions (protocol section 2):
  C0: tests pass
  C1: C0 + line coverage >= cov_min
  C2: C1 + max CRAP < crap_max + mutation score >= mut_min + no bandit medium/high
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

from gates.crap import function_metrics
from gates.mutate import run_mutation, default_test_cmd

DEFAULTS = {"cov_min": 0.90, "crap_max": 10.0, "mut_min": 0.80}
TARGET = "solution.py"


def _env():
    return dict(os.environ, PYTHONDONTWRITEBYTECODE="1")


def run_tests(workdir: str, python: str = sys.executable, timeout: float = 120) -> dict:
    cmd = [python, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"]
    try:
        r = subprocess.run(cmd, cwd=workdir, capture_output=True, text=True, timeout=timeout, env=_env())
    except subprocess.TimeoutExpired:
        return {"passed": False, "returncode": None, "tail": "timeout"}
    tail = "\n".join((r.stdout or "").strip().splitlines()[-15:])
    # pytest exit code 5 = no tests collected
    return {"passed": r.returncode == 0, "returncode": r.returncode, "tail": tail}


RCFILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "coveragerc")


def run_coverage(workdir: str, python: str = sys.executable, timeout: float = 120) -> dict:
    # RCFILE disables exclusion pragmas, so "# pragma: no cover" cannot hide lines from the gate
    datafile = os.path.join(workdir, ".coverage.gate")
    env = dict(_env(), COVERAGE_FILE=datafile)
    subprocess.run([python, "-m", "coverage", "run", f"--rcfile={RCFILE}", f"--include={TARGET}", "-m", "pytest",
                    "-q", "-p", "no:cacheprovider", "tests"], cwd=workdir, capture_output=True, timeout=timeout,
                   env=env)
    out = os.path.join(workdir, ".coverage.gate.json")
    subprocess.run([python, "-m", "coverage", "json", f"--rcfile={RCFILE}", "-o", out], cwd=workdir,
                   capture_output=True, env=env)
    try:
        with open(out, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return {"line_coverage": 0.0, "executed": [], "missing": []}
    finally:
        for p in (out, datafile):
            if os.path.exists(p):
                os.remove(p)
    fdata = next((v for k, v in data.get("files", {}).items() if os.path.basename(k) == TARGET), None)
    if not fdata:
        return {"line_coverage": 0.0, "executed": [], "missing": []}
    ex, miss = fdata["executed_lines"], fdata["missing_lines"]
    total = len(ex) + len(miss)
    return {"line_coverage": round(len(ex) / total, 4) if total else 1.0, "executed": ex, "missing": miss}


def run_crap(workdir: str, cov: dict) -> list[dict]:
    with open(os.path.join(workdir, TARGET), encoding="utf-8") as f:
        src = f.read()
    stmts = set(cov["executed"]) | set(cov["missing"])
    if not stmts:
        # No coverage data at all (no tests, or tests never import the module): every function is
        # untested. Count every line as a statement so coverage is 0, not 1 (post-run check).
        stmts = set(range(1, len(src.splitlines()) + 1))
    return [m.as_dict() for m in function_metrics(src, set(cov["executed"]), stmts)]


def run_bandit(workdir: str, python: str = sys.executable) -> list[dict]:
    # --ignore-nosec: an agent must not be able to silence the scanner with a comment
    r = subprocess.run([python, "-m", "bandit", "-q", "--ignore-nosec", "-f", "json", TARGET], cwd=workdir,
                       capture_output=True, text=True, env=_env())
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError:
        return [{"issue_severity": "ERROR", "issue_text": "bandit failed: " + r.stderr[-300:], "line_number": 0,
                 "test_id": "-"}]
    return [{k: i[k] for k in ("test_id", "issue_severity", "issue_confidence", "issue_text", "line_number")}
            for i in data.get("results", [])]


def evaluate(workdir: str, condition: str, thresholds: dict | None = None, python: str = sys.executable,
             mutation_workers: int = 4) -> dict:
    """Run the gates for `condition` and return a JSON-able report."""
    th = {**DEFAULTS, **(thresholds or {})}
    rep: dict = {"condition": condition, "thresholds": th, "gates": {}}
    if condition == "CN":  # no-tests baseline: nothing is checked, the delivery is accepted as is
        rep["passed"] = True
        return rep
    tests = run_tests(workdir, python)
    rep["gates"]["tests"] = {"passed": tests["passed"], **tests}

    if condition in ("C1", "C2"):
        cov = run_coverage(workdir, python)
        rep["gates"]["coverage"] = {"passed": cov["line_coverage"] >= th["cov_min"],
                                    "line_coverage": cov["line_coverage"], "missing_lines": cov["missing"]}
    if condition == "C2":
        metrics = run_crap(workdir, cov)
        over = [m for m in metrics if m["crap"] >= th["crap_max"]]
        rep["gates"]["crap"] = {"passed": not over, "max_crap": max((m["crap"] for m in metrics), default=0.0),
                                "over_limit": over, "functions": metrics}
        if tests["passed"]:
            mut = run_mutation(workdir, TARGET, default_test_cmd(python), workers=mutation_workers)
        else:
            mut = {"baseline": "failed", "score": None, "total": 0, "killed": 0, "survived": 0, "survivors": []}
        rep["gates"]["mutation"] = {"passed": mut["score"] is not None and mut["score"] >= th["mut_min"], **mut}
        issues = [i for i in run_bandit(workdir, python) if i["issue_severity"] in ("MEDIUM", "HIGH", "ERROR")]
        rep["gates"]["security"] = {"passed": not issues, "issues": issues}

    rep["passed"] = all(g["passed"] for g in rep["gates"].values())
    return rep


def feedback_text(rep: dict, max_survivors: int = 25) -> str:
    """Human/agent-readable report of failing gates."""
    th = rep["thresholds"]
    g = rep["gates"]
    out = []
    if not g["tests"]["passed"]:
        out.append("GATE tests: FAILED. Your test suite does not pass (or no tests were collected).\n"
                   + g["tests"].get("tail", ""))
    if "coverage" in g and not g["coverage"]["passed"]:
        out.append(f"GATE coverage: FAILED. Line coverage of solution.py is {g['coverage']['line_coverage']:.1%}, "
                   f"required >= {th['cov_min']:.0%}. Lines never executed by tests: {g['coverage']['missing_lines']}")
    if "crap" in g and not g["crap"]["passed"]:
        rows = [f"  {m['name']} (line {m['lineno']}): complexity {m['complexity']}, coverage {m['coverage']:.0%}, "
                f"CRAP {m['crap']}" for m in g["crap"]["over_limit"]]
        out.append(f"GATE CRAP: FAILED. Every function must have CRAP < {th['crap_max']}. "
                   "CRAP = CC^2 * (1-coverage)^3 + CC, so reduce complexity and/or test more.\n" + "\n".join(rows))
    if "mutation" in g and not g["mutation"]["passed"]:
        m = g["mutation"]
        if m["score"] is None:
            out.append("GATE mutation: FAILED. Tests must pass before mutation testing can run.")
        else:
            rows = [f"  line {s['lineno']}: {s['description']}   | {s['code']}" for s in m["survivors"][:max_survivors]]
            more = "" if len(m["survivors"]) <= max_survivors else f"\n  ... and {len(m['survivors']) - max_survivors} more"
            out.append(f"GATE mutation: FAILED. Mutation score {m['score']:.1%} ({m['killed']}/{m['total']} killed), "
                       f"required >= {th['mut_min']:.0%}. Each surviving mutant is a change your tests did not detect:\n"
                       + "\n".join(rows) + more)
    if "security" in g and not g["security"]["passed"]:
        rows = [f"  line {i['line_number']}: [{i['test_id']} {i['issue_severity']}] {i['issue_text']}"
                for i in g["security"]["issues"]]
        out.append("GATE security (bandit): FAILED.\n" + "\n".join(rows))
    return "\n\n".join(out) if out else "All gates passed."


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("workdir")
    ap.add_argument("--condition", default="C2", choices=["C0", "C1", "C2"])
    a = ap.parse_args()
    r = evaluate(a.workdir, a.condition)
    print(feedback_text(r))
    print(json.dumps({"passed": r["passed"]}))
