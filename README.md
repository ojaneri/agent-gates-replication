# Study: automated gates for agent-written code

Empirical study for the paper. Protocol: `protocol/protocol.md` (pre-specified and hash-frozen; not deposited in an external registry).

## Layout

| Path | What it is |
|---|---|
| `protocol/` | Pre-specified protocol (`protocol.md`, hash-frozen) and deviations log |
| `gates/` | Gate pipeline: tests, coverage, CRAP, mutation, bandit. `gates/tests/` holds the known-answer tests |
| `tasks/` | Task corpus. Each task has spec, stub, reference, hidden oracle, hand-written faults, metadata |
| `tasks/validate_tasks.py` | Task validity checks and fault/mutant overlap check |
| `harness/` | Agent runner (`run.py`), pilot matrix (`pilot.py`), versioned prompts |
| `data/raw/` | One folder per run (288: main run T01-T06 and extension T07-T12): prompts, CLI output, gate reports, code per round, evaluation |
| `data/pilot_v2/` | Pilot runs (not used in the analysis; counts reported in the paper) |
| `data/processed/` | CSVs derived from `data/raw/` by the analysis scripts |
| `PACKAGE_HASHES.md` | SHA-256 of the redacted protocol files as shipped |
| `analysis/` | Summary scripts and reports |

## Reproduce

Requires Python 3.12. Re-running agents (steps 3 and 4) also needs the Claude Code CLI, logged in, and
costs money; every other step works offline on the stored data. Commands use the Windows layout
(`.venv/Scripts/python`); on Linux or macOS use `.venv/bin/python`.

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.lock.txt
.venv/Scripts/python -m pytest gates/tests -q          # 1. measurement infrastructure (20 tests)
.venv/Scripts/python -m tasks.validate_tasks           # 2. task validity, all 12 tasks (writes tasks/validation_report.json)
.venv/Scripts/python -m harness.run --task T01-coupons --condition C2 --rep 1   # 3. one run (paid)
.venv/Scripts/python -m harness.pilot --model claude-sonnet-5-5 --tasks T01-coupons --conditions CN C0 C1 C2 --reps 3   # 4. a matrix (paid)
```

### Reproduce the paper's numbers from the stored data

`data/processed/` is already current; run these to regenerate it, in this order. `gate_timing` re-measures wall-clock time, so its CSV and the gate-time macros vary by machine and run; everything else reproduces exactly. `data/processed/runs.csv` (from `analysis.summarize`) keeps the original line-review load without the specification; the paper's reading-load figures add the specification on both sides and come from `paper_numbers`.

```bash
.venv/Scripts/python -m analysis.differential                # data/processed/differential.csv (slow)
.venv/Scripts/python -m analysis.differential_sensitivity    # data/processed/differential_sensitivity.csv
.venv/Scripts/python -m analysis.detection_repaired          # data/processed/detection_repaired.csv
.venv/Scripts/python -m analysis.gate_timing                 # data/processed/gate_timing.csv
.venv/Scripts/python -m analysis.paper_numbers               # every number and table in the paper
```

`analysis.paper_numbers` reads `data/raw/*/meta.json`, `tasks/validation_report.json`,
`analysis/reject_reference_classification.csv` and the CSVs above, writes `data/processed/main_runs.csv`
and `condition_summary.csv`, and writes the LaTeX macros and tables to `../paper/generated/`
(`numbers.tex`, `tab_tasks.tex`, `tab_results.tex`, `tab_pertask.tex`, `tab_sensitivity.tex`); create that
folder next to this one, or edit `OUT` at the top of the script. Each macro in the paper is defined
there with the computation beside it. `analysis.reevaluate --task T05-rate-limiter` (and T08, T10)
re-applies the corrected oracles. The Cosmic Ray cross-check (`analysis.mutation_crosscheck`) needs
`pip install cosmic-ray==8.4.1`; its outputs are shipped as `data/processed/mutation_crosscheck*.csv`.
## Notes

- The gate uses its own AST mutation engine (`gates/mutate.py`), validated by known-answer tests and cross-checked against Cosmic Ray (`analysis/mutation_crosscheck.py`).
- Protocol hashes: `protocol/deviations.md` records the SHA-256 of the unredacted `protocol.md` and `addendum-extension.md`, computed before the runs. Both files are redacted in this copy, so their hashes differ; `PACKAGE_HASHES.md` gives the hashes as shipped, and the unredacted files can be provided to the programme chairs.
- Times in `meta.json` are local; transcript timestamps were removed from this copy.
- Evaluation keys in `meta.json`: `evaluation` is the current oracle for every run. For the 24 T05 runs, `evaluation_original` is the frozen oracle and `evaluation_int_inputs` the integer-input variant of the return-type check (`evaluation_previous` there equals the integer-input variant). For the 48 T08 and T10 runs, `evaluation_original` is the frozen oracle (before the trailing-newline and NaN tests). For the other main-run runs, `evaluation_previous` is the frozen-oracle evaluation; the other extension runs have only `evaluation`.
- Anti-gaming: the gate ignores `# nosec` and `# pragma: no cover`.
- The agent runs in a temporary folder outside this tree, with only Read, Write, Edit, Glob, Grep and `python -m pytest` allowed, no MCP servers and no skills. The `init` records in the transcripts list every tool the CLI registers; the permission mode (`dontAsk` with an allow-list) denies all others, which is why denied tool calls appear in the transcripts.
- Random seeds: run order 20261114 (main) and 20261115 (extension); all bootstraps and permutation tests in `analysis/paper_numbers.py` use `numpy.random.default_rng(20261114)` with 10,000 resamples; two-sided permutation p values are twice the one-sided ones.
