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
    if not isinstance(credit, Decimal) or credit.is_nan() or credit < 0:
        raise ValueError("invalid credit")
    rates = RATES[region]

    with localcontext() as ctx:
        ctx.prec = 60
        net = Decimal("0.00")
        tax = Decimal("0.00")
        by_rate = {}
        for ln in lines:
            cat = ln.get("category")
            if not isinstance(cat, str) or cat not in rates:
                raise ValueError("unknown category")
            qty = ln.get("qty")
            if isinstance(qty, bool) or not isinstance(qty, int) or qty < 1:
                raise ValueError("invalid qty")
            price = ln.get("unit_price")
            if not isinstance(price, Decimal) or price.is_nan() or price < 0:
                raise ValueError("invalid unit_price")
            disc = ln.get("discount_pct", Decimal("0"))
            if disc is None:
                disc = Decimal("0")
            if not isinstance(disc, Decimal) or disc.is_nan() or disc < 0 or disc > 100:
                raise ValueError("invalid discount_pct")

            amount = price * qty * (Decimal(100) - disc) / Decimal(100)
            if cat == "standard" and qty >= 10:
                amount = amount * Decimal(95) / Decimal(100)
            line_net = _q(amount)
            rate = rates[cat]
            line_tax = _q(line_net * rate / Decimal(100))
            net += line_net
            tax += line_tax
            by_rate[rate] = by_rate.get(rate, Decimal("0.00")) + line_tax

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
