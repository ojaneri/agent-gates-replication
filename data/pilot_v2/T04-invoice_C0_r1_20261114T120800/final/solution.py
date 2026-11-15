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
    if not isinstance(region, str) or region not in RATES:
        raise ValueError("unknown region")
    if not isinstance(credit, Decimal) or credit < 0:
        raise ValueError("invalid credit")
    table = RATES[region]
    with localcontext() as ctx:
        ctx.prec = 60
        net = Decimal("0")
        tax = Decimal("0")
        by_rate = {}
        for line in lines:
            cat = line.get("category")
            if not isinstance(cat, str) or cat not in table:
                raise ValueError("unknown category")
            qty = line.get("qty")
            if isinstance(qty, bool) or not isinstance(qty, int) or qty < 1:
                raise ValueError("invalid qty")
            price = line.get("unit_price")
            if not isinstance(price, Decimal) or price < 0:
                raise ValueError("invalid unit_price")
            disc = line.get("discount_pct", Decimal("0"))
            if not isinstance(disc, Decimal) or not (0 <= disc <= 100):
                raise ValueError("invalid discount_pct")
            n = price * qty * (Decimal(100) - disc) / Decimal(100)
            if cat == "standard" and qty >= 10:
                n = n * Decimal("0.95")
            n = _q(n)
            rate = table[cat]
            t = _q(n * rate / Decimal(100))
            net += n
            tax += t
            by_rate[rate] = by_rate.get(rate, Decimal("0")) + t
        gross = net + tax
        used = min(credit, gross)
        return {
            "net": _q(net),
            "tax": _q(tax),
            "gross": _q(gross),
            "credit_used": _q(used),
            "total_due": _q(gross - used),
            "credit_left": _q(credit - used),
            "tax_by_rate": {r: _q(v) for r, v in by_rate.items()},
        }
