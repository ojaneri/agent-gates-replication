"""Small AST-based mutation testing engine used as a *gate*.

Operators are generic and syntactic. They are deliberately different from the
hand-written evaluation faults in tasks/*/faults.json (see protocol, section 4).

Only code inside function bodies is mutated. A mutant is killed when the test
command exits non-zero or times out. Score = killed / (killed + survived).
Equivalent mutants are not filtered (threat to validity, protocol section 9).
"""
from __future__ import annotations

import ast
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, asdict

CMP_SWAP = {
    ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt,
    ast.Eq: ast.NotEq, ast.NotEq: ast.Eq, ast.In: ast.NotIn, ast.NotIn: ast.In,
    ast.Is: ast.IsNot, ast.IsNot: ast.Is,
}
BIN_SWAP = {
    ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.Div, ast.Div: ast.Mult,
    ast.FloorDiv: ast.Div, ast.Mod: ast.FloorDiv,
}
OP_TXT = {
    ast.Lt: "<", ast.LtE: "<=", ast.Gt: ">", ast.GtE: ">=", ast.Eq: "==", ast.NotEq: "!=",
    ast.In: "in", ast.NotIn: "not in", ast.Is: "is", ast.IsNot: "is not",
    ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/", ast.FloorDiv: "//", ast.Mod: "%",
    ast.And: "and", ast.Or: "or",
}


@dataclass
class Site:
    index: int        # position in ast.walk order
    variant: int      # e.g. which comparator in a chained comparison
    lineno: int
    description: str

    def as_dict(self) -> dict:
        return asdict(self)


def _function_node_ids(tree: ast.AST) -> set[int]:
    ids = set()
    for fn in ast.walk(tree):
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            body = fn.body
            # skip docstring
            if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) \
                    and isinstance(body[0].value.value, str):
                body = body[1:]
            for stmt in body:
                for n in ast.walk(stmt):
                    ids.add(id(n))
    return ids


def find_sites(source: str) -> list[Site]:
    tree = ast.parse(source)
    inside = _function_node_ids(tree)
    sites: list[Site] = []
    for i, n in enumerate(ast.walk(tree)):
        if id(n) not in inside:
            continue
        ln = getattr(n, "lineno", 0)
        if isinstance(n, ast.Compare):
            for k, op in enumerate(n.ops):
                if type(op) in CMP_SWAP:
                    sites.append(Site(i, k, ln, f"{OP_TXT[type(op)]} -> {OP_TXT[CMP_SWAP[type(op)]]}"))
        elif isinstance(n, (ast.BinOp, ast.AugAssign)) and type(n.op) in BIN_SWAP:
            sites.append(Site(i, 0, ln, f"{OP_TXT[type(n.op)]} -> {OP_TXT[BIN_SWAP[type(n.op)]]}"))
        elif isinstance(n, ast.BoolOp):
            other = "or" if isinstance(n.op, ast.And) else "and"
            sites.append(Site(i, 0, ln, f"{OP_TXT[type(n.op)]} -> {other}"))
        elif isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.Not):
            sites.append(Site(i, 0, ln, "remove 'not'"))
        elif isinstance(n, ast.Constant):
            v = n.value
            if isinstance(v, bool):
                sites.append(Site(i, 0, ln, f"{v} -> {not v}"))
            elif isinstance(v, (int, float)):
                sites.append(Site(i, 0, ln, f"{v!r} -> {v + 1!r}"))
        elif isinstance(n, ast.Return) and n.value is not None and not (
                isinstance(n.value, ast.Constant) and n.value.value is None):
            sites.append(Site(i, 0, ln, "return value -> return None"))
    return sites


class _Apply(ast.NodeTransformer):
    def __init__(self, target_index: int, variant: int):
        self.target = target_index
        self.variant = variant

    def run(self, tree: ast.AST) -> ast.AST:
        nodes = list(ast.walk(tree))
        n = nodes[self.target]
        if isinstance(n, ast.Compare):
            n.ops[self.variant] = CMP_SWAP[type(n.ops[self.variant])]()
        elif isinstance(n, (ast.BinOp, ast.AugAssign)):
            n.op = BIN_SWAP[type(n.op)]()
        elif isinstance(n, ast.BoolOp):
            n.op = ast.Or() if isinstance(n.op, ast.And) else ast.And()
        elif isinstance(n, ast.UnaryOp):
            # replace `not x` by `x`, in its parent
            for parent in nodes:
                for field, value in ast.iter_fields(parent):
                    if value is n:
                        setattr(parent, field, n.operand)
                        return tree
                    if isinstance(value, list):
                        for j, item in enumerate(value):
                            if item is n:
                                value[j] = n.operand
                                return tree
        elif isinstance(n, ast.Constant):
            n.value = (not n.value) if isinstance(n.value, bool) else n.value + 1
        elif isinstance(n, ast.Return):
            n.value = ast.Constant(None)
        return tree


def mutant_source(source: str, site: Site) -> str:
    tree = ast.parse(source)
    tree = _Apply(site.index, site.variant).run(tree)
    ast.fix_missing_locations(tree)
    return ast.unparse(tree)


def _run_tests(workdir: str, test_cmd: list[str], timeout: float) -> str:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    try:
        r = subprocess.run(test_cmd, cwd=workdir, capture_output=True, timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        return "timeout"
    return "passed" if r.returncode == 0 else "failed"


def _clean_pycache(d: str) -> None:
    for root, dirs, _ in os.walk(d):
        for x in list(dirs):
            if x == "__pycache__":
                shutil.rmtree(os.path.join(root, x), ignore_errors=True)


def default_test_cmd(python: str = sys.executable) -> list[str]:
    return [python, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", "tests"]


def run_mutation(workdir: str, target: str = "solution.py", test_cmd: list[str] | None = None,
                 timeout: float = 20.0, workers: int = 4) -> dict:
    test_cmd = test_cmd or default_test_cmd()
    src_path = os.path.join(workdir, target)
    with open(src_path, encoding="utf-8") as f:
        source = f.read()
    baseline = _run_tests(workdir, test_cmd, timeout * 3)
    if baseline != "passed":
        return {"baseline": baseline, "score": None, "total": 0, "killed": 0, "survived": 0, "survivors": []}
    sites = find_sites(source)
    lines = source.splitlines()

    copies = []
    for _ in range(max(1, min(workers, len(sites) or 1))):
        d = tempfile.mkdtemp(prefix="mut_")
        shutil.copytree(workdir, d, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", ".coverage*"))
        copies.append(d)

    # Each worker owns one copy; run mutants assigned to it sequentially.
    buckets = [[] for _ in copies]
    for k, s in enumerate(sites):
        buckets[k % len(copies)].append(s)

    def run_bucket(bi):
        d = copies[bi]
        res = []
        for site in buckets[bi]:
            with open(os.path.join(d, target), "w", encoding="utf-8") as f:
                f.write(mutant_source(source, site))
            _clean_pycache(d)
            res.append((site, _run_tests(d, test_cmd, timeout)))
        return res

    results = []
    with ThreadPoolExecutor(max_workers=len(copies)) as ex:
        for r in ex.map(run_bucket, range(len(copies))):
            results.extend(r)
    for d in copies:
        shutil.rmtree(d, ignore_errors=True)

    survivors = []
    killed = 0
    for site, outcome in results:
        if outcome == "passed":
            code = lines[site.lineno - 1].strip() if 0 < site.lineno <= len(lines) else ""
            survivors.append({**site.as_dict(), "code": code})
        else:
            killed += 1
    survivors.sort(key=lambda s: (s["lineno"], s["index"], s["variant"]))
    total = len(results)
    return {"baseline": baseline, "total": total, "killed": killed, "survived": len(survivors),
            "score": round(killed / total, 4) if total else 1.0, "survivors": survivors}
