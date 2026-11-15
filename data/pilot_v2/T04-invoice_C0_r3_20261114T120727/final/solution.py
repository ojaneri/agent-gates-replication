from decimal import Decimal, ROUND_HALF_UP

RATES = {
    "A": {"food": 0, "books": 5, "standard": 20},
    "B": {"food": 7, "books": 7, "standard": 15},
}
CENT = Decimal("0.01")


def _q(x: Decimal) -> Decimal:
    return x.quantize(CENT, rounding=ROUND_HALF_UP)


def invoice_totals(lines: list[dict], region: str, credit: Decimal = Decimal("0")) -> dict:
    """Return the invoice totals. See spec.md."""
    if region not in RATES:
        raise ValueError("unknown region")
    if credit < 0:
        raise ValueError("negative credit")
    net = Decimal("0")
    tax = Decimal("0")
    by_rate = {}
    for ln in lines:
        cat = ln["category"]
        if cat not in RATES[region]:
            raise ValueError("unknown category")
        qty = ln["qty"]
        if isinstance(qty, bool) or not isinstance(qty, int) or qty < 1:
            raise ValueError("bad qty")
        price = ln["unit_price"]
        if price < 0:
            raise ValueError("negative price")
        disc = ln.get("discount_pct", Decimal("0"))
        if disc < 0 or disc > 100:
            raise ValueError("bad discount")
        amt = price * qty * (Decimal(100) - disc) / Decimal(100)
        if cat == "standard" and qty >= 10:
            amt = amt * Decimal("0.95")
        line_net = _q(amt)
        rate = RATES[region][cat]
        line_tax = _q(line_net * rate / Decimal(100))
        net += line_net
        tax += line_tax
        by_rate[rate] = by_rate.get(rate, Decimal("0")) + line_tax
    gross = net + tax
    used = min(credit, gross)
    return {
        "net": _q(net),
        "tax": _q(tax),
        "gross": _q(gross),
        "credit_used": _q(used),
        "total_due": _q(gross - used),
        "credit_left": _q(credit - used),
        "tax_by_rate": {k: _q(v) for k, v in by_rate.items()},
    }
