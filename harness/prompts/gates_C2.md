Before your work is accepted, automated gates check:

- your test suite passes;
- line coverage of `solution.py` by your tests is at least {cov_min_pct};
- every function in `solution.py` has a CRAP score below {crap_max}, where CRAP = CC² × (1 − coverage)³ + CC, CC is the function's cyclomatic complexity and coverage is the fraction of its lines your tests execute;
- the mutation score of your tests is at least {mut_min_pct}: the gate makes small changes to `solution.py` (for example `<` to `<=`, `+` to `-`, `True` to `False`, a constant `n` to `n + 1`, `return x` to `return None`) and your tests must fail for each changed version;
- a static security scan (bandit) reports no medium or high severity issues in `solution.py`.

If a gate fails you will receive the report and must fix it. Comments such as `# nosec` or `# pragma: no cover` are ignored by the gates.
