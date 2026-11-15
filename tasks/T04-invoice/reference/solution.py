from decimal import Decimal, ROUND_HALF_UP

RATES = {"A": {"food": 0, "books": 5, "standard": 20},
         "B": {"food": 7, "books": 7, "standard": 15}}
BULK_QTY = 10
BULK_PCT = Decimal("5")
CENT = Decimal("0.01")


def _cents(x: Decimal) -> Decimal:
    return x.quantize(CENT, rounding=ROUND_HALF_UP)


def _validate(line: dict):
    qty = line["qty"]
    price = line["unit_price"]
    disc = line.get("discount_pct", Decimal("0"))
    if not isinstance(qty, int) or isinstance(qty, bool) or qty < 1:
        raise ValueError("qty must be an integer >= 1")
    if price < 0:
        raise ValueError("unit_price must be >= 0")
    if not (0 <= disc <= 100):
        raise ValueError("discount_pct must be within 0..100")
    return qty, price, disc


def _line(line: dict, rates: dict):
    qty, price, disc = _validate(line)
    cat = line["category"]
    if cat not in rates:
        raise ValueError("unknown category")
    factor = 1 - disc / 100
    if cat == "standard" and qty >= BULK_QTY:
        factor = factor * (1 - BULK_PCT / 100)
    raw = price * qty * factor
    net = _cents(raw)
    rate = rates[cat]
    tax = _cents(net * rate / 100)
    return raw, net, tax, rate


def invoice_totals(lines: list[dict], region: str, credit: Decimal = Decimal("0")) -> dict:
    if region not in RATES:
        raise ValueError("unknown region")
    if credit < 0:
        raise ValueError("credit must be >= 0")
    rates = RATES[region]
    total_net = Decimal("0")
    total_tax = Decimal("0")
    by_rate: dict = {}
    for line in lines:
        raw, net, tax, rate = _line(line, rates)
        total_net += net
        total_tax += tax
        by_rate[rate] = by_rate.get(rate, Decimal("0")) + tax
    gross = total_net + total_tax
    used = min(credit, gross)
    return {"net": _cents(total_net), "tax": _cents(total_tax), "gross": _cents(gross),
            "credit_used": _cents(used), "total_due": _cents(gross - used),
            "credit_left": _cents(credit - used),
            "tax_by_rate": {r: _cents(v) for r, v in sorted(by_rate.items())}}
