"""Cyclomatic complexity, per-function line coverage and CRAP score.

CRAP = CC^2 * (1 - cov)^3 + CC   (Savoia and Evans, 2007)
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from radon.complexity import cc_visit


def crap(cc: int, cov: float) -> float:
    if not 0.0 <= cov <= 1.0:
        raise ValueError("coverage must be a fraction between 0 and 1")
    return cc ** 2 * (1.0 - cov) ** 3 + cc


@dataclass
class FunctionMetric:
    name: str
    lineno: int
    endline: int
    complexity: int
    statements: int
    covered: int
    coverage: float
    crap: float

    def as_dict(self) -> dict:
        return asdict(self)


def _blocks(source: str):
    for block in cc_visit(source):
        methods = getattr(block, "methods", None)
        if methods is not None:  # class: report its methods, not the class itself
            for m in methods:
                yield f"{block.name}.{m.name}", m
        else:
            yield block.name, block


def function_metrics(source: str, executed: set[int], statements: set[int]) -> list[FunctionMetric]:
    """Per-function metrics. `executed` and `statements` are line numbers from coverage.py.

    The `def` line is excluded because it always runs at import time.
    """
    out = []
    for name, b in _blocks(source):
        body = {l for l in statements if b.lineno < l <= b.endline}
        hit = body & executed
        cov = len(hit) / len(body) if body else 1.0
        out.append(FunctionMetric(name, b.lineno, b.endline, b.complexity,
                                  len(body), len(hit), round(cov, 4), round(crap(b.complexity, cov), 3)))
    return out
