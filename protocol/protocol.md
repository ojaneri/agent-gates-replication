# Study protocol: automated gates for agent-written code

Version: 2, frozen 2026-11-14 before the main Part A run.
Status: **frozen**. Thresholds: COV_MIN 0.90, CRAP_MAX 10, MUT_MIN 0.80, MAX_ITERS 3. Main run: 6 tasks x 4 conditions x 2 models x 3 repetitions. Every change from here on goes into `deviations.md`. (No Git repository exists yet, so the freeze is recorded by date and by the file hash in `deviations.md`, not by a tag.)

## 0. Thesis and framing

**Central question (2026-11-14):** can AI-generated code be verified, and reach high quality, through tests and automated gates *instead of* line-by-line human review?

The study tests a directional thesis: **automated tests and gates make AI-written code safe to accept at a quality comparable to line-by-line human review, at a fraction of the human time, so the human is not the bottleneck.** "Instead of" is a non-inferiority claim: the gated workflow does not need to beat human review, it needs to be not meaningfully worse on escaped defects while costing much less human time. The study therefore has two parts:

- **Part A, automated (sections 2 to 7):** do gates improve agent code compared with weaker or no gates? No human participants.
- **Part B, human comparison (section 2b):** on the same deliveries, how does test-based verification compare with line-by-line human review, in escaped defects and in human time? Requires ethics approval.

The hypotheses below are stated in that direction. The study is designed so that the thesis can fail: hypotheses, measures and analysis are fixed before the main data exist, and results are reported whatever their direction. A null or negative result is a finding about where gates are not enough, which is what RQ3 is for.

Two consequences for the design:

- **Tasks must be hard enough for unguided agents to fail sometimes.** If every condition passes the oracle (ceiling), the study cannot show that gates help. Task difficulty is calibrated on C0 only, before comparing conditions, so the calibration cannot favor the gates.
- **The human cost must be measured, not assumed** (RQ5).

## 1. Research questions and hypotheses

- **RQ0 (primary, Part B).** Is test-based verification non-inferior to line-by-line human review?
  - H0a (quality, non-inferiority): the escaped-defect rate of deliveries accepted by the gated workflow is not worse than the rate for deliveries accepted after line-by-line human review, by more than a margin Δ fixed in protocol v2 (provisional Δ = 10 percentage points, to be justified from the pilot).
  - H0b (human time, superiority): human minutes per accepted delivery are lower in the gated workflow than in line-by-line review.
  - H0c (secondary): the categories of defects each method misses differ (complementarity), which tells where targeted reading still pays off.
- **RQ1.** Do mutation and CRAP gates reduce escaped defects in agent-written code?
  - H1a: escape rate(C2) < escape rate(C1).
  - H1b: escape rate(C1) < escape rate(C0).
- **RQ2.** Do agents write stronger test suites under the full gates?
  - H2: seeded-fault detection rate(C2) > rate(C1) > rate(C0).
- **RQ3.** Which defect types escape the full gates? (exploratory, qualitative)
- **RQ4.** What do the gates cost? Iterations, wall time, API cost, false rejections.
- **RQ5.** Do gates remove the human from the critical path?
  - H5a: under C2, deliveries reach acceptance with no human intervention at least as often as under C0 (autonomous acceptance rate).
  - H5b: the material a human must read to approve a C2 delivery (spec, gate summary, surviving mutants) is much smaller than the code and tests a line-by-line reviewer would read (reading load, section 4).
  - H5c: the residual defects after C2 concentrate in a small, predictable set of categories (from RQ3), so targeted human reading can be limited to them.

## 2. Units and conditions

The unit is one run: one agent, one task, one condition, one repetition.

| Code | Condition | The agent's delivery must pass |
|---|---|---|
| CN | No tests (added in v2) | Nothing. The agent writes no tests and has no shell; the delivery is accepted as is |
| C0 | No gate | The agent's own tests |
| C1 | Coverage | C0, plus line coverage of `solution.py` >= COV_MIN |
| C2 | Full gates | C1, plus max CRAP per function < CRAP_MAX, mutation score >= MUT_MIN, no bandit finding of medium or high severity |

Provisional thresholds (pilot): COV_MIN = 0.90, CRAP_MAX = 10, MUT_MIN = 0.80.

**Feedback loop.** After the agent finishes, the harness runs the condition's gates. If any gate fails, the agent is resumed in the same session with the gate report. At most MAX_ITERS rounds (pilot: 3; main: 5). A run that never passes is "not delivered" and is analysed separately.

**Information given to the agent.** The prose specification (`spec.md`) and a stub `solution.py` with signatures. Under C1 and C2 the agent is told the gate names and thresholds. The agent never sees the oracle, the reference implementation or the seeded faults: its working directory is a fresh temporary folder outside the study tree.

## 2b. Part B: human comparison study

**Material.** A fixed set of agent deliveries (code plus the agent's tests) produced in Part A under C0, with known ground truth from the hidden oracle. To make sure each task has defective and correct deliveries, defective variants are also built by applying hand-written faults to correct agent deliveries (the classic fault-seeding method of inspection experiments). Each delivery is labelled correct or defective, with the defect list, before any reviewer sees it.

**Verification modes, applied to the same deliveries:**

| Mode | Who decides | What the decider sees |
|---|---|---|
| R-line | Human reviewer | Spec, full code and tests. Reviews line by line and accepts or rejects, listing defects found |
| R-gate | Human reviewer | Spec, gate report (test result, coverage, CRAP, mutation score, surviving mutants, bandit findings). No code. Accepts or rejects |
| G-auto | Gate pipeline alone (C2 thresholds) | Nothing human. Accepts if all gates pass |

R-line is the status quo. G-auto is the fully automated claim. R-gate is the realistic middle: a human approves from the gate report, as in the "move the reading" argument of the companion article.

**Design.** Within-subject: each reviewer works in both human modes on different deliveries, with mode order and delivery assignment counterbalanced (Latin square). Each delivery is seen in each mode by several reviewers. Provisional size: 16 to 24 reviewers, 6 to 8 deliveries each, fixed by a power analysis for H0a before recruitment.

**Measures.** Per decision: accept or reject; defects listed; time from opening to decision; self-reported confidence (1 to 5). Escaped defect = a defective delivery that was accepted. False rejection = a correct delivery that was rejected.

**Participants.** Developers or testers with at least one year of Python experience, recruited voluntarily. No link between participation and any evaluation of the participant. Data are anonymised.

**Ethics.** The protocol is submitted to a Research Ethics Committee ([redacted], via the ethics review system) before recruitment, with an informed consent form (informed consent form). No Part B data are collected before approval.

**Analysis.** H0a: one-sided 95% confidence interval for the difference in escaped-defect rate (gated mode minus R-line), from a mixed-effects logistic model with random effects for reviewer and delivery. Non-inferiority holds if the upper bound is below Δ. H0b: mixed-effects model on log time. H0c: cross-tabulation of missed defect categories by mode.

## 3. Tasks

Each task directory contains:

- `spec.md`: requirements in prose.
- `stub/solution.py`: function signatures and docstrings only.
- `reference/solution.py`: human reference implementation.
- `oracle/test_oracle.py`: hidden tests.
- `faults.json`: hand-written faults, each a single exact text replacement applied to the reference.
- `metadata.json`: traps, CWE identifiers, notes.

**Task validity checks** (script `tasks/validate_tasks.py`), all must pass:

1. The reference passes 100% of the oracle.
2. Each fault's search text occurs exactly once in the reference.
3. Each faulty version fails at least one oracle test.
4. The stub does not contain implementation logic (manual check).

## 4. Measures

- **Escaped defect (RQ1).** The final delivered `solution.py` fails at least one oracle test. Also recorded: oracle pass fraction and which trap tests failed.
- **Seeded-fault detection (RQ2).** The agent's final tests are run against (a) the reference, which they must pass, and (b) each faulty version. Detection rate = faulty versions detected / total faults. If the agent's tests fail on the reference, they encode a wrong expectation. This is recorded as `tests_reject_reference` and the detection rate is not computed for that run.
- **Cost (RQ4).** Agent rounds, wall time, `total_cost_usd` reported by the CLI, turns.
- **False rejection (RQ4).** A round where the code already passed the full oracle but a gate failed.
- **Autonomous acceptance (RQ5).** Delivered within MAX_ITERS rounds with no human input. Reported together with escaped defects, so that "accepted" and "correct" are never conflated.
- **Reading load (RQ5).** Two quantities per run, computed from stored artifacts:
  - *Line-review load:* non-blank lines of the final `solution.py` plus `tests/`, what a reviewer reads in a traditional review.
  - *Gate-review load:* lines of the spec, plus the final gate summary, plus one line per surviving mutant, what a reviewer reads under the gated workflow.
  The ratio is reported per task and condition. Converting lines to minutes needs an external review-rate figure. If used, it must come from a cited source and be reported as an estimate, with a sensitivity range.
- **Human sub-study:** now Part B (section 2b), the primary comparison.
- **Quality, beyond correctness.** "High quality" is reported on four axes: functional correctness (hidden oracle), security (CWE traps and bandit), maintainability (max CRAP, cyclomatic complexity, duplication) and specification conformance (oracle tests grouped by spec rule). In Part B, reviewers in R-line may also report maintainability issues. Those are recorded but not counted as escaped defects.

**Non-circularity.** The gate's mutation operators (`gates/mutate.py`) are generic syntactic operators. The evaluation faults are written by hand from realistic mistakes (boundaries, rounding, rule omissions, security), not generated by the gate's operators. Section 9 lists the overlap check.

## 5. Agent configuration

- Claude Code CLI in print mode, version recorded per run.
- Model fixed by exact ID, recorded per run. Pilot: `claude-sonnet-5-5`.
- Tools allowed: Read, Write, Edit, Glob, Grep, and Bash restricted to running the study's Python interpreter.
- No MCP servers, no project settings (`--strict-mcp-config`, `--setting-sources ""`).
- Prompts are versioned in `harness/prompts/`.

## 6. Sample size

Pilot: 3 tasks x 3 conditions x 1 repetition, plus a C0 rerun to observe variance. The main experiment's repetitions per cell are set from the pilot's variance by a power analysis for H1a (alpha 0.05, power 0.8), recorded in protocol v2.

## 7. Analysis plan

- RQ1: mixed-effects logistic regression, escaped ~ condition + (1 | task); pairwise contrasts with Holm correction. Report rates with Wilson 95% intervals.
- RQ2: detection rate by condition; paired Wilcoxon by task; Cliff's delta.
- RQ3: two raters classify each escaped defect (logic, boundary, spec misreading, security with CWE); Cohen's kappa; disagreements resolved by discussion.
- RQ4: descriptive statistics.
- Sensitivity: alternative thresholds re-evaluated offline on stored code; exclusion of non-delivered runs.

## 8. Exclusions

A run is excluded only for harness failure (crash, CLI error, timeout of the CLI itself), never for its outcome. Excluded runs are logged and rerun with a new repetition number.

## 9. Threats to validity (initial list)

- Internal: prompt wording, model version drift, non-determinism. Mitigation: fixed IDs, repetitions, versioned prompts.
- Construct: our mutation tool differs from industrial tools; equivalent mutants are not filtered; faults may not represent real bugs. Mitigation: cross-check with a second mutation tool before the main study; derive faults from known bug classes.
- Overlap check: for each fault, record whether one gate operator produces the identical change. Report results with and without those faults.
- Proxy validity (added after literature check, 2026-11-14): Zhao, Zhou and Cohen (PACMSE 3, ISSTA 2026, doi 10.1145/3832093) found that coverage and mutation score of LLM-generated tests are informative when the code under test is correct and unreliable when it may be buggy. In our setting the same agent writes code and tests, so the gate's proxies may be weak signals. This is why RQ1 is measured against the hidden oracle, not the proxies. RQ2 applies faults to the bug-free reference, which matches their informative setting. Report `tests_reject_reference` by condition as a measure of tests that confirm wrong behavior (the "misguidance effect", doi 10.1145/3832204).
- External: Python only, small tasks, one or two models.
- Conclusion: small sample in the pilot; the pilot is not used to test hypotheses.
