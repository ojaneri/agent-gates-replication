from decimal import Decimal, ROUND_HALF_UP


_CENT = Decimal("0.01")
_HUNDRED = Decimal("100")

# Tax rates in percent, per region and category.
_TAX_RATES = {
    "A": {"food": 0, "books": 5, "standard": 20},
    "B": {"food": 7, "books": 7, "standard": 15},
}


def _cents(value: Decimal) -> Decimal:
    """Round to 2 decimal places, halves rounded up."""
    return value.quantize(_CENT, rounding=ROUND_HALF_UP)


def invoice_totals(lines: list[dict], region: str, credit: Decimal = Decimal("0")) -> dict:
    """Return the invoice totals. See spec.md."""
    if region not in _TAX_RATES:
        raise ValueError(f"unknown region: {region!r}")
    rates = _TAX_RATES[region]

    if credit < 0:
        raise ValueError("credit must not be negative")

    net_total = Decimal("0")
    tax_total = Decimal("0")
    tax_by_rate: dict[int, Decimal] = {}

    for line in lines:
        category = line["category"]
        if category not in rates:
            raise ValueError(f"unknown category: {category!r}")

        qty = line["qty"]
        if isinstance(qty, bool) or not isinstance(qty, int) or qty < 1:
            raise ValueError("qty must be an integer of at least 1")

        unit_price = line["unit_price"]
        if unit_price < 0:
            raise ValueError("unit_price must not be negative")

        discount_pct = line.get("discount_pct", Decimal("0"))
        if discount_pct < 0 or discount_pct > _HUNDRED:
            raise ValueError("discount_pct must be between 0 and 100")

        # Line net: gross amount reduced by the line's own discount.
        net = unit_price * qty * (_HUNDRED - discount_pct) / _HUNDRED
        # Extra 5% bulk discount on standard lines with qty >= 10, multiplicative.
        if category == "standard" and qty >= 10:
            net = net * Decimal("95") / _HUNDRED
        net = _cents(net)

        rate = rates[category]
        tax = _cents(net * rate / _HUNDRED)

        net_total += net
        tax_total += tax
        tax_by_rate[rate] = tax_by_rate.get(rate, Decimal("0")) + tax

    net_total = _cents(net_total)
    tax_total = _cents(tax_total)
    gross = _cents(net_total + tax_total)

    credit_used = _cents(min(credit, gross))
    total_due = _cents(gross - credit_used)
    credit_left = _cents(credit - credit_used)

    return {
        "net": net_total,
        "tax": tax_total,
        "gross": gross,
        "credit_used": credit_used,
        "total_due": total_due,
        "credit_left": credit_left,
        "tax_by_rate": {rate: _cents(value) for rate, value in tax_by_rate.items()},
    }
