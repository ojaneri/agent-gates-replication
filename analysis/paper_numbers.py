"""Generate every number and table used in the paper (paper/generated/*.tex) from the raw runs.

Usage: .venv/Scripts/python -m analysis.paper_numbers
Reads:  data/raw/*/meta.json, tasks/validation_report.json, tasks/*/oracle,
        analysis/reject_reference_classification.csv, data/processed/mutation_crosscheck*.csv,
        data/processed/gate_timing.csv
Writes: ../paper/generated/{numbers,tab_tasks,tab_results,tab_pertask,tab_sensitivity}.tex,
        data/processed/{main_runs,condition_summary}.csv
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd
from radon.complexity import cc_visit
from scipy.stats import wilcoxon, spearmanr

from tasks.validate_tasks import oracle_run

STUDY = Path(__file__).resolve().parents[1]
RAW = STUDY / "data" / "raw"
PILOT_V2 = STUDY / "data" / "pilot_v2"
PROC = STUDY / "data" / "processed"
OUT = STUDY.parent / "paper" / "generated"
COND_ORDER = ["CN", "C0", "C1", "C2"]
COND_NAME = {"CN": "CN", "C0": "Czero", "C1": "Cone", "C2": "Ctwo"}  # LaTeX macro names cannot contain digits
MODEL_SHORT = {"claude-haiku-5-5": "Haiku", "claude-sonnet-5-5": "Sonnet"}
RNG = np.random.default_rng(20261114)


# ---------------------------------------------------------------- helpers
def wilson(k: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def boot_mean_ci(x, b: int = 10000) -> tuple[float, float]:
    x = np.asarray([v for v in x if v is not None and not (isinstance(v, float) and math.isnan(v))], float)
    if len(x) < 2:
        return (float("nan"), float("nan"))
    means = RNG.choice(x, size=(b, len(x)), replace=True).mean(axis=1)
    return (float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)))


def boot_diff_ci(a, c, b: int = 10000) -> tuple[float, float]:
    a = np.asarray(a, float)
    c = np.asarray(c, float)
    d = RNG.choice(c, (b, len(c))).mean(1) - RNG.choice(a, (b, len(a))).mean(1)
    return (float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5)))


def cliffs_delta(a, c) -> float:
    a, c = list(a), list(c)
    gt = sum(1 for x in c for y in a if x > y)
    lt = sum(1 for x in c for y in a if x < y)
    return (gt - lt) / (len(a) * len(c)) if a and c else float("nan")


def _nonblank(p: Path) -> int:
    return sum(1 for l in p.read_text(encoding="utf-8", errors="ignore").splitlines() if l.strip()) if p.exists() else 0


def _funcs(src: str):
    for b in cc_visit(src):
        methods = getattr(b, "methods", None)
        if methods is not None:
            yield from methods
        else:
            yield b


def max_cc(src: str) -> int:
    return max((f.complexity for f in _funcs(src)), default=0)


def shape(src: str) -> tuple[int, int, int]:
    fs = list(_funcs(src))
    return (sum(f.complexity for f in fs), len(fs), sum(1 for l in src.splitlines() if l.strip()))


GAMING_RX = re.compile(r"pytest\.(skip|xfail|importorskip)|@pytest\.mark\.(skip|skipif|xfail)")


def fmt(x, nd=2, pct=False):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "--"
    return f"{100 * x:.0f}\\%" if pct else f"{x:.{nd}f}"


def sgn(x: float, nd: int = 1) -> str:
    """Signed number with a typographic minus for LaTeX."""
    s = f"{x:+.{nd}f}"
    return s.replace("-", "$-$")


def macro(name: str, value) -> str:
    assert re.fullmatch(r"[A-Za-z]+", name), name
    return f"\\newcommand{{\\{name}}}{{{value}}}"


# ---------------------------------------------------------------- data
def load_runs(report: list[dict]) -> pd.DataFrame:
    overlap = {(r["task"], f["id"]) for r in report for f in r["faults"] if f.get("same_as_gate_mutant")}
    rows = []
    for m in sorted(RAW.glob("*/meta.json")):
        meta = json.loads(m.read_text(encoding="utf-8"))
        if meta.get("harness_error"):
            continue
        ev = meta["evaluation"]
        post = ev.get("posthoc") or {}
        faults = ev.get("seeded_faults") or []
        nonov = [f for f in faults if (meta["task"], f["id"]) not in overlap]
        final = m.parent / "final"
        src = (final / "solution.py").read_text(encoding="utf-8")
        cc = max_cc(src)
        wrote = ev.get("agent_wrote_tests", True)
        # CRAP with no tests is CC^2 + CC (coverage 0). Stored post-hoc values for CN assumed coverage 1
        # (bug found in (post-run check); recompute here.
        crap = post.get("max_crap") if wrote else cc * cc + cc
        spec_lines = _nonblank(STUDY / "tasks" / meta["task"] / "spec.md")
        # symmetric reading load (post-run check): both reviewers read the specification
        line_load = spec_lines + _nonblank(final / "solution.py") + \
            sum(_nonblank(p) for p in (final / "tests").rglob("*.py"))
        total_cc, n_funcs, mod_lines = shape(src)
        test_txt = "".join(p.read_text(encoding="utf-8", errors="ignore") for p in (final / "tests").rglob("*.py"))
        rejected_by = [g for it in meta["iterations"][:-1] if not it["gate_passed"] for g in it["failed_gates"]]
        survivors = post.get("survivors") or 0
        false_rej = 0
        for it in meta["iterations"][:-1]:
            if not it["gate_passed"]:
                code = (m.parent / f"iter{it['iter']}_code" / "solution.py").read_text(encoding="utf-8")
                if oracle_run(STUDY / "tasks" / meta["task"], code)["passed"]:
                    false_rej += 1
        prev = meta.get("evaluation_original") or meta.get("evaluation_previous") or {}
        ints = meta.get("evaluation_int_inputs")
        rows.append({
            # runs never re-evaluated were evaluated only under the frozen oracle
            "escaped_original": bool(prev.get("escaped_defect")) if prev else bool(ev.get("escaped_defect")),
            "escaped_int_inputs": bool(ints.get("escaped_defect")) if ints else False,
            "oracle_failed": ev["oracle"]["failed"],
            "run_id": meta["run_id"], "task": meta["task"], "condition": meta["condition"], "model": meta["model"],
            "rep": meta["rep"], "cli": meta.get("cli_version", ""), "started": meta.get("started", ""),
            "delivered": meta["delivered"], "rounds": meta["rounds"], "cost": meta["total_cost_usd"],
            "escaped": bool(ev["escaped_defect"]), "oracle_pass": ev["oracle"]["pass_fraction"],
            "wrote_tests": wrote, "tests_reject_ref": ev.get("tests_reject_reference"),
            "detect": ev.get("seeded_detection_rate"),
            "detect_nonoverlap": (sum(f["detected"] for f in nonov) / len(nonov))
            if nonov and ev.get("tests_reject_reference") is False else None,
            "missed_faults": ",".join(f["id"] for f in faults if not f["detected"])
            if ev.get("tests_reject_reference") is False else "",
            "mutation": post.get("mutation_score"), "max_cc": cc, "max_crap": crap,
            "coverage": post.get("line_coverage"), "bandit": post.get("bandit_issues"),
            "nosec": (ev.get("gaming_markers") or {}).get("nosec", 0),
            "pragma": (ev.get("gaming_markers") or {}).get("pragma_no_cover", 0),
            "line_load": line_load, "spec_lines": spec_lines, "survivors": survivors,
            "gate_load": spec_lines + 6 + survivors,
            "rejected_rounds": sum(1 for it in meta["iterations"][:-1] if not it["gate_passed"]),
            "false_rejections": false_rej,
            "denials": sum(it.get("denials") or 0 for it in meta["iterations"]),
            "total_cc": total_cc, "n_funcs": n_funcs, "mod_lines": mod_lines,
            "conftest": int(any((final / "tests").rglob("conftest.py")) or (final / "conftest.py").exists()),
            "skips": len(GAMING_RX.findall(test_txt)),
            "rejected_by": ",".join(rejected_by),
            "wall_s": sum(it.get("agent_wall_s") or 0 for it in meta["iterations"]),
        })
    return pd.DataFrame(rows)


def passes(g: pd.DataFrame, crap_max: float, mut_min: float, cov_min: float = 0.90) -> pd.Series:
    return (g["coverage"].fillna(0) >= cov_min) & (g["max_crap"] < crap_max) & \
           (g["mutation"].fillna(0) >= mut_min) & (g["bandit"].fillna(0) == 0)


def oracle_cases(task_dir: Path) -> int:
    """Number of collected oracle test cases (parametrized cases counted individually)."""
    import shutil
    import subprocess
    import sys
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        shutil.copy(task_dir / "reference" / "solution.py", Path(d) / "solution.py")
        shutil.copy(task_dir / "oracle" / "test_oracle.py", Path(d) / "test_oracle.py")
        out = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"],
                             cwd=d, capture_output=True, text=True).stdout
    return sum(1 for line in out.splitlines() if "::" in line)


# ---------------------------------------------------------------- main
def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    report = json.loads((STUDY / "tasks" / "validation_report.json").read_text(encoding="utf-8"))
    df = load_runs(report)
    df.to_csv(PROC / "main_runs.csv", index=False)
    m: list[str] = []

    # ---- per condition x model summary
    rows = []
    for model in sorted(df["model"].unique()):
        for cond in COND_ORDER:
            g = df[(df.model == model) & (df.condition == cond)]
            if g.empty:
                continue
            k, n = int(g["escaped"].sum()), len(g)
            det = g["detect"].dropna()
            lo, hi = boot_mean_ci(det)
            rows.append({"model": model, "condition": cond, "runs": n, "escaped": k, "esc_hi": wilson(k, n)[1],
                         "det": det.mean() if len(det) else None, "det_lo": lo, "det_hi": hi, "det_n": len(det),
                         "det_nonov": g["detect_nonoverlap"].dropna().mean() if g["detect_nonoverlap"].notna().any() else None,
                         "reject_ref": int((g["tests_reject_ref"] == True).sum()),  # noqa: E712
                         "mutation": g["mutation"].dropna().mean() if g["mutation"].notna().any() else None,
                         "max_cc": g["max_cc"].mean(), "max_crap": g["max_crap"].mean(),
                         "pass_c2": passes(g, 10, 0.80).mean() if cond != "CN" else 0.0,
                         "rounds": g["rounds"].mean(), "cost": g["cost"].mean(),
                         "line_load": g["line_load"].mean(), "gate_load": g["gate_load"].mean(),
                         "survivors": g["survivors"].mean() if cond != "CN" else None})
    summ = pd.DataFrame(rows)
    summ.to_csv(PROC / "condition_summary.csv", index=False)

    # ---- global macros
    k_all, n_all = int(df["escaped"].sum()), len(df)
    m += [macro("numRuns", n_all), macro("numTasks", df["task"].nunique()), macro("numModels", df["model"].nunique()),
          macro("repsPerCell", int(df.groupby(["task", "condition", "model"]).size().max())),
          macro("totalCost", f"{df['cost'].sum():.2f}"), macro("totalEscaped", k_all),
          macro("escapeUpperAll", f"{100 * wilson(k_all, n_all)[1]:.1f}\\%"),
          macro("escapeUpperTasks", f"{100 * wilson(0, df['task'].nunique())[1]:.0f}\\%"),
          macro("cliVersion", "; ".join(sorted(set(df["cli"]))).replace("(Claude Code)", "").strip()),
          macro("runDate", sorted(df["started"])[0][:10]),
          macro("runFirst", sorted(df["started"])[0][11:16]), macro("runLast", sorted(df["started"])[-1][11:16]),
          macro("denialsMain", int(df["denials"].sum()))]
    pilot = [json.loads(p.read_text(encoding="utf-8")) for p in PILOT_V2.glob("*/meta.json")] if PILOT_V2.exists() else []
    m += [macro("pilotRuns", len(pilot)),
          macro("pilotEasy", sum(1 for p in pilot if p["task"] in ("T01-coupons", "T02-booking", "T03-product-search"))),
          macro("pilotCalib", sum(1 for p in pilot if p["task"] not in ("T01-coupons", "T02-booking", "T03-product-search")
                                  and p["condition"] == "C0")),
          macro("pilotSmoke", sum(1 for p in pilot if p["condition"] == "CN"))]
    m += [macro("oracleMutantsTotal", sum(r["oracle_strength"]["total"] for r in report)),
          macro("faultsTotal", sum(len(r["faults"]) for r in report)),
          macro("faultsOverlap", sum(1 for r in report for f in r["faults"] if f.get("same_as_gate_mutant"))),
          macro("nosecTotal", int(df["nosec"].sum())), macro("pragmaTotal", int(df["pragma"].sum())),
          macro("gamingRuns", int(((df["nosec"] > 0) | (df["pragma"] > 0)).sum())),
          macro("rejectedRounds", int(df["rejected_rounds"].sum())),
          macro("falseRejTotal", int(df["false_rejections"].sum())),
          macro("rejectRefTotal", int((df["tests_reject_ref"] == True).sum()))]  # noqa: E712
    gated = df[df.condition.isin(["C1", "C2"])]
    m.append(macro("rejectRefGated", int((gated["tests_reject_ref"] == True).sum())))  # noqa: E712
    m.append(macro("rejectRefCzeroAll", int((df[df.condition == "C0"]["tests_reject_ref"] == True).sum())))  # noqa: E712

    for _, r in summ.iterrows():
        key = MODEL_SHORT.get(r.model, "M") + COND_NAME[r.condition]
        m += [macro(f"esc{key}", f"{r.escaped}/{r.runs}"), macro(f"escHi{key}", fmt(r.esc_hi, pct=True)),
              macro(f"det{key}", fmt(r.det, pct=True)), macro(f"detN{key}", r.det_n),
              macro(f"detNonov{key}", fmt(r.det_nonov, pct=True)),
              macro(f"mut{key}", fmt(r.mutation, pct=True)), macro(f"cc{key}", fmt(r.max_cc, 1)),
              macro(f"crap{key}", fmt(r.max_crap, 1)), macro(f"passCtwo{key}", fmt(r.pass_c2, pct=True)),
              macro(f"rounds{key}", fmt(r.rounds, 2)), macro(f"cost{key}", fmt(r.cost, 3)),
              macro(f"lineLoad{key}", f"{r.line_load:.0f}"), macro(f"gateLoad{key}", f"{r.gate_load:.0f}"),
              macro(f"rejRef{key}", int(r.reject_ref))]

    for cond in COND_ORDER:
        g = df[df.condition == cond]
        cn = COND_NAME[cond]
        m += [macro(f"escPooled{cn}", f"{int(g['escaped'].sum())}/{len(g)}"),
              macro(f"escHiPooled{cn}", fmt(wilson(int(g["escaped"].sum()), len(g))[1], pct=True)),
              macro(f"ccPooled{cn}", fmt(g["max_cc"].mean(), 1)), macro(f"crapPooled{cn}", fmt(g["max_crap"].mean(), 1))]
    m.append(macro("specLinesMean", f"{df['spec_lines'].mean():.0f}"))

    # ---- RQ2 inference: C2 vs C0 per model
    for model in sorted(df["model"].unique()):
        a = df[(df.model == model) & (df.condition == "C0")]["detect"].dropna()
        c = df[(df.model == model) & (df.condition == "C2")]["detect"].dropna()
        lo, hi = boot_diff_ci(a, c)
        pa = df[(df.model == model) & (df.condition == "C0")].groupby("task")["detect"].mean()
        pc = df[(df.model == model) & (df.condition == "C2")].groupby("task")["detect"].mean()
        both = pd.concat([pa, pc], axis=1, keys=["a", "c"]).dropna()
        try:
            p = wilcoxon(both["c"], both["a"]).pvalue
        except ValueError:
            p = float("nan")
        key = MODEL_SHORT[model]
        m += [macro(f"detDiff{key}", sgn(100 * (c.mean() - a.mean()))),
              macro(f"detDiffLo{key}", sgn(100 * lo)), macro(f"detDiffHi{key}", sgn(100 * hi)),
              macro(f"detWilcoxonP{key}", f"{p:.3f}"), macro(f"detCliff{key}", f"{cliffs_delta(a, c):.2f}"),
              macro(f"detTasksDiffer{key}", int((both["c"] != both["a"]).sum()))]

    # ---- RQ1 under the original oracle (before the T05 float check) and per condition on T05
    if df["escaped_original"].notna().all():
        m.append(macro("escOriginalTotal", int(df["escaped_original"].sum())))
    m.append(macro("escIntInputs", int(df["escaped_int_inputs"].sum())))
    ii = df[df["escaped_int_inputs"]]
    for cond in COND_ORDER:
        m.append(macro(f"escInt{COND_NAME[cond]}", int((ii.condition == cond).sum())))
    t5c = df[df.task == "T05-rate-limiter"]
    m.append(macro("tfiveRuns", len(t5c)))
    # T05 suites that assert a float return type, per condition
    for cond in COND_ORDER:
        k = 0
        for rid in t5c[t5c.condition == cond]["run_id"]:
            lines = [l for p in (RAW / rid / "final" / "tests").rglob("*.py")
                     for l in p.read_text(encoding="utf-8", errors="ignore").splitlines()]
            k += int(any("isinstance" in l and "retry_after" in l and "float" in l for l in lines))
        m.append(macro(f"typedTests{COND_NAME[cond]}", k))
    # per-model SDs of cost, wall time and line load (round-5: pooled SDs mixed the model gap)
    for _, r in summ.iterrows():
        key = MODEL_SHORT.get(r.model, "M") + COND_NAME[r.condition]
        g = df[(df.model == r.model) & (df.condition == r.condition)]
        m += [macro(f"costSD{key}", f"{g['cost'].std():.3f}"), macro(f"wallSD{key}", f"{g['wall_s'].std():.0f}"),
              macro(f"lineLoadSD{key}", f"{g['line_load'].std():.0f}")]
    # tasks at full detection under both C0 and C2, per model
    for model in sorted(df["model"].unique()):
        sub = df[(df.model == model) & df.condition.isin(["C0", "C2"])].dropna(subset=["detect"])
        full = sub.groupby(["task", "condition"])["detect"].mean().unstack()
        m.append(macro(f"tasksFull{MODEL_SHORT[model]}", int(((full["C0"] >= 0.9999) & (full["C2"] >= 0.9999)).sum())))
    # dispersion for RQ4/RQ5 and gate-compliance means (pooled over models, per condition)
    for cond in COND_ORDER:
        g = df[df.condition == cond]
        cn = COND_NAME[cond]
        m += [macro(f"costSD{cn}", f"{g['cost'].std():.3f}"), macro(f"wallSD{cn}", f"{g['wall_s'].std():.0f}"),
              macro(f"lineLoadSD{cn}", f"{g['line_load'].std():.0f}"), macro(f"maxCCSD{cn}", f"{g['max_cc'].std():.1f}")]
    # within-task, within-model paired difference in total CC and function count, C2 - C0
    pair = df[df.condition.isin(["C0", "C2"])].groupby(["model", "task", "condition"])[["total_cc", "n_funcs"]].mean().unstack("condition")
    dcc = (pair[("total_cc", "C2")] - pair[("total_cc", "C0")]).to_numpy()
    dfn = (pair[("n_funcs", "C2")] - pair[("n_funcs", "C0")]).to_numpy()
    bs = [RNG.choice(dcc, len(dcc)).mean() for _ in range(10000)]
    m += [macro("ccPairDiff", sgn(dcc.mean())), macro("ccPairLo", sgn(np.percentile(bs, 2.5))),
          macro("ccPairHi", sgn(np.percentile(bs, 97.5))), macro("ccPairMin", sgn(dcc.min())),
          macro("ccPairMax", sgn(dcc.max())), macro("ccPairs", len(dcc)),
          macro("funcsUpPairs", int((dfn > 0).sum()))]
    # RQ3 clustering details
    fl = df[df["tests_reject_ref"] == True]  # noqa: E712
    m += [macro("rrHaikuCone", int(((fl.model == "claude-haiku-5-5") & (fl.condition == "C1")).sum())),
          macro("rrHaikuTfiveCone", int(((fl.model == "claude-haiku-5-5") & (fl.condition == "C1")
                                         & (fl.task == "T05-rate-limiter")).sum())),
          macro("rrWithPragma", int((fl["pragma"] > 0).sum()))]
    for col, name in (("total_cc", "totalCC"), ("n_funcs", "nFuncs")):
        for cond in ("CN", "C2"):
            g = df[df.condition == cond][col]
            m.append(macro(f"{name}SD{COND_NAME[cond]}", f"{g.std():.1f}"))
    esc_tasks = sorted(df[df.escaped]["task"].unique())
    m.append(macro("escTasks", ", ".join(t.split("-")[0] for t in esc_tasks) if esc_tasks else "none"))
    m.append(macro("escMaxOracleFailed", int(df[df.escaped]["oracle_failed"].max()) if df.escaped.any() else 0))
    t5 = df[df.task == "T05-rate-limiter"]
    for cond in COND_ORDER:
        g = t5[t5.condition == cond]
        m += [macro(f"escTfive{COND_NAME[cond]}", f"{int(g['escaped'].sum())}/{len(g)}")]
    from scipy.stats import fisher_exact as _fe
    a2, n2 = int(df[df.condition == "C2"]["escaped"].sum()), int((df.condition == "C2").sum())
    an, nn = int(df[df.condition == "CN"]["escaped"].sum()), int((df.condition == "CN").sum())
    m.append(macro("escFisherCtwoCN", f"{_fe([[a2, n2 - a2], [an, nn - an]])[1]:.2f}"))
    esc_c2_tests_typed = 0
    for rid in df[(df.condition == "C2") & df.escaped]["run_id"]:
        txt = "".join(p.read_text(encoding="utf-8", errors="ignore") for p in (RAW / rid / "final" / "tests").rglob("*.py"))
        esc_c2_tests_typed += int("isinstance" in txt and "float" in txt)
    m.append(macro("escCtwoTypedTests", esc_c2_tests_typed))

    # ---- RQ2 inference respecting the task blocking (post-run check)
    nz_pos = nz_all = 0
    for model in sorted(df["model"].unique()):
        key = MODEL_SHORT[model]
        sub = df[(df.model == model) & df.condition.isin(["C0", "C2"])].dropna(subset=["detect"])
        tasks = sorted(sub["task"].unique())
        cells = {(t, c): sub[(sub.task == t) & (sub.condition == c)]["detect"].to_numpy() for t in tasks for c in ("C0", "C2")}
        ok_tasks = [t for t in tasks if len(cells[(t, "C0")]) and len(cells[(t, "C2")])]
        bal = np.mean([cells[(t, "C2")].mean() - cells[(t, "C0")].mean() for t in ok_tasks])
        strat, clus = [], []
        for _ in range(10000):
            strat.append(np.mean([RNG.choice(cells[(t, "C2")], len(cells[(t, "C2")])).mean()
                                  - RNG.choice(cells[(t, "C0")], len(cells[(t, "C0")])).mean() for t in ok_tasks]))
            pick = RNG.choice(ok_tasks, len(ok_tasks))
            clus.append(np.mean([cells[(t, "C2")].mean() - cells[(t, "C0")].mean() for t in pick]))
        diffs = [cells[(t, "C2")].mean() - cells[(t, "C0")].mean() for t in ok_tasks]
        nz_pos += sum(1 for d in diffs if d > 1e-12)
        nz_all += sum(1 for d in diffs if abs(d) > 1e-12)
        m += [macro(f"detSignPos{key}", sum(1 for d in diffs if d > 1e-12)),
              macro(f"detSignAll{key}", sum(1 for d in diffs if abs(d) > 1e-12))]
        m += [macro(f"detBal{key}", sgn(100 * bal)),
              macro(f"detStratLo{key}", sgn(100 * np.percentile(strat, 2.5))),
              macro(f"detStratHi{key}", sgn(100 * np.percentile(strat, 97.5))),
              macro(f"detClusLo{key}", sgn(100 * np.percentile(clus, 2.5))),
              macro(f"detClusHi{key}", sgn(100 * np.percentile(clus, 97.5)))]
        c1 = df[(df.model == model) & (df.condition == "C1")]["detect"].dropna()
        c0 = df[(df.model == model) & (df.condition == "C0")]["detect"].dropna()
        m.append(macro(f"detDiffCone{key}", sgn(100 * (c1.mean() - c0.mean()))))
    from scipy.stats import binomtest, fisher_exact
    m += [macro("detSignPos", nz_pos), macro("detSignAll", nz_all),
          macro("detSignP", f"{binomtest(nz_pos, nz_all, 0.5).pvalue:.3f}" if nz_all else "--")]

    # ---- RQ3 rates per pooled condition, with Fisher tests against C0
    tw = df[df.wrote_tests]
    rr = {c: (int((tw[tw.condition == c]["tests_reject_ref"] == True).sum()), int((tw.condition == c).sum()))  # noqa: E712
          for c in ("C0", "C1", "C2")}
    for c, (k, n) in rr.items():
        m += [macro(f"rr{COND_NAME[c]}", k), macro(f"rrN{COND_NAME[c]}", n)]
    gk, gn = rr["C1"][0] + rr["C2"][0], rr["C1"][1] + rr["C2"][1]
    m += [macro("rrGated", gk), macro("rrNGated", gn),
          macro("rrFisherGated", f"{fisher_exact([[gk, gn - gk], [rr['C0'][0], rr['C0'][1] - rr['C0'][0]]])[1]:.2f}"),
          macro("rrFisherCone", f"{fisher_exact([[rr['C1'][0], rr['C1'][1] - rr['C1'][0]], [rr['C0'][0], rr['C0'][1] - rr['C0'][0]]])[1]:.2f}"),
          macro("rrFisherCtwo", f"{fisher_exact([[rr['C2'][0], rr['C2'][1] - rr['C2'][0]], [rr['C0'][0], rr['C0'][1] - rr['C0'][0]]])[1]:.2f}")]
    flagged_df = df[df["tests_reject_ref"] == True]  # noqa: E712
    m += [macro("rrSingleRound", int((flagged_df["rounds"] == 1).sum())),
          macro("rrTopTask", flagged_df["task"].value_counts().index[0].split("-")[0] if len(flagged_df) else "--"),
          macro("rrTopTaskN", int(flagged_df["task"].value_counts().iloc[0]) if len(flagged_df) else 0)]

    # ---- code shape, wall time, gaming, rejections, autonomy
    for cond in COND_ORDER:
        g = df[df.condition == cond]
        cn = COND_NAME[cond]
        m += [macro(f"totalCC{cn}", fmt(g["total_cc"].mean(), 1)), macro(f"nFuncs{cn}", fmt(g["n_funcs"].mean(), 1)),
              macro(f"modLines{cn}", fmt(g["mod_lines"].mean(), 1)), macro(f"runsPooled{cn}", len(g))]
    for _, r in summ.iterrows():
        key = MODEL_SHORT.get(r.model, "M") + COND_NAME[r.condition]
        g = df[(df.model == r.model) & (df.condition == r.condition)]
        m.append(macro(f"wall{key}", f"{g['wall_s'].mean():.0f}"))
    rej = pd.Series([x for s in df["rejected_by"] if s for x in s.split(",")]).value_counts()
    m += [macro("rejByCrap", int(rej.get("crap", 0))), macro("rejBySecurity", int(rej.get("security", 0))),
          macro("rejByMutation", int(rej.get("mutation", 0))), macro("rejByCoverage", int(rej.get("coverage", 0))),
          macro("conftestRuns", int(df["conftest"].sum())), macro("skipRuns", int((df["skips"] > 0).sum())),
          macro("deliveredAll", int(df["delivered"].sum())),
          macro("Tsixmutants", next(r["oracle_strength"]["total"] for r in report if r["task"].startswith("T06")))]
    dx = PROC / "differential.csv"
    if dx.exists():
        d = pd.read_csv(dx)
        m += [macro("diffDeliveries", len(d)), macro("diffInputs", int(d["n"].iloc[0])),
              macro("diffDivergent", int((d["divergent"] > 0).sum())),
              macro("diffComparisons", f"{len(d) * int(d['n'].iloc[0]):,}".replace(",", "{,}"))]

    # ---- RQ2: faults C2 tests missed
    c2 = df[df.condition == "C2"]
    missed = pd.Series([f"{t.split('-')[0]}~{f}" for t, s in zip(c2["task"], c2["missed_faults"]) if s
                        for f in s.split(",")]).value_counts()
    notes = {r["task"].split("-")[0] + "~" + f["id"]: f.get("note", "") for r in report for f in r["faults"]}
    m.append(macro("missedCtwo", ", ".join(f"{k} ({v}; {notes.get(k, '')})" for k, v in missed.items()) or "none"))
    m.append(macro("missedCtwoRuns", int((c2["missed_faults"] != "").sum())))
    m.append(macro("missedCtwoDenom", int((c2["tests_reject_ref"] == False).sum())))  # noqa: E712
    m.append(macro("missedFaultsTotal", int(missed.sum()) if len(missed) else 0))
    # same count under C0 and C1, as a baseline for the C2 figure (post-run check)
    for cond in ("C0", "C1"):
        g = df[df.condition == cond]
        m += [macro(f"missed{COND_NAME[cond]}Runs", int((g["missed_faults"].fillna("") != "").sum())),
              macro(f"missed{COND_NAME[cond]}Denom", int((g["tests_reject_ref"] == False).sum()))]  # noqa: E712
    m.append(macro("gatedRuns", int(df.condition.isin(["C1", "C2"]).sum())))
    m.append(macro("gateFeedbackRuns", int(df[df.condition.isin(["C1", "C2"])]["rounds"].gt(1).sum())))

    # ---- main run (T01-T06) vs extension (T07-T12), as the protocol addendum requires
    def rq2_bal(sub_df, model):
        sub = sub_df[(sub_df.model == model) & sub_df.condition.isin(["C0", "C2"])].dropna(subset=["detect"])
        cells = {(t, c): sub[(sub.task == t) & (sub.condition == c)]["detect"].to_numpy()
                 for t in sub["task"].unique() for c in ("C0", "C2")}
        ok = [t for t in sorted(sub["task"].unique()) if len(cells[(t, "C0")]) and len(cells[(t, "C2")])]
        d = np.array([cells[(t, "C2")].mean() - cells[(t, "C0")].mean() for t in ok])
        clus = [RNG.choice(d, len(d)).mean() for _ in range(10000)]
        return d.mean(), np.percentile(clus, 2.5), np.percentile(clus, 97.5), int((d > 1e-12).sum()), int((np.abs(d) > 1e-12).sum())
    main_tasks = {f"T0{i}" for i in range(1, 7)}
    parts = {"Main": df[df.task.str[:3].isin(main_tasks)], "Ext": df[~df.task.str[:3].isin(main_tasks)]}
    for pname, sub_df in parts.items():
        if sub_df.empty:
            continue
        k = int(sub_df["escaped"].sum())
        m += [macro(f"numRuns{pname}", len(sub_df)), macro(f"numTasks{pname}", sub_df["task"].nunique()),
              macro(f"esc{pname}", k), macro(f"escHi{pname}", f"{100 * wilson(k, len(sub_df))[1]:.1f}\\%"),
              macro(f"cost{pname}", f"{sub_df['cost'].sum():.2f}"),
              macro(f"rejRef{pname}", int((sub_df["tests_reject_ref"] == True).sum()))]  # noqa: E712
        for model in sorted(sub_df["model"].unique()):
            bal, lo, hi, pos, nz = rq2_bal(sub_df, model)
            key = MODEL_SHORT[model] + pname
            m += [macro(f"detBal{key}", sgn(100 * bal)), macro(f"detClusLo{key}", sgn(100 * lo)),
                  macro(f"detClusHi{key}", sgn(100 * hi)), macro(f"detSignPos{key}", pos), macro(f"detSignAll{key}", nz)]
    # ---- (post-run check): task-level inference and sensitivity to the post-treatment exclusion
    from scipy.stats import t as _t, binomtest as _bt
    rep_path = PROC / "detection_repaired.csv"
    rep = pd.read_csv(rep_path).set_index("run_id")["detect_repaired"] if rep_path.exists() else pd.Series(dtype=float)
    wt = df[df.wrote_tests].copy()
    undefined = wt["detect"].isna()
    variants = {"": wt["detect"],
                "Rep": wt["detect"].where(~undefined, wt["run_id"].map(rep)),
                "ImpZero": wt["detect"].where(~undefined, 0.0),
                "ImpOne": wt["detect"].where(~undefined, 1.0)}

    def task_diffs(col, model):
        g = wt.assign(v=col)[(wt.model == model) & wt.condition.isin(["C0", "C2"])].dropna(subset=["v"])
        piv = g.groupby(["task", "condition"])["v"].mean().unstack()
        piv = piv.dropna(subset=[c for c in ("C0", "C2") if c in piv])
        return (piv["C2"] - piv["C0"]), g
    for vname, col in variants.items():
        for model in sorted(wt["model"].unique()):
            d, g = task_diffs(col, model)
            key = MODEL_SHORT[model] + vname
            n = len(d)
            se = d.std(ddof=1) / np.sqrt(n) if n > 1 else float("nan")
            q = _t.ppf(0.975, n - 1) if n > 1 else float("nan")
            m += [macro(f"tdBal{key}", sgn(100 * d.mean())), macro(f"tdN{key}", n),
                  macro(f"tdTLo{key}", sgn(100 * (d.mean() - q * se), 2)), macro(f"tdTHi{key}", sgn(100 * (d.mean() + q * se), 2))]
            if vname == "":
                # within-task permutation of C0/C2 labels; one-sided p for a C2 > C0 difference
                obs = d.mean()
                cells = {t: (g[(g.task == t) & (g.condition == "C0")]["v"].to_numpy(),
                             g[(g.task == t) & (g.condition == "C2")]["v"].to_numpy()) for t in d.index}
                cnt = 0
                for _ in range(10000):
                    s = []
                    for a, c in cells.values():
                        pool = RNG.permutation(np.concatenate([a, c]))
                        s.append(pool[len(a):].mean() - pool[:len(a)].mean())
                    cnt += np.mean(s) >= obs - 1e-12
                m.append(macro(f"tdPermP{key}", f"{(cnt + 1) / 10001:.3f}"))
    # sign test over tasks (models averaged within task), as the addendum specified
    tdiff = []
    for t in sorted(wt["task"].unique()):
        vals = [task_diffs(variants[""], mod)[0].get(t) for mod in sorted(wt["model"].unique())]
        vals = [v for v in vals if v is not None and not pd.isna(v)]
        if vals:
            tdiff.append(np.mean(vals))
    tpos, tnz = sum(v > 1e-12 for v in tdiff), sum(abs(v) > 1e-12 for v in tdiff)
    m += [macro("taskSignPos", tpos), macro("taskSignAll", tnz), macro("taskSignDefined", len(tdiff)),
          macro("taskSignP", f"{_bt(tpos, tnz, 0.5).pvalue:.3f}" if tnz else "--"),
          macro("repUsable", int(rep.notna().sum())), macro("repTotal", len(rep)),
          macro("escapeUpperTasksOne", f"{100 * wilson(1, df['task'].nunique())[1]:.0f}\\%")]
    # RQ3 without T10 (round-7 VR-QN-04)
    nt = wt[wt.task != "T10-shipping"]
    for c in ("C0", "C1", "C2"):
        g = nt[nt.condition == c]
        m += [macro(f"rrNoTten{COND_NAME[c]}", int((g["tests_reject_ref"] == True).sum())),  # noqa: E712
              macro(f"rrNNoTten{COND_NAME[c]}", len(g))]
    from scipy.stats import fisher_exact as _fx
    for c in ("C1", "C2"):
        a = nt[nt.condition == c]; b = nt[nt.condition == "C0"]
        ka, kb = int((a["tests_reject_ref"] == True).sum()), int((b["tests_reject_ref"] == True).sum())  # noqa: E712
        m.append(macro(f"rrFisherNoTten{COND_NAME[c]}", f"{_fx([[ka, len(a) - ka], [kb, len(b) - kb]])[1]:.2f}"))
    m.append(macro("rrHaikuShare", int((df[df["tests_reject_ref"] == True]["model"] == "claude-haiku-5-5").sum())))  # noqa: E712
    mc0 = df[df.condition == "C0"]; mc2 = df[df.condition == "C2"]
    k0 = int((mc0["missed_faults"].fillna("") != "").sum()); n0 = int((mc0["tests_reject_ref"] == False).sum())  # noqa: E712
    k2 = int((mc2["missed_faults"].fillna("") != "").sum()); n2 = int((mc2["tests_reject_ref"] == False).sum())  # noqa: E712
    m.append(macro("missedFisher", f"{_fx([[k2, n2 - k2], [k0, n0 - k0]])[1]:.2f}"))

    # ---- (post-run check)
    if rep_path.exists():
        rp = pd.read_csv(rep_path)
        for c in ("C0", "C1", "C2"):
            g = df[(df.condition == c) & df.wrote_tests]
            base_k = int((g["missed_faults"].fillna("") != "").sum())
            base_n = int((g["tests_reject_ref"] == False).sum())  # noqa: E712
            r = rp[(rp.condition == c) & rp.usable]
            k = base_k + int(r["missed_repaired"].fillna("").astype(str).ne("").sum())
            m += [macro(f"missedRep{COND_NAME[c]}Runs", k), macro(f"missedRep{COND_NAME[c]}Denom", base_n + len(r))]
    gated_rr = df[(df["tests_reject_ref"] == True) & df.condition.isin(["C1", "C2"])]  # noqa: E712
    for c in ("C1", "C2"):
        g = gated_rr[gated_rr.condition == c]
        m += [macro(f"rrFirst{COND_NAME[c]}", int((g["rounds"] == 1).sum())), macro(f"rrAll{COND_NAME[c]}", len(g))]
    m.append(macro("rrFirstGated", int((gated_rr["rounds"] == 1).sum())))
    # sensitivity: T10 extreme-value cases counted as reference defects (round-8 VR-M-01)
    _cls = pd.read_csv(STUDY / "analysis" / "reject_reference_classification.csv")
    ext = set(_cls.loc[_cls["category"] == "extreme-value", "run_id"])
    m.append(macro("rrExtremeN", len(ext)))
    for c in ("C0", "C1", "C2"):
        g = df[(df.condition == c) & df.wrote_tests]
        k = int(((g["tests_reject_ref"] == True) & ~g["run_id"].isin(ext)).sum())  # noqa: E712
        m.append(macro(f"rrNoExt{COND_NAME[c]}", k))
    for model in sorted(wt["model"].unique()):
        col = wt["detect"].where(~(undefined & wt["run_id"].isin(ext)), wt["run_id"].map(rep))
        d, _ = task_diffs(col, model)
        m += [macro(f"tdBalNoExt{MODEL_SHORT[model]}", sgn(100 * d.mean())), macro(f"tdNNoExt{MODEL_SHORT[model]}", len(d))]
    # (post-run check), two-sided permutation p, RQ3 per task
    for model in sorted(wt["model"].unique()):
        d, _ = task_diffs(variants[""], model)
        sd, mu, n = d.std(ddof=1), abs(d.mean()), len(d)
        half = _t.ppf(0.975, n - 1) * sd / np.sqrt(n)
        need = next((k for k in range(3, 2000) if _t.ppf(0.975, k - 1) * sd / np.sqrt(k) < mu), None)
        key = MODEL_SHORT[model]
        m += [macro(f"tdHalf{key}", f"{100 * half:.1f}"), macro(f"tdNeed{key}", need if need else "--")]
    for model in sorted(wt["model"].unique()):
        key = MODEL_SHORT[model]
        one = float(next(x for x in m if x.startswith(f"\\newcommand{{\\tdPermP{key}}}")).split("{")[-1].rstrip("}"))
        m.append(macro(f"tdPermPTwo{key}", f"{min(1.0, 2 * one):.2f}"))
    up = dn = 0
    for t in sorted(wt["task"].unique()):
        g = wt[wt.task == t]
        k1 = int((g[g.condition == "C1"]["tests_reject_ref"] == True).sum())  # noqa: E712
        k0 = int((g[g.condition == "C0"]["tests_reject_ref"] == True).sum())  # noqa: E712
        up += k1 > k0; dn += k1 < k0
    m += [macro("rrTaskConeUp", up), macro("rrTaskConeDown", dn),
          macro("rrTaskConeP", f"{_bt(up, up + dn, 0.5).pvalue:.3f}" if up + dn else "--")]
    # (post-run check) and C2 first-round-only detection (VR-M07-01)
    from scipy.stats import fisher_exact as _fe2
    for model in sorted(wt["model"].unique()):
        key = MODEL_SHORT[model]
        g = wt[wt.model == model]
        k0 = int((g[g.condition == "C0"]["tests_reject_ref"] == True).sum()); n0 = int((g.condition == "C0").sum())  # noqa: E712
        for c in ("C1", "C2"):
            k = int((g[g.condition == c]["tests_reject_ref"] == True).sum()); n = int((g.condition == c).sum())  # noqa: E712
            m += [macro(f"rrBy{key}{COND_NAME[c]}", k),
                  macro(f"rrFisher{key}{COND_NAME[c]}", f"{_fe2([[k, n - k], [k0, n0 - k0]])[1]:.2f}")]
        m.append(macro(f"rrBy{key}Czero", k0))
    c2f = wt[(wt.condition == "C2") & (wt["rounds"] == 1)]["detect"].dropna()
    c2r = wt[(wt.condition == "C2") & (wt["rounds"] > 1)]["detect"].dropna()
    m += [macro("detCtwoFirst", fmt(c2f.mean(), pct=True)), macro("detCtwoFirstN", len(c2f)),
          macro("detCtwoFeedback", fmt(c2r.mean(), pct=True)), macro("detCtwoFeedbackN", len(c2r)),
          macro("detCzeroAll", fmt(wt[wt.condition == "C0"]["detect"].dropna().mean(), pct=True))]
    si = PROC / "survivor_inspection.csv"
    if si.exists():
        sv = pd.read_csv(si)
        m += [macro("survTotal", len(sv)), macro("survOracle", int((sv["class"] == "oracle-killed").sum())),
              macro("survDiff", int((sv["class"] == "diff-divergent").sum())),
              macro("survEquiv", int((sv["class"] == "no-difference").sum())),
              macro("survReal", int(sv["class"].isin(["oracle-killed", "diff-divergent"]).sum())),
              macro("survRuns", sv.loc[sv["class"].isin(["oracle-killed", "diff-divergent"]), "run_id"].nunique())]
    m.append(macro("costRatioHaiku", f"{100 * (df[(df.model == 'claude-haiku-5-5') & (df.condition == 'C2')]['cost'].mean() / df[(df.model == 'claude-haiku-5-5') & (df.condition == 'C0')]['cost'].mean() - 1):.0f}\\%"))
    m.append(macro("costRatioSonnet", f"{100 * (df[(df.model == 'claude-sonnet-5-5') & (df.condition == 'C2')]['cost'].mean() / df[(df.model == 'claude-sonnet-5-5') & (df.condition == 'C0')]['cost'].mean() - 1):.0f}\\%"))

    ds = PROC / "differential_sensitivity.csv"
    if ds.exists():
        s = pd.read_csv(ds)
        und = s[~(s["divergent"] > 0)]
        m += [macro("diffSensDetected", int((s["divergent"] > 0).sum())), macro("diffSensTotal", len(s)),
              macro("diffSensMissed", ", ".join(f"{t.split('-')[0]}~{f}" for t, f in zip(und["task"], und["fault"])) or "none")]

    # ---- RQ3 classification
    cls = pd.read_csv(STUDY / "analysis" / "reject_reference_classification.csv")
    flagged = set(df.loc[df["tests_reject_ref"] == True, "run_id"])  # noqa: E712
    if flagged - set(cls["run_id"]):
        raise SystemExit(f"unclassified reject-reference runs: {sorted(flagged - set(cls['run_id']))}")
    cls = cls[cls["run_id"].isin(flagged)]
    allcls = pd.read_csv(STUDY / "analysis" / "reject_reference_classification.csv")
    m.append(macro("rejSpecCorrect", int((allcls["category"] == "spec-correct").sum())))
    m += [macro("rejInputType", int((cls["category"] == "input-type").sum())),
          macro("rejReturnType", int((cls["category"] == "return-type").sum())),
          macro("rejBoth", int((cls["category"] == "both").sum())),
          macro("rejPrivateApi", int((cls["category"] == "private-api").sum())),
          macro("rejMessage", int((cls["category"] == "message").sum())),
          macro("rejExtreme", int((cls["category"] == "extreme-value").sum())),
          macro("rejSpecCorrectExt", int(((allcls["category"] == "spec-correct")
                                          & ~allcls["run_id"].str[:3].isin(main_tasks)).sum()))]
    esc_now = df[df.escaped]
    m.append(macro("escWhere", "; ".join(f"{r.task.split('-')[0]} {r.condition} ({MODEL_SHORT[r.model]})"
                                         for r in esc_now.itertuples()) or "none"))
    m.append(macro("escOriginalExt", int(parts["Ext"]["escaped_original"].sum()) if "Ext" in parts else 0))
    fr = df[df["rejected_rounds"] > 0]
    m.append(macro("rejRunsCrap", int(fr["rejected_by"].str.contains("crap").sum())))
    m.append(macro("rejRunsMutation", int(fr["rejected_by"].str.contains("mutation").sum())))
    m.append(macro("rejRunsSecurity", int(fr["rejected_by"].str.contains("security").sum())))

    # ---- RQ4: gate timing
    gt = PROC / "gate_timing.csv"
    if gt.exists():
        t = pd.read_csv(gt)
        m += [macro("gateTimeMedian", f"{t['t_total'].median():.0f}"), macro("gateTimeMax", f"{t['t_total'].max():.0f}"),
              macro("gateMutShare", f"{100 * (t['t_mutation'].sum() / t['t_total'].sum()):.0f}\\%"),
              macro("gateTimeRuns", len(t))]

    # ---- mutation cross-checks
    for tag, name in (("", "Pilot"), ("_main_rep1", "Main")):
        xc = PROC / f"mutation_crosscheck{tag}.csv"
        if xc.exists():
            x = pd.read_csv(xc).dropna(subset=["ours_score", "cr_score"])
            if len(x) > 2:
                rho, p = spearmanr(x["ours_score"], x["cr_score"])
                m += [macro(f"xc{name}Runs", len(x)), macro(f"xc{name}Rho", f"{rho:.2f}"),
                      macro(f"xc{name}P", f"{p:.1g}"),
                      macro(f"xc{name}OursMean", fmt(x["ours_score"].mean(), pct=True)),
                      macro(f"xc{name}CrMean", fmt(x["cr_score"].mean(), pct=True)),
                      macro(f"xc{name}OursMutants", f"{x['ours_total'].mean():.0f}"),
                      macro(f"xc{name}CrMutants", f"{(x['cr_killed'] + x['cr_survived']).mean():.0f}")]

    (OUT / "numbers.tex").write_text("% generated by study/analysis/paper_numbers.py -- do not edit\n" + "\n".join(m) + "\n",
                                     encoding="utf-8")

    # ---- Table I: tasks
    t = ["% generated by study/analysis/paper_numbers.py -- do not edit",
         "\\begin{table}[t]\\centering\\caption{Tasks. Tests: hidden oracle test cases. Faults: hand-written faults "
         "(in parentheses, how many equal a gate mutant). Strength: share of our engine's mutants of the reference that "
         "the oracle kills. CWE: Common Weakness Enumeration entry of the security trap.}\\label{tab:tasks}",
         "\\small\\setlength{\\tabcolsep}{2.5pt}", "\\begin{tabular}{@{}llrrrl@{}}\\toprule",
         "Task & Domain & Tests & Faults & Strength & CWE\\\\\\midrule"]
    for r in report:
        meta = json.loads((STUDY / "tasks" / r["task"] / "metadata.json").read_text(encoding="utf-8"))
        ntests = oracle_cases(STUDY / "tasks" / r["task"])
        o = r["oracle_strength"]
        ov = sum(1 for f in r["faults"] if f.get("same_as_gate_mutant"))
        name = r["task"].split("-", 1)
        t.append(f"{name[0]} {name[1].replace('-', ' ')} & {meta['domain'].split(' /')[0]} & {ntests} & "
                 f"{len(r['faults'])} ({ov}) & {o['total'] - o['survived']}/{o['total']} & "
                 f"{', '.join(c.replace('CWE-', '') for c in meta.get('cwe') or []) or '--'}\\\\")
    t += ["\\bottomrule\\end{tabular}\\end{table}"]
    (OUT / "tab_tasks.tex").write_text("\n".join(t) + "\n", encoding="utf-8")

    # ---- Table II: results per model and condition
    r = ["% generated by study/analysis/paper_numbers.py -- do not edit",
         f"\\begin{{table*}}[t]\\centering\\caption{{Part A per model and condition ({len(df) // max(1, len(summ))} runs per row). "
         "Escaped: deliveries failing the hidden oracle, with the Wilson 95\\% upper bound. "
         "Detection: mean share of hand-written faults detected, with bootstrap 95\\% confidence interval (CI; "
         "runs resampled, tasks ignored) and the number of runs $n$ for which it is defined. Read: lines a reviewer reads under gate-based and "
         "under line-by-line review (RQ5). Measures are defined in Section~\\ref{sec:measures}.}"
         "\\label{tab:results}",
         "\\small\\setlength{\\tabcolsep}{4pt}",
         "\\begin{tabular}{@{}llrlrrrrrrr@{}}\\toprule",
         "Model & Cond. & Escaped & Detection [95\\% CI] ($n$) & Mutation & Max CC & Max CRAP & Rounds & "
         "Cost (USD) & Read (gate) & Read (line)\\\\\\midrule"]
    for _, s in summ.iterrows():
        det = "--" if s.det is None or (isinstance(s.det, float) and math.isnan(s.det)) else \
            f"{100 * s.det:.0f}\\% [{100 * s.det_lo:.0f}, {100 * s.det_hi:.0f}] ({s.det_n})"
        r.append(f"{MODEL_SHORT[s.model]} & {s.condition} & {s.escaped} ($\\leq${fmt(s.esc_hi, pct=True)}) & {det} & "
                 f"{fmt(s.mutation, pct=True)} & {fmt(s.max_cc, 1)} & {fmt(s.max_crap, 1)} & {fmt(s.rounds, 2)} & "
                 f"{fmt(s.cost, 3)} & {'--' if s.condition == 'CN' else f'{s.gate_load:.0f}'} & {s.line_load:.0f}\\\\")
    r += ["\\bottomrule\\end{tabular}\\end{table*}"]
    (OUT / "tab_results.tex").write_text("\n".join(r) + "\n", encoding="utf-8")

    # ---- Table III: per task (models pooled)
    pt = ["% generated by study/analysis/paper_numbers.py -- do not edit",
          "\\begin{table}[t]\\centering\\caption{Per task, both models pooled (6 runs per cell; detection uses the runs "
          "whose tests pass the reference). Detection under C0 and C2; "
          "maximum cyclomatic complexity under CN and C2; Ref.-fail: runs whose tests fail on the reference "
          "(all conditions). T07 to T12 are the extension tasks.}"
          "\\label{tab:pertask}", "\\small\\setlength{\\tabcolsep}{4pt}",
          "\\begin{tabular}{@{}lrrrrr@{}}\\toprule",
          "Task & Det.\\ C0 & Det.\\ C2 & CC CN & CC C2 & Ref.-fail\\\\\\midrule"]
    for task in sorted(df["task"].unique()):
        g = df[df.task == task]
        d0 = g[g.condition == "C0"]["detect"].dropna().mean()
        d2 = g[g.condition == "C2"]["detect"].dropna().mean()
        pt.append(f"{task.split('-')[0]} & {fmt(d0, pct=True)} & {fmt(d2, pct=True)} & "
                  f"{g[g.condition == 'CN']['max_cc'].mean():.1f} & {g[g.condition == 'C2']['max_cc'].mean():.1f} & "
                  f"{int((g['tests_reject_ref'] == True).sum())}\\\\")  # noqa: E712
    pt += ["\\bottomrule\\end{tabular}\\end{table}"]
    (OUT / "tab_pertask.tex").write_text("\n".join(pt) + "\n", encoding="utf-8")

    # ---- Table IV: threshold sensitivity on C0/C1 deliveries (offline)
    base = df[df.condition.isin(["C0", "C1"])]
    settings = [(10, 0.80), (20, 0.80), (30, 0.80), (10, 0.70), (10, 0.90)]
    sv = ["% generated by study/analysis/paper_numbers.py -- do not edit",
          "\\begin{table}[t]\\centering\\caption{Threshold sensitivity, computed offline on the stored C0 and C1 "
          "deliveries: share that would pass the full gates (coverage $\\geq$ 90\\%, no Bandit finding) under other "
          "CRAP and mutation thresholds. The first row is the setting used for C2.}\\label{tab:sensitivity}",
          "\\small", "\\begin{tabular}{@{}rrrr@{}}\\toprule",
          "CRAP $<$ & Mutation $\\geq$ & Haiku & Sonnet\\\\\\midrule"]
    for cm, mm in settings:
        vals = [passes(base[base.model == mod], cm, mm).mean() for mod in sorted(df["model"].unique())]
        sv.append(f"{cm} & {int(mm * 100)}\\% & {fmt(vals[0], pct=True)} & {fmt(vals[1], pct=True)}\\\\")
    sv += ["\\bottomrule\\end{tabular}\\end{table}"]
    (OUT / "tab_sensitivity.tex").write_text("\n".join(sv) + "\n", encoding="utf-8")
    sens = {f"{cm}-{int(mm*100)}": [passes(base[base.model == mod], cm, mm).mean() for mod in sorted(df.model.unique())]
            for cm, mm in settings}
    with open(OUT / "numbers.tex", "a", encoding="utf-8") as fh:
        fh.write(macro("sensBaseHaiku", fmt(sens["10-80"][0], pct=True)) + "\n")
        fh.write(macro("sensBaseSonnet", fmt(sens["10-80"][1], pct=True)) + "\n")
        fh.write(macro("sensLooseHaiku", fmt(sens["30-80"][0], pct=True)) + "\n")
        fh.write(macro("sensLooseSonnet", fmt(sens["30-80"][1], pct=True)) + "\n")
        fh.write(macro("sensStrictHaiku", fmt(sens["10-90"][0], pct=True)) + "\n")
        fh.write(macro("sensStrictSonnet", fmt(sens["10-90"][1], pct=True)) + "\n")
    print(summ.round(3).to_string())


if __name__ == "__main__":
    main()

