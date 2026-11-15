from decimal import Decimal, ROUND_HALF_UP, localcontext

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
    rates = RATES[region]
    net = Decimal("0.00")
    tax = Decimal("0.00")
    by_rate: dict = {}
    with localcontext() as ctx:
        ctx.prec = 60
        for line in lines:
            cat = line["category"]
            if cat not in rates:
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
            amount = price * qty * (Decimal(100) - disc) / Decimal(100)
            if cat == "standard" and qty >= 10:
                amount = amount * Decimal("0.95")
            ln = _q(amount)
            rate = rates[cat]
            lt = _q(ln * rate / Decimal(100))
            net += ln
            tax += lt
            by_rate[rate] = by_rate.get(rate, Decimal("0.00")) + lt
        gross = net + tax
        credit_used = min(credit, gross)
        return {
            "net": _q(net),
            "tax": _q(tax),
            "gross": _q(gross),
            "credit_used": _q(credit_used),
            "total_due": _q(gross - credit_used),
            "credit_left": _q(credit - credit_used),
            "tax_by_rate": {k: _q(v) for k, v in by_rate.items()},
        }
