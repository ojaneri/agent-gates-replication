# Deviations from the protocol

Each entry: date, what changed, why, and which results it affects.

## After the extension run: analysis additions, 2026-11-14

- **RQ2 unit of analysis.** The addendum named "a sign test over tasks"; the paper's earlier headline sign test pooled task-model pairs. Both are now reported: over tasks (models averaged within task) 4 of 4 non-zero tasks positive, p = 0.125; over pairs (exploratory) 7 of 7, p = 0.016. Added: t intervals over task differences and a within-task label permutation test.
- **Post-treatment exclusion.** Detection is undefined for runs whose tests fail on the reference. Added `analysis/detection_repaired.py` (failing test cases deselected; 27 of 30 runs usable) and worst/best-case imputation bounds.
- **RQ3 without T10** reported per condition (C1 vs C0 and C2 vs C0), uncorrected for multiplicity.
- **Oracle changes after the extension** (fifth correction) depart from the addendum's "evaluation code unchanged"; both evaluations are reported.
## After the extension run: fifth correction, 2026-11-14

- **Two extension references violated rules their specifications state.** Found by inspecting the extension's reference-failing suites (30 runs), before writing any extension result. (1) T08: the version regex ended in `$`, which in Python also matches before a final newline, so `"1.0.0\n"` was accepted; the spec says anything else is invalid. Fixed with `fullmatch`. (2) T10: a NaN input reached the arithmetic and raised `decimal.InvalidOperation`; the spec requires values greater than zero (zero or more for the subtotal) and `ValueError` otherwise, and NaN is neither. Fixed with an explicit NaN check. Oracle tests added for both (`test_trailing_newline_is_invalid`, `test_nan_is_not_positive`); all twelve tasks revalidated (still 100% oracle strength); the 48 T08 and T10 deliveries re-evaluated (`analysis/reevaluate.py`; frozen-oracle evaluation kept as `evaluation_original`).
- **Result:** under the frozen oracle 0 of 288 deliveries fail; under the corrected oracle **1** fails (T08, CN, Haiku: accepts a trailing newline). Both are reported. 11 suites that failed only on the original references (10 on T08, 1 on T10) are classified spec-correct.
- **Not corrected:** infinite inputs and finite values too large for the reference's 28-digit Decimal context (T10). The spec bounds values only by "greater than zero" and says nothing about representability; we treat them as unspecified (RQ3 category `extreme-value`, 13 runs). Also unspecified: TypeError for non-string versions (T08, 2 runs, `input-type`), error-message wording (T09, 1 run, `message`), imports of private helpers (T07 2, T10 1, `private-api`). All classified by the AI assistant; no human rater yet.
- **Differential testing** extended to all 288 deliveries with generators for T07 to T12 written before inspecting any extension delivery: 0 divergent. The generators do not produce trailing newlines, so they could not have caught the T08 escape. Sensitivity: the generators separate 84 of 87 faulty references from the correct one (`analysis/differential_sensitivity.py`).
## Extension addendum frozen, 2026-11-14

- **Part A extension (T07 to T12)** added after a post-run review (number of tasks not justified). Protocol addendum `protocol/addendum-extension.md` frozen before any extension run, SHA-256 0DD9E262E4672F9FA58D4B0CC75D549A8941C8AF16EB72C4E6208980F8997A65. The frozen protocol v2 is otherwise unchanged.

## After the main run: fourth correction, 2026-11-14

- **Sample-size rationale corrected.** The first-correction entry below says "sample fixed by budget". That was wrong: the main run cost USD 5.77 and the tasks were drafted quickly with AI assistance. The number of tasks was fixed without a power or precision analysis and was not limited by cost or effort. The paper states this.
- **RQ3 classification** was done by the AI assistant, not by an author; no human second rater yet.
## After the main run: third correction, 2026-11-14

- **T05 return-type check moved to in-domain inputs.** The type check added in the second correction called `retry_after` with integer times; spec.md says "Times are floats". It was rewritten to use float inputs. Result: **0 of 144 deliveries fail** (was 11 with integer inputs). The integer-input evaluation of the 24 T05 runs is kept in each meta.json as `evaluation_int_inputs` (11 fail: CN 3, C0 2, C1 4, C2 2) and reported as a sensitivity result; the frozen-oracle evaluation is kept as `evaluation_original` (0 fail). The choice between the two versions is a judgment on an ambiguous interface (Python's typing accepts an int where a float is annotated), made on the specification's input type.
- **The first integer-input version of the check was modelled on a test written by one of the agents** (a C2 delivery); disclosed in the paper.
- **RQ2 bootstraps and the sign test** were added after the main run; the planned Wilcoxon test cannot reject at this number of non-zero task pairs.
- **Authorship of the materials:** the six tasks, references, oracles and hand-written faults were drafted by an AI assistant (a Claude model, the same family as the agents under test) under the authors' direction and validated by the scripts in tasks/; disclosed in the paper as a threat to validity.
## After the main run: second correction, 2026-11-14

- **T05 reference violated the specified return type.** `retry_after` returned an int for int inputs, while spec.md and the stub declare `-> float`. The oracle compared with `pytest.approx` and never checked the type. Fixed: the reference returns `float(...)`, fault F05 updated, oracle test `test_retry_after_returns_float` added; all six tasks revalidated (still 100% oracle strength). All 144 deliveries re-evaluated (`analysis/reevaluate.py`; previous evaluation kept as `evaluation_previous` in each meta.json). Result: 11 deliveries now fail, all on T05 and all on that single test (CN 3, C0 2, C1 4, C2 2 of 6 T05 runs per condition). Under the original oracle there were 0. Both evaluations are reported.
- **Two RQ3 cases reclassified as spec-correct:** their tests expected the float return type, which the spec requires; they no longer fail on the corrected reference.
- **Differential testing added** (`analysis/differential.py`): 144 deliveries x 400 in-domain inputs against the reference, values compared numerically; 0 divergent deliveries.
- **Reading load made symmetric:** the line-by-line side now also counts the specification.
- **RQ2 analysis extended** with task-stratified and task-cluster bootstraps and a sign test over tasks; the Wilcoxon test has no power at this number of non-zero pairs.
- **Unreported protocol items now stated in the paper:** RQ rephrasing, autonomous acceptance (144/144), residual-defect concentration untestable, duplication and per-rule conformance not measured, run-order randomisation and per-model concurrency.

## After the main run: first correction, 2026-11-14

- **Correction:** the calibration entry below says "9 Haiku and Sonnet C0 runs"; there were 18 (9 per model). Pilot v2 total is 37: 18 on T01 to T03, 18 calibration C0 runs, 1 CN smoke run.
- **CRAP for CN was stored with coverage 1.** With no tests, `run_coverage` returned empty statement sets and `function_metrics` treated empty as fully covered, so stored `max_crap` for CN equals max CC. Fixed in `gates/gate.py` (no coverage data means coverage 0, regression test added); `analysis/paper_numbers.py` recomputes CN CRAP as CC^2 + CC. No gate decision in the main run was affected (CN has no gates; all C0 to C2 runs had coverage data).
- **Logistic model not estimable** (0 escapes, complete separation). Reported Wilson intervals only.
- **RQ2 inference** as planned (paired Wilcoxon by task, Cliff's delta) plus run-level bootstrap intervals, added after the main run.
- **RQ3 redirected after seeing the data:** with no escaped defects, RQ3 examines runs whose tests fail on the reference. Coded by one rater; the planned second rater and Cohen's kappa were not done.
- **Power analysis not done;** sample fixed by budget.
- **MAX_ITERS:** the protocol body says "main: 5"; the frozen header and the main run used 3. The header is the frozen setting.
- **Part B margin:** Delta stays provisional (10 points) and must be fixed before Part B data collection.
- **Threshold sensitivity** run offline on stored C0/C1 deliveries, as planned.
- **Cosmic Ray cross-check** extended to the first repetition of every main-run cell with tests.
- **Gate compute time** measured offline by re-running the C2 gates on the stored C2 deliveries.

## Freezing (protocol v2), 2026-11-14

- **Hard tasks T04 to T06 added** after pilot v2 showed a ceiling on T01 to T03. All six validated, oracles at 100% mutation strength.
- **Calibration on C0 only:** 9 Haiku and Sonnet C0 runs on T04 to T06 also passed the full oracle. The ceiling persists on the harder tasks.
- **New baseline condition CN (no tests):** the agent implements the module without writing or running tests and without shell access; the delivery is accepted as is. Added because C0 already requires the agent to write and pass its own tests, so the study had no condition that isolates the effect of testing itself. A CN smoke run on T04 with Haiku also passed the full oracle.
- **Main run definition:** 6 tasks x 4 conditions (CN, C0, C1, C2) x 2 models (claude-haiku-5-5, claude-sonnet-5-5) x 3 repetitions = 144 runs. Thresholds unchanged: COV_MIN 0.90, CRAP_MAX 10, MUT_MIN 0.80, MAX_ITERS 3. Pilot v2, calibration and smoke runs are moved to `data/pilot_v2/` and are not used for the analysis.
- **Analysis adjustment forced by the ceiling:** with escape rates near zero, the logistic model of section 7 may not be estimable (separation). Escape rates are then reported with Wilson 95% intervals per condition and model, and comparisons rest on RQ2 (seeded-fault detection), structure (CRAP) and RQ5 (reading load). Sample size is fixed by budget and time, not by a power analysis; this is stated as a limitation.

## Before freezing (pilot phase, allowed by protocol section 1)

- **2026-11-14. Mutation tool.** The plan named mutmut. mutmut does not run natively on Windows, so the gate uses its own AST engine (`gates/mutate.py`). It is validated by known-answer tests (`gates/tests`). It must be cross-checked against a second tool before the main study.
- **2026-11-14. Agent shell commands.** The agent can run only `python -m pytest`, not coverage or other tools. Under C1 and C2 it learns coverage, CRAP and mutation results only from gate feedback. To be reviewed after the pilot.
- **2026-11-14. Anti-gaming.** The gate runs bandit with `--ignore-nosec` and coverage with exclusion pragmas disabled. Agents are told this in the prompt.
- **2026-11-14. Pilot v1 invalidated (harness defect).** In 6 of 10 agent calls of the first pilot, the agent tried to run tests with compound shell commands (`cd ... &&`, heredocs, pipes) or through the PowerShell tool, and the permission rules denied them. Some runs may have been delivered without the agent running its own tests. Fix: allow `python -m pytest` in PowerShell too, tell the agent to use the file tools and run the test command alone, and capture the full stream-json transcript to count test commands and denials per round. The 9 v1 runs were moved to `data/pilot_v1_invalid/` and are not analysed. Pilot v2 reruns all units.
- **2026-11-14. Second model in the pilot.** Added `claude-haiku-5-5` to check for a ceiling effect, since all v1 runs passed the full oracle.
- **2026-11-14. Oracle strength check added; T01 oracle strengthened.** Following the literature review (EvalPlus/UTBoost line of work), `tasks/validate_tasks.py` now reports the mutation score of each hidden oracle against the reference. T01 had 2 survivors (no test with a percent or fixed value between 0 and 1); two tests were added. All three oracles now kill 100% of gate mutants (T01 33/33, T02 35/35, T03 21/21). The change happened while pilot v2 was running, so all v2 runs are re-scored with `analysis/reevaluate.py` before analysis.
- **2026-11-14. Fault/operator overlap.** Computed automatically by `tasks/validate_tasks.py`. In the pilot tasks, 5 of 22 faults are identical to a gate mutant: T01 F01 and F06, T02 F01, F03 and F06.

- **Freeze record:** SHA-256 of protocol.md at freeze: 6EF04A99385B94ECF27528D0929061F3374FB402786D9B736A6F043D262464D6 (2026-11-14).


