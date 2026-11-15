# Protocol addendum: Part A extension (T07 to T12)

Written and frozen on 2026-11-14 **before** any extension run. The SHA-256 of this file is recorded in deviations.md.

## Why

(post-run check) was fixed without a power or precision analysis. With 0 escapes in 144 runs, the main lever on precision is more independent tasks, not more repetitions of the same tasks. This addendum adds six tasks and runs them under the frozen protocol v2, unchanged.

## What is added

Six tasks, drafted by the AI assistant like T01 to T06 and validated by `tasks/validate_tasks.py` before any run (reference passes the oracle and the security gate, every hand-written fault applies once and is detected, oracle kills 100% of the engine's mutants):

| Task | Domain | Hand-written faults |
|---|---|---|
| T07-password-policy | validation rules (CWE-521) | 7 |
| T08-semver | parsing and ordering | 7 |
| T09-rle | encoding with escapes | 7 |
| T10-shipping | decimal pricing | 7 |
| T11-business-days | calendar arithmetic | 7 |
| T12-csv-line | parsing | 7 |

During validation the oracles of T07, T09, T10 and T12 were strengthened and the references of T09, T11 and T12 were restructured to remove equivalent mutants. All of this happened before any agent saw the tasks.

## What is unchanged

Conditions CN, C0, C1, C2; thresholds (90% line coverage; CRAP < 10; mutation score >= 80%; no Bandit medium/high); feedback loop of at most 3 rounds; prompts; agent version, tools and permissions; models `claude-haiku-5-5` and `claude-sonnet-5-5`; 3 repetitions per cell; budget per call USD 1.50; primary outcome (escaped defect against the hidden oracle) and secondary outcomes (seeded-fault detection, reference-failing suites, gate decisions); evaluation code.

## Design

6 tasks x 4 conditions x 2 models x 3 repetitions = **144 runs**. Run order randomised with seed 20261115 within each model; one process per model, concurrent. Cost cap: USD 16 total across all raw runs (main run spent USD 5.77).

## Analysis

1. The extension is reported **separately** (T07 to T12) and **pooled** with the main run (T01 to T12, 288 runs). No result from the main run is replaced.
2. Same estimators as the main run: Wilson intervals for escapes per condition; RQ2 task-balanced differences with run-level, task-stratified and task-cluster bootstraps and a sign test over tasks; Fisher's exact test for C0 vs C2 counts.
3. Differential testing (400 in-domain inputs per delivery) is extended with generators for T07 to T12, written before inspecting any extension delivery's code.
4. A delivery that the harness marks as a harness error is re-run once; otherwise no run is excluded.

## Stopping rule

The extension runs once. No further tasks are added in response to its results.
