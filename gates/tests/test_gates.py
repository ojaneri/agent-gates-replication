"""Known-answer tests for the measurement infrastructure (protocol B2).

Run from the study root:  .venv/Scripts/python -m pytest gates/tests -q
"""
import textwrap
from pathlib import Path

import pytest

from gates.crap import crap, function_metrics
from gates.gate import evaluate, feedback_text
from gates.mutate import find_sites, mutant_source

# ---------- CRAP formula: values computed by hand ----------

@pytest.mark.parametrize("cc,cov,expected", [
    (10, 0.0, 110.0), (10, 0.5, 22.5), (10, 1.0, 10.0),
    (12, 0.0, 156.0), (12, 0.9, 12.144), (1, 0.0, 2.0),
])
def test_crap_known_values(cc, cov, expected):
    assert crap(cc, cov) == pytest.approx(expected, abs=1e-9)


def test_crap_never_below_complexity():
    assert all(crap(cc, c / 10) >= cc for cc in range(1, 20) for c in range(11))


def test_crap_rejects_bad_coverage():
    with pytest.raises(ValueError):
        crap(3, 1.5)


# ---------- cyclomatic complexity: counted by hand ----------

SRC_CC = textwrap.dedent('''\
    def straight(x):
        return x + 1

    def three_ifs(x):
        if x > 0:
            x += 1
        if x > 10:
            x += 1
        if x > 100:
            x += 1
        return x

    def with_and(a, b):
        if a and b:
            return 1
        return 0
    ''')


def test_complexity_counts():
    stm = {i for i, l in enumerate(SRC_CC.splitlines(), 1) if l.strip()}
    m = {f.name: f for f in function_metrics(SRC_CC, executed=stm, statements=stm)}
    assert m["straight"].complexity == 1
    assert m["three_ifs"].complexity == 4
    assert m["with_and"].complexity == 3   # radon counts the boolean operator
    assert all(f.coverage == 1.0 for f in m.values())


def test_per_function_coverage_excludes_def_line():
    stm = {1, 2}
    m = function_metrics("def f(x):\n    return x\n", executed={1}, statements=stm)[0]
    assert m.statements == 1 and m.covered == 0 and m.coverage == 0.0 and m.crap == 2.0


# ---------- mutation operators ----------

def test_sites_and_mutants():
    src = "def adult(age):\n    return age >= 18\n"
    sites = find_sites(src)
    descs = {s.description for s in sites}
    assert descs == {">= -> >", "18 -> 19", "return value -> return None"}
    muts = {s.description: mutant_source(src, s) for s in sites}
    assert "age > 18" in muts[">= -> >"]
    assert "age >= 19" in muts["18 -> 19"]


def test_docstrings_and_module_constants_not_mutated():
    src = 'LIMIT = 5\n\ndef f():\n    """Doc 1."""\n    return LIMIT\n'
    assert [s.description for s in find_sites(src)] == ["return value -> return None"]


# ---------- full gate on tiny projects ----------

SOLUTION = textwrap.dedent('''\
    def adult(age):
        """True when age is 18 or more."""
        if age < 0:
            raise ValueError("negative age")
        return age >= 18
    ''')

STRONG = textwrap.dedent('''\
    import pytest
    from solution import adult

    def test_boundary():
        assert adult(18) is True
        assert adult(17) is False

    def test_negative():
        with pytest.raises(ValueError):
            adult(-1)
        assert adult(0) is False
    ''')

WEAK = textwrap.dedent('''\
    from solution import adult

    def test_runs():
        adult(30)
        adult(5)
        try:
            adult(-1)
        except ValueError:
            pass
    ''')


def _project(tmp_path: Path, solution: str, tests: str) -> str:
    (tmp_path / "solution.py").write_text(solution, encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_solution.py").write_text(tests, encoding="utf-8")
    return str(tmp_path)


def test_strong_suite_passes_all_gates(tmp_path):
    rep = evaluate(_project(tmp_path, SOLUTION, STRONG), "C2", mutation_workers=2)
    assert rep["gates"]["coverage"]["line_coverage"] == 1.0
    assert rep["gates"]["mutation"]["score"] == 1.0, rep["gates"]["mutation"]["survivors"]
    assert rep["passed"], feedback_text(rep)


def test_assertion_free_suite_full_coverage_but_fails_mutation(tmp_path):
    """The night guard: every door visited, no handle tried."""
    rep = evaluate(_project(tmp_path, SOLUTION, WEAK), "C2", mutation_workers=2)
    assert rep["gates"]["coverage"]["passed"] and rep["gates"]["coverage"]["line_coverage"] == 1.0
    assert rep["gates"]["mutation"]["score"] < 0.5
    assert not rep["passed"]
    assert "GATE mutation: FAILED" in feedback_text(rep)
    # C1 would have accepted this suite
    assert evaluate(str(tmp_path), "C1")["passed"]


def test_untested_branchy_function_fails_crap(tmp_path):
    branchy = SOLUTION + textwrap.dedent('''\

        def price(kind, qty):
            if kind == "a":
                return qty * 1
            elif kind == "b":
                return qty * 2
            elif kind == "c":
                return qty * 3
            elif kind == "d":
                return qty * 4
            elif kind == "e":
                return qty * 5
            return 0
        ''')
    rep = evaluate(_project(tmp_path, branchy, STRONG), "C2", mutation_workers=2)
    over = {m["name"] for m in rep["gates"]["crap"]["over_limit"]}
    assert over == {"price"}       # CC 6, coverage 0 -> CRAP 42
    assert not rep["passed"]


def test_sql_injection_is_flagged(tmp_path):
    sql = textwrap.dedent('''\
        def find(conn, name):
            return conn.execute(f"SELECT * FROM users WHERE name = '{name}'").fetchall()
        ''')
    tests = "from solution import find\n\ndef test_x():\n    assert find is not None\n"
    rep = evaluate(_project(tmp_path, sql, tests), "C2", mutation_workers=2)
    assert not rep["gates"]["security"]["passed"]
    assert any(i["test_id"] == "B608" for i in rep["gates"]["security"]["issues"])


def test_nosec_comment_does_not_silence_scanner(tmp_path):
    sql = ('def find(conn, name):\n'
           '    return conn.execute(f"SELECT * FROM users WHERE name = \'{name}\'").fetchall()  # nosec\n')
    tests = "from solution import find\n\ndef test_x():\n    assert find is not None\n"
    rep = evaluate(_project(tmp_path, sql, tests), "C2", mutation_workers=2)
    assert not rep["gates"]["security"]["passed"]


def test_pragma_no_cover_does_not_hide_lines(tmp_path):
    src = ("def f(x):\n    if x:  # pragma: no cover\n        return 1  # pragma: no cover\n    return 0\n")
    tests = "from solution import f\n\ndef test_f():\n    assert f(0) == 0\n"
    rep = evaluate(_project(tmp_path, src, tests), "C1")
    assert rep["gates"]["coverage"]["line_coverage"] < 1.0
    assert 3 in rep["gates"]["coverage"]["missing_lines"]


def test_missing_coverage_data_means_zero_coverage(tmp_path):
    """Regression (post-run check): with no tests, CRAP must be CC^2 + CC, not CC."""
    from gates.gate import run_crap
    (tmp_path / "solution.py").write_text(SOLUTION, encoding="utf-8")
    m = run_crap(str(tmp_path), {"executed": [], "missing": []})[0]
    assert m["complexity"] == 2 and m["coverage"] == 0.0 and m["crap"] == 6.0


def test_failing_suite_fails_tests_gate(tmp_path):
    bad = "from solution import adult\n\ndef test_wrong():\n    assert adult(18) is False\n"
    rep = evaluate(_project(tmp_path, SOLUTION, bad), "C0")
    assert not rep["passed"]
