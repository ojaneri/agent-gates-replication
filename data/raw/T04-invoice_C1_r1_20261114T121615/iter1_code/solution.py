from decimal import Decimal, ROUND_HALF_UP

RATES = {
    "A": {"food": 0, "books": 5, "standard": 20},
    "B": {"food": 7, "books": 7, "standard": 15},
}
CENT = Decimal("0.01")


def _r(x: Decimal) -> Decimal:
    return x.quantize(CENT, rounding=ROUND_HALF_UP)


def invoice_totals(lines: list[dict], region: str, credit: Decimal = Decimal("0")) -> dict:
    """Return the invoice totals. See spec.md."""
    if region not in RATES:
        raise ValueError("unknown region")
    if credit < 0:
        raise ValueError("negative credit")
    table = RATES[region]
    net = Decimal("0")
    tax = Decimal("0")
    by_rate = {}
    for line in lines:
        cat = line["category"]
        if cat not in table:
            raise ValueError("unknown category")
        qty = line["qty"]
        if isinstance(qty, bool) or not isinstance(qty, int) or qty < 1:
            raise ValueError("bad qty")
        price = line["unit_price"]
        if price < 0:
            raise ValueError("negative price")
        disc = line.get("discount_pct", Decimal("0"))
        if disc < 0 or disc > 100:
            raise ValueError("bad discount")
        n = price * qty * (Decimal(100) - disc) / Decimal(100)
        if cat == "standard" and qty >= 10:
            n = n * Decimal("0.95")
        n = _r(n)
        rate = table[cat]
        t = _r(n * rate / Decimal(100))
        net += n
        tax += t
        by_rate[rate] = by_rate.get(rate, Decimal("0")) + t
    net = _r(net)
    tax = _r(tax)
    gross = net + tax
    used = min(credit, gross)
    return {
        "net": net,
        "tax": tax,
        "gross": gross,
        "credit_used": _r(used),
        "total_due": _r(gross - used),
        "credit_left": _r(credit - used),
        "tax_by_rate": {k: _r(v) for k, v in by_rate.items()},
    }
