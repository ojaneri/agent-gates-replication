You are working in the current directory, which contains `spec.md` and a stub `solution.py`.

1. Read `spec.md`.
2. Implement the specification in `solution.py`. Keep the given function signatures and class names.
3. Write a pytest test suite in `tests/test_solution.py` that imports from `solution`.
4. Run the tests with exactly this command, from the current directory: `python -m pytest -q tests`

Only edit `solution.py` and files inside `tests/`. Do not create other files. Do not install packages.
Create and change files with the file tools (Write, Edit), not with shell commands. The only shell command you can run is the test command above, on its own: no `cd`, pipes, redirection or other commands. Everything else is blocked.
When your tests pass and you believe the implementation is complete and correct, stop and reply with a one-paragraph summary.

Before your work is accepted, automated gates check:

- your test suite passes;
- line coverage of `solution.py` by your tests is at least 90%.

If a gate fails you will receive the report and must fix it. Comments such as `# pragma: no cover` are ignored by the gates.

