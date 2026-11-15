from decimal import Decimal, ROUND_HALF_UP, localcontext

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
    if not isinstance(credit, Decimal) or credit.is_nan() or credit < 0:
        raise ValueError("invalid credit")
    rates = RATES[region]
    net = Decimal("0")
    tax = Decimal("0")
    by_rate = {}
    with localcontext() as ctx:
        ctx.prec = 60
        for ln in lines:
            cat = ln.get("category")
            if cat not in rates:
                raise ValueError("unknown category")
            qty = ln.get("qty")
            if isinstance(qty, bool) or not isinstance(qty, int) or qty < 1:
                raise ValueError("invalid qty")
            price = ln.get("unit_price")
            if price is None or price.is_nan() or price < 0:
                raise ValueError("invalid unit_price")
            disc = ln.get("discount_pct", Decimal("0"))
            if disc is None or disc.is_nan() or disc < 0 or disc > 100:
                raise ValueError("invalid discount_pct")
            amount = price * qty * (Decimal(100) - disc) / Decimal(100)
            if cat == "standard" and qty >= 10:
                amount = amount * Decimal("0.95")
            ln_net = _r(amount)
            rate = rates[cat]
            ln_tax = _r(ln_net * rate / Decimal(100))
            net += ln_net
            tax += ln_tax
            by_rate[rate] = by_rate.get(rate, Decimal("0.00")) + ln_tax
        gross = net + tax
        used = min(credit, gross)
        due = gross - used
        left = credit - used
    return {
        "net": _r(net),
        "tax": _r(tax),
        "gross": _r(gross),
        "credit_used": _r(used),
        "total_due": _r(due),
        "credit_left": _r(left),
        "tax_by_rate": {k: _r(v) for k, v in by_rate.items()},
    }
