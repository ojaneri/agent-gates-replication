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
    for ln in lines:
        cat = ln["category"]
        if cat not in table:
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
        amount = price * qty * (Decimal(100) - disc) / Decimal(100)
        if cat == "standard" and qty >= 10:
            amount = amount * Decimal("0.95")
        line_net = _r(amount)
        rate = table[cat]
        line_tax = _r(line_net * rate / Decimal(100))
        net += line_net
        tax += line_tax
        by_rate[rate] = by_rate.get(rate, Decimal("0")) + line_tax
    net = _r(net)
    tax = _r(tax)
    gross = net + tax
    credit_used = min(credit, gross)
    return {
        "net": net,
        "tax": tax,
        "gross": gross,
        "credit_used": _r(credit_used),
        "total_due": _r(gross - credit_used),
        "credit_left": _r(credit - credit_used),
        "tax_by_rate": {k: _r(v) for k, v in by_rate.items()},
    }
