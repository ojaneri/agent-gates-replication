
import importlib.util, json, random, sqlite3, sys, datetime as dt
from decimal import Decimal as D
from pathlib import Path

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

task, ref_path, sol_path, n, seed = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
REF = load(ref_path, "ref_mod"); SOL = load(sol_path, "sol_mod")
rng = random.Random(seed)

def norm(v):
    if isinstance(v, bool) or v is None or isinstance(v, str): return v
    if isinstance(v, (int, float, D)): return round(float(v), 9)
    if isinstance(v, dict): return {str(k): norm(x) for k, x in sorted(v.items(), key=lambda kv: str(kv[0]))}
    if isinstance(v, (list, tuple)): return [norm(x) for x in v]
    if isinstance(v, (dt.datetime, dt.date)): return v.isoformat()
    return repr(v)

def outcome(fn):
    try:
        return ("ok", norm(fn()))
    except Exception as e:  # compare the family the spec defines
        kind = "ValueError" if isinstance(e, ValueError) else type(e).__name__
        return ("raise", kind, type(e).__name__ if type(e).__name__ in ("CouponError", "UnsafePathError") else "")

def money(lo, hi, places=2):
    q = D(10) ** -places
    return (D(rng.randint(int(lo * 10**places), int(hi * 10**places))) * q).quantize(q)

def case_T01():
    today = dt.date(2026, 11, 14)
    items = [(f"s{i}", money(0, 150, rng.choice([2, 2, 3])), rng.choice([1, 1, 2, 3, 5, 12]) if rng.random() > 0.05 else rng.choice([0, -1]))
             for i in range(rng.randint(0, 4))]
    coupon = None
    if rng.random() < 0.75:
        kind = rng.choice(["percent", "percent", "fixed", "fixed", "bogo"])
        value = money(0, 100, 2) if kind == "percent" else money(0, 80, 2)
        coupon = {"code": rng.choice(["A", "B"]), "kind": kind, "value": value,
                  "min_subtotal": rng.choice([D("0"), money(0, 200, 2)]),
                  "expires": today + dt.timedelta(days=rng.randint(-2, 2))}
    used = set(rng.sample(["A", "B", "C"], rng.randint(0, 2)))
    return lambda M: M.order_total(list(items), dict(coupon) if coupon else None, today, set(used))

def case_T02():
    day = dt.datetime(2026, 11, 16)
    def at(m): return day + dt.timedelta(minutes=m)
    if rng.random() < 0.5:
        ex = []
        for _ in range(rng.randint(0, 4)):
            s = rng.randrange(6 * 60, 20 * 60, 15); ex.append((at(s), at(s + rng.choice([15, 30, 60, 90]))))
        s = rng.randrange(5 * 60, 21 * 60, 15); e = s + rng.choice([-15, 0, 15, 60, 120, 240, 255, 600])
        buf = rng.choice([0, 0, 5, 15, 30, -1])
        return lambda M: M.can_book(list(ex), at(s), at(e), buf)
    iv = []
    for _ in range(rng.randint(0, 6)):
        s = rng.randrange(0, 24 * 60, 30); iv.append((at(s), at(s + rng.choice([0, 30, 60, 120])) if rng.random() < 0.1 else at(s + rng.choice([30, 60, 120]))))
    return lambda M: M.merge_intervals(list(iv))

NAMES = ["Widget", "widget pro", "50% Off", "500 Club", "snake_case", "snake-case", "Bolt", "a\\b", "It's", "ZED", "zed"]
def case_T03():
    rows = [(i + 1, rng.choice(NAMES), rng.choice([1.0, 5.0, 7.5, 10.0, 12.0]), rng.choice([0, 1, 3])) for i in range(rng.randint(0, 9))]
    q = dict(name_contains=rng.choice(["", "w", "W", "%", "_", "50%", "snake_", "\\", "'", "zed", "x"]),
             max_price=rng.choice([None, None, 5.0, 7.5, 10.0]), order_by=rng.choice(["name", "price", "price", "id"]),
             descending=rng.random() < 0.5, limit=rng.choice([1, 2, 3, 20, 100, 0, 101]), offset=rng.choice([0, 0, 1, 2, -1]))
    def call(M):
        c = sqlite3.connect(":memory:")
        c.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, price REAL NOT NULL, stock INTEGER NOT NULL)")
        c.executemany("INSERT INTO products VALUES (?,?,?,?)", rows)
        return M.search_products(c, **q)
    return call

def case_T04():
    cats = ["food", "books", "standard"]
    lines = []
    for i in range(rng.randint(0, 4)):
        l = {"sku": f"s{i}", "category": rng.choice(cats) if rng.random() > 0.03 else "toys",
             "unit_price": money(0, 120, rng.choice([2, 2, 3])), "qty": rng.choice([1, 2, 3, 9, 10, 11, 15])}
        if rng.random() < 0.6: l["discount_pct"] = money(0, 100, rng.choice([0, 1, 2]))
        lines.append(l)
    region = rng.choice(["A", "B", "B", "A", "C"]) if rng.random() > 0.02 else "C"
    credit = rng.choice([D("0"), money(0, 300, 2)])
    return lambda M: M.invoice_totals([dict(x) for x in lines], region, credit)

def case_T05():
    limit = rng.randint(1, 5); window = rng.choice([0.5, 1, 2, 5, 10])
    ops, t = [], 0.0
    for _ in range(rng.randint(1, 25)):
        t += rng.choice([0, 0.25, 0.5, 1, 2])
        ops.append((rng.choice(["allow", "allow", "remaining", "retry"]), rng.choice("ab"), t, rng.randint(1, limit)))
    def call(M):
        r = M.RateLimiter(limit, window); out = []
        for op, c, now, cost in ops:
            if op == "allow": out.append(r.allow(c, now, cost))
            elif op == "remaining": out.append(r.remaining(c, now))
            else: out.append(round(float(r.retry_after(c, now, cost)), 9))
        return out
    return call

SEGS = ["a", "b", "x.txt", "..", ".", "", "A", "..a", "...", ".hidden"]
def case_T06():
    members = []
    for _ in range(rng.randint(0, 4)):
        sep = rng.choice(["/", "/", "\\"]); m = sep.join(rng.choice(SEGS) for _ in range(rng.randint(1, 4)))
        r = rng.random()
        if r < 0.08: m = "/" + m
        elif r < 0.14: m = rng.choice(["C:", "c:", "z:"]) + rng.choice(["/", "\\", ""]) + m
        elif r < 0.18: m = m + "\x00"
        if rng.random() < 0.15: m += sep
        members.append(m)
    dest = rng.choice(["out", "out/", "/", "o/x"])
    return lambda M: M.plan_extraction(dest, list(members))

# Extension tasks (protocol addendum): generators written before any extension delivery was inspected.
PW_CHARS = "aAzZ09-!xyB7 é"
def case_T07():
    n = rng.choice([0, 3, 10, 11, 12, 13, 20, 63, 64, 65])
    pw = "".join(rng.choice(PW_CHARS) for _ in range(n))
    if rng.random() < 0.3 and n > 4:
        k = rng.randrange(n - 3); pw = pw[:k] + pw[k] * 3 + pw[k + 3:]
    user = rng.choice(["", "ab", "abc", "Bob", "alice", "zz9", "x"])
    if rng.random() < 0.3 and user: k = rng.randrange(max(1, n)); pw = pw[:k] + user.upper() + pw[k:]
    block = set(rng.sample([pw.upper(), pw[:5], "password", "letmein"], rng.randint(0, 2)))
    return lambda M: M.check_password(pw, user, set(block))

def semver():
    r = rng.random()
    core = ".".join(rng.choice(["0", "1", "2", "10", "01", ""]) if r < 0.08 else rng.choice(["0", "1", "2", "10"]) for _ in range(3))
    if rng.random() < 0.05: core += rng.choice([".1", " ", "x"])
    if rng.random() < 0.6:
        ids = [rng.choice(["alpha", "beta", "rc", "1", "2", "11", "0", "x-y", "A"]) if rng.random() > 0.05 else rng.choice(["", "07", "a_b"])
               for _ in range(rng.randint(1, 3))]
        core += "-" + ".".join(ids)
    if rng.random() < 0.3:
        core += "+" + ".".join(rng.choice(["001", "b", "exp-sha", ""] if rng.random() < 0.05 else ["001", "b", "exp-sha"]) for _ in range(rng.randint(1, 2)))
    return core
def case_T08():
    a, b = semver(), semver()
    r = rng.random()
    if r < 0.2: b = a.split("+")[0] + rng.choice(["", "+zz"])
    elif r < 0.5:  # same core, related prerelease: the cases where precedence rules decide
        core, _, rest = a.split("+")[0].partition("-")
        pre = rest.split(".") if rest else []
        alt = rng.choice([[], pre + ["1"], pre + ["alpha"], pre[:-1], [rng.choice(["2", "11", "alpha", "beta"])] + pre[1:]])
        b = core + ("-" + ".".join(alt) if alt else "")
    return lambda M: M.compare_versions(a, b)

RLE_CHARS = "aab~1é "
def case_T09():
    if rng.random() < 0.5:
        s = "".join(rng.choice(RLE_CHARS) * rng.choice([1, 1, 2, 3, 4, 5, 9, 10, 12]) for _ in range(rng.randint(0, 6)))
        return lambda M: M.encode(s)
    toks = ["a", "b", "1", "~~", "~4~a", "~10~b", "~5~~", "~12~1", "~3~a", "~04~a", "~", "~x", "~4", "~4~", "~4a"]
    t = "".join(rng.choice(toks) if rng.random() > 0.1 else rng.choice(toks[-6:]) for _ in range(rng.randint(0, 5)))
    return lambda M: M.decode(t)

def case_T10():
    def num():
        v = rng.choice([D("0.5"), D("1"), D("10"), D("30"), D("50"), D("119.9"), D("120"), D("120.1"), D("130")]) if rng.random() > 0.03 else rng.choice([D("0"), D("-1")])
        return rng.choice([v, float(v), int(v) if v == v.to_integral_value() else v])
    w = rng.choice([D("0.1"), D("0.5"), D("1"), D("1.01"), D("1.2"), D("2.5"), D("7.3"), D("20")]) if rng.random() > 0.03 else D("0")
    zone = rng.choice([1, 2, 3]) if rng.random() > 0.03 else rng.choice([0, 4])
    sub = rng.choice([D("0"), D("149.99"), D("150"), D("150.01"), D("500")])
    args = (num(), num(), num(), w, zone, sub)
    return lambda M: str(M.shipping_cost(*args))

BD_HOL = [dt.date(2026, 11, d) for d in (13, 16, 20, 27)] + [dt.date(2026, 12, 25), dt.date(2027, 1, 1), dt.date(2026, 11, 14)]
def case_T11():
    start = dt.date(2026, 11, 1) + dt.timedelta(days=rng.randint(0, 80))
    n = rng.choice([0, 0, 1, 2, 3, 5, 10, -1, -2, -5, -10]) if rng.random() > 0.04 else rng.choice([True, False, 1.0])
    hol = rng.sample(BD_HOL, rng.randint(0, 3))
    return lambda M: M.add_business_days(start, n, list(hol))

CSV_TOK = ["a", "b c", " ", ",", ",", '"x"', '"y,z"', '"q""r"', '""', ";", '"', "\n", '"m\nn"']
def case_T12():
    line = "".join(rng.choice(CSV_TOK) for _ in range(rng.randint(0, 6)))
    sep = rng.choice([",", ",", ",", ";", "\t"]) if rng.random() > 0.05 else rng.choice(["", '"', ";;", "\n"])
    return lambda M: M.parse_line(line, sep)

CASES = {"T01-coupons": case_T01, "T02-booking": case_T02, "T03-product-search": case_T03,
         "T04-invoice": case_T04, "T05-rate-limiter": case_T05, "T06-safe-extract": case_T06,
         "T07-password-policy": case_T07, "T08-semver": case_T08, "T09-rle": case_T09,
         "T10-shipping": case_T10, "T11-business-days": case_T11, "T12-csv-line": case_T12}
gen = CASES[task]; div = []
for i in range(n):
    f = gen(); a, b = outcome(lambda: f(REF)), outcome(lambda: f(SOL))
    if a != b and len(div) < 5: div.append({"i": i, "ref": a, "sol": b})
    elif a != b: div.append({"i": i})
print(json.dumps({"n": n, "divergent": len(div), "examples": [d for d in div if "ref" in d][:5]}, default=str))
