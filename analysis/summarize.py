"""Summarize all runs in data/raw into a CSV and a Markdown report.

Usage: .venv/Scripts/python -m analysis.summarize
Outputs: data/processed/runs.csv, analysis/pilot_summary.md
Descriptive only: the pilot is not used to test hypotheses (protocol section 9).
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

STUDY = Path(__file__).resolve().parents[1]
RAW = STUDY / "data" / "raw"
OUT_CSV = STUDY / "data" / "processed" / "runs.csv"
OUT_MD = STUDY / "analysis" / "pilot_summary.md"


def _nonblank(path: Path) -> int:
    try:
        return sum(1 for l in path.read_text(encoding="utf-8", errors="ignore").splitlines() if l.strip())
    except FileNotFoundError:
        return 0


def reading_load(run_dir: Path, task: str, survivors: int | None) -> dict:
    """RQ5 reading load (protocol section 4)."""
    final = run_dir / "final"
    line_review = _nonblank(final / "solution.py") + sum(_nonblank(p) for p in (final / "tests").rglob("*.py"))
    spec = _nonblank(STUDY / "tasks" / task / "spec.md")
    gate_summary = 6  # one line per gate result: tests, coverage, CRAP, mutation, security, overall
    gate_review = spec + gate_summary + (survivors or 0)
    return {"line_review_load": line_review, "gate_review_load": gate_review,
            "load_ratio": round(gate_review / line_review, 3) if line_review else None}


def load() -> pd.DataFrame:
    rows = []
    for m in sorted(RAW.glob("*/meta.json")):
        meta = json.loads(m.read_text(encoding="utf-8"))
        ev = meta.get("evaluation") or {}
        post = ev.get("posthoc") or {}
        faults = {f["id"]: f["detected"] for f in ev.get("seeded_faults", [])}
        rows.append({
            "run_id": meta["run_id"], "task": meta["task"], "condition": meta["condition"], "rep": meta["rep"],
            "model": meta["model"], "delivered": meta["delivered"], "rounds": meta["rounds"],
            "cost_usd": meta["total_cost_usd"], "harness_error": meta.get("harness_error"),
            "failed_gates_round1": ",".join(meta["iterations"][0]["failed_gates"]) if meta["iterations"] else "",
            "escaped_defect": ev.get("escaped_defect"),
            "oracle_pass_fraction": (ev.get("oracle") or {}).get("pass_fraction"),
            "tests_reject_reference": ev.get("tests_reject_reference"),
            "seeded_detection_rate": ev.get("seeded_detection_rate"),
            "faults_missed": ",".join(k for k, v in faults.items() if not v),
            "line_coverage": post.get("line_coverage"), "max_crap": post.get("max_crap"),
            "mutation_score": post.get("mutation_score"), "survivors": post.get("survivors"),
            "bandit_issues": post.get("bandit_issues"), "would_pass_C2": post.get("would_pass_C2"),
            "gaming_nosec": (ev.get("gaming_markers") or {}).get("nosec"),
            "gaming_pragma": (ev.get("gaming_markers") or {}).get("pragma_no_cover"),
            "agent_wall_s": sum(i.get("agent_wall_s") or 0 for i in meta["iterations"]),
            "test_cmds": sum(i.get("test_commands_attempted") or 0 for i in meta["iterations"]),
            "test_cmds_denied": sum(i.get("test_commands_denied") or 0 for i in meta["iterations"]),
            "denials": sum(i.get("denials") or 0 for i in meta["iterations"]),
            "accepted_and_correct": bool(meta["delivered"]) and ev.get("escaped_defect") is False,
            **reading_load(m.parent, meta["task"], post.get("survivors")),
        })
    return pd.DataFrame(rows)


def main() -> None:
    df = load()
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    ok = df[df["harness_error"].isna()]
    by = ok.groupby(["model", "condition"]).agg(
        runs=("run_id", "count"), delivered=("delivered", "mean"), escaped=("escaped_defect", "mean"),
        oracle_pass=("oracle_pass_fraction", "mean"), seeded_detection=("seeded_detection_rate", "mean"),
        mutation_score=("mutation_score", "mean"), max_crap=("max_crap", "mean"),
        rounds=("rounds", "mean"), cost_usd=("cost_usd", "mean"), wall_s=("agent_wall_s", "mean"),
        test_cmds=("test_cmds", "mean"), denials=("denials", "mean"),
        accepted_and_correct=("accepted_and_correct", "mean"),
        line_review_load=("line_review_load", "mean"), gate_review_load=("gate_review_load", "mean"),
        load_ratio=("load_ratio", "mean"),
    ).round(3)
    cols = ["model", "task", "condition", "rep", "delivered", "rounds", "cost_usd", "test_cmds", "denials",
            "failed_gates_round1", "escaped_defect",
            "oracle_pass_fraction", "tests_reject_reference", "seeded_detection_rate", "faults_missed",
            "line_coverage", "max_crap", "mutation_score", "survivors", "bandit_issues", "gaming_nosec",
            "gaming_pragma", "line_review_load", "gate_review_load", "load_ratio"]
    md = ["# Pilot summary (descriptive only)", "",
          f"Runs: {len(df)} total, {len(ok)} without harness error. Total cost: {df['cost_usd'].sum():.2f} USD.", "",
          "## By condition", "", by.to_markdown(), "",
          "## Per run", "", ok.sort_values(["model", "task", "condition", "rep"])[cols].to_markdown(index=False), ""]
    errs = df[df["harness_error"].notna()]
    if len(errs):
        md += ["## Harness errors", "", errs[["run_id", "harness_error"]].to_markdown(index=False), ""]
    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("\n".join(md))


if __name__ == "__main__":
    main()
