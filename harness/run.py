"""Run one experimental unit: agent x task x condition x repetition (protocol section 2).

Usage (from study root):
  .venv/Scripts/python -m harness.run --task T01-coupons --condition C2 --rep 1 --model claude-sonnet-5-5

Everything is written to data/raw/<run_id>/. The agent works in a fresh temporary directory
outside the study tree, so it cannot see the oracle, the reference or the seeded faults.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from gates.gate import evaluate, feedback_text, run_tests, DEFAULTS
from tasks.validate_tasks import load_faults, apply_fault

STUDY = Path(__file__).resolve().parents[1]
PROMPTS = STUDY / "harness" / "prompts"
RAW = STUDY / "data" / "raw"
VENV_SCRIPTS = Path(sys.executable).parent

ALLOWED_TOOLS = ["Read", "Write", "Edit", "Glob", "Grep",
                 "Bash(python -m pytest *)", "Bash(python -m pytest:*)",
                 "PowerShell(python -m pytest *)", "PowerShell(python -m pytest:*)"]


TOOLS_NO_SHELL = ["Read", "Write", "Edit", "Glob", "Grep"]


def tools_for(condition: str) -> list[str]:
    return TOOLS_NO_SHELL if condition == "CN" else ALLOWED_TOOLS


def build_prompt(condition: str, th: dict) -> str:
    if condition == "CN":
        return (PROMPTS / "base_CN.md").read_text(encoding="utf-8")
    gates =(PROMPTS / f"gates_{condition}.md").read_text(encoding="utf-8").format(
        cov_min_pct=f"{th['cov_min']:.0%}", crap_max=th["crap_max"], mut_min_pct=f"{th['mut_min']:.0%}")
    return (PROMPTS / "base.md").read_text(encoding="utf-8").replace("{gates}", "\n" + gates)


def agent_env() -> dict:
    env = dict(os.environ)
    # `python` inside the agent's shell resolves to the study's virtualenv
    env["PATH"] = str(VENV_SCRIPTS) + os.pathsep + env.get("PATH", "")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def call_agent(workdir: Path, prompt: str, model: str, session_id: str | None, budget: float,
               timeout: float, tools: list[str] | None = None) -> dict:
    cmd = ["claude", "-p", prompt, "--model", model, "--output-format", "stream-json", "--verbose",
           "--permission-mode", "dontAsk", "--allowedTools", *(tools or ALLOWED_TOOLS),
           "--strict-mcp-config", "--disable-slash-commands", "--setting-sources", "project",
           "--max-budget-usd", str(budget)]
    if session_id:
        cmd += ["--resume", session_id]
    t0 = time.time()
    try:
        r = subprocess.run(cmd, cwd=workdir, capture_output=True, text=True, encoding="utf-8",
                           timeout=timeout, env=agent_env())
    except subprocess.TimeoutExpired:
        return {"harness_error": "cli_timeout", "wall_s": round(time.time() - t0, 1)}
    out = {"wall_s": round(time.time() - t0, 1), "returncode": r.returncode, "stream": r.stdout}
    events = []
    for line in r.stdout.splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    result = next((e for e in reversed(events) if e.get("type") == "result"), None)
    if result is None:
        out["harness_error"] = "no_result_event"
        out["stderr_tail"] = r.stderr[-2000:]
        return out
    out["cli"] = result
    test_calls = []
    for e in events:
        if e.get("type") != "assistant":
            continue
        for c in (e.get("message") or {}).get("content") or []:
            if c.get("type") == "tool_use" and c.get("name") in ("Bash", "PowerShell"):
                cmd_txt = (c.get("input") or {}).get("command", "")
                if "pytest" in cmd_txt:
                    test_calls.append(cmd_txt)
    denied = [d.get("tool_input", {}).get("command", d.get("tool_name"))
              for d in result.get("permission_denials") or []]
    out["test_commands_attempted"] = len(test_calls)
    out["test_commands_denied"] = sum(1 for d in denied if d and "pytest" in str(d))
    out["denials"] = len(denied)
    return out


def _counts(tail: str) -> dict:
    c = {k: int(v) for v, k in re.findall(r"(\d+) (passed|failed|error|errors)", tail)}
    return {"passed": c.get("passed", 0), "failed": c.get("failed", 0) + c.get("error", 0) + c.get("errors", 0)}


def _with(solution_src: str, tests_dir: Path) -> dict:
    d = Path(tempfile.mkdtemp(prefix="eval_"))
    try:
        (d / "solution.py").write_text(solution_src, encoding="utf-8")
        shutil.copytree(tests_dir, d / "tests", ignore=shutil.ignore_patterns("__pycache__"))
        r = run_tests(str(d))
        return {"ok": r["passed"], "tail": r.get("tail", ""), **_counts(r.get("tail", ""))}
    finally:
        shutil.rmtree(d, ignore_errors=True)


def final_evaluation(task_dir: Path, final_dir: Path) -> dict:
    sol = (final_dir / "solution.py").read_text(encoding="utf-8")
    ref = (task_dir / "reference" / "solution.py").read_text(encoding="utf-8")
    agent_tests = final_dir / "tests"

    oracle = _with(sol, task_dir / "oracle")
    tot = oracle["passed"] + oracle["failed"]
    ev = {"oracle": {"all_passed": oracle["ok"], "passed": oracle["passed"], "failed": oracle["failed"],
                     "pass_fraction": round(oracle["passed"] / tot, 4) if tot else 0.0, "tail": oracle["tail"]}}
    ev["escaped_defect"] = not ev["oracle"]["all_passed"]

    ev["agent_wrote_tests"] = any(agent_tests.rglob("test*.py"))
    if not ev["agent_wrote_tests"]:  # CN baseline, or an agent that wrote no tests
        ev["tests_reject_reference"] = None
        ev["seeded_faults"] = []
        ev["seeded_detection_rate"] = None
    else:
        on_ref = _with(ref, agent_tests)
        ev["agent_tests_on_reference"] = {"passed": on_ref["passed"], "failed": on_ref["failed"],
                                          "tail": on_ref["tail"]}
        ev["tests_reject_reference"] = not on_ref["ok"]
        faults = []
        for f in load_faults(task_dir):
            r = _with(apply_fault(ref, f), agent_tests)
            faults.append({"id": f["id"], "class": f.get("class"), "detected": not r["ok"]})
        ev["seeded_faults"] = faults
        ev["seeded_detection_rate"] = None if ev["tests_reject_reference"] else round(
            sum(f["detected"] for f in faults) / len(faults), 4)

    # post-hoc gate metrics for every run, whatever its condition (for analysis only)
    post = evaluate(str(final_dir), "C2", mutation_workers=4)
    ev["posthoc"] = {
        "line_coverage": post["gates"]["coverage"]["line_coverage"] if ev["agent_wrote_tests"] else None,
        "max_crap": post["gates"]["crap"]["max_crap"],
        "mutation_score": post["gates"]["mutation"]["score"],
        "survivors": post["gates"]["mutation"]["survived"] if ev["agent_wrote_tests"] else None,
        "bandit_issues": len(post["gates"]["security"]["issues"]),
        "would_pass_C2": post["passed"],
    }
    text = sol + "".join(p.read_text(encoding="utf-8", errors="ignore") for p in agent_tests.rglob("*.py"))
    ev["gaming_markers"] = {"nosec": text.count("nosec"), "pragma_no_cover": text.count("pragma: no cover")}
    return ev


def snapshot(workdir: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(workdir / "solution.py", dest / "solution.py")
    if (workdir / "tests").exists():
        shutil.copytree(workdir / "tests", dest / "tests", dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    else:
        (dest / "tests").mkdir(exist_ok=True)


def run_unit(task: str, condition: str, rep: int, model: str, max_iters: int, budget_per_call: float,
             thresholds: dict | None = None, timeout: float = 1200) -> dict:
    th = {**DEFAULTS, **(thresholds or {})}
    task_dir = STUDY / "tasks" / task
    stamp = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    run_id = f"{task}_{condition}_r{rep}_{stamp}"
    out = RAW / run_id
    out.mkdir(parents=True)

    work = Path(tempfile.mkdtemp(prefix="agentrun_"))
    shutil.copy2(task_dir / "spec.md", work / "spec.md")
    shutil.copy2(task_dir / "stub" / "solution.py", work / "solution.py")
    (work / "tests").mkdir()

    cli_version = subprocess.run(["claude", "--version"], capture_output=True, text=True).stdout.strip()
    meta = {"run_id": run_id, "task": task, "condition": condition, "rep": rep, "model": model,
            "cli_version": cli_version, "thresholds": th, "max_iters": max_iters,
            "started": dt.datetime.now().isoformat(timespec="seconds"), "iterations": [], "workdir": str(work)}
    prompt = build_prompt(condition, th)
    (out / "prompt_initial.md").write_text(prompt, encoding="utf-8")

    session_id = None
    delivered = False
    harness_error = None
    for it in range(1, max_iters + 1):
        res = call_agent(work, prompt, model, session_id, budget_per_call, timeout, tools_for(condition))
        (out / f"iter{it}_stream.jsonl").write_text(res.pop("stream", ""), encoding="utf-8")
        (out / f"iter{it}_agent.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
        cli = res.get("cli", {})
        if "harness_error" in res:
            harness_error = res["harness_error"]
        session_id = cli.get("session_id", session_id)
        gate = evaluate(str(work), condition, th)
        (out / f"iter{it}_gate.json").write_text(json.dumps(gate, indent=2), encoding="utf-8")
        snapshot(work, out / f"iter{it}_code")
        meta["iterations"].append({"iter": it, "gate_passed": gate["passed"],
                                   "failed_gates": [k for k, v in gate["gates"].items() if not v["passed"]],
                                   "cost_usd": cli.get("total_cost_usd"), "turns": cli.get("num_turns"),
                                   "agent_wall_s": res.get("wall_s"), "cli_is_error": cli.get("is_error"),
                                   "test_commands_attempted": res.get("test_commands_attempted"),
                                   "test_commands_denied": res.get("test_commands_denied"),
                                   "denials": res.get("denials"),
                                   "cli_subtype": cli.get("subtype")})
        if harness_error:
            break
        if gate["passed"]:
            delivered = True
            break
        prompt = (PROMPTS / "feedback.md").read_text(encoding="utf-8").replace("{report}", feedback_text(gate))
        (out / f"prompt_feedback{it}.md").write_text(prompt, encoding="utf-8")

    snapshot(work, out / "final")
    meta.update(delivered=delivered, harness_error=harness_error,
                total_cost_usd=round(sum(i["cost_usd"] or 0 for i in meta["iterations"]), 4),
                rounds=len(meta["iterations"]), finished=dt.datetime.now().isoformat(timespec="seconds"))
    if not harness_error:
        meta["evaluation"] = final_evaluation(task_dir, out / "final")
    (out / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    shutil.rmtree(work, ignore_errors=True)
    return meta


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--condition", required=True, choices=["CN", "C0", "C1", "C2"])
    ap.add_argument("--rep", type=int, default=1)
    ap.add_argument("--model", default="claude-sonnet-5-5")
    ap.add_argument("--max-iters", type=int, default=3)
    ap.add_argument("--budget-per-call", type=float, default=1.50)
    a = ap.parse_args()
    m = run_unit(a.task, a.condition, a.rep, a.model, a.max_iters, a.budget_per_call)
    ev = m.get("evaluation", {})
    print(json.dumps({"run_id": m["run_id"], "delivered": m["delivered"], "rounds": m["rounds"],
                      "cost": m["total_cost_usd"], "harness_error": m["harness_error"],
                      "escaped_defect": ev.get("escaped_defect"), "oracle_pass": ev.get("oracle", {}).get("pass_fraction"),
                      "seeded_detection": ev.get("seeded_detection_rate"), "posthoc": ev.get("posthoc")}, indent=2))


if __name__ == "__main__":
    main()
