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
    if credit < 0:
        raise ValueError("negative credit")
    rates = RATES[region]
    with localcontext() as ctx:
        ctx.prec = 100
        net = Decimal("0")
        tax = Decimal("0")
        by_rate = {}
        for ln in lines:
            cat = ln["category"]
            if cat not in rates:
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
            v = price * qty * (Decimal(100) - disc) / Decimal(100)
            if cat == "standard" and qty >= 10:
                v = v * Decimal(95) / Decimal(100)
            ln_net = _r(v)
            rate = rates[cat]
            ln_tax = _r(ln_net * rate / Decimal(100))
            net += ln_net
            tax += ln_tax
            by_rate[rate] = by_rate.get(rate, Decimal("0")) + ln_tax
        gross = net + tax
        used = min(credit, gross)
        return {
            "net": _r(net),
            "tax": _r(tax),
            "gross": _r(gross),
            "credit_used": _r(used),
            "total_due": _r(gross - used),
            "credit_left": _r(credit - used),
            "tax_by_rate": {k: _r(x) for k, x in by_rate.items()},
        }
