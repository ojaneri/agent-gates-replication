from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")
HUNDRED = Decimal("100")

TAX_RATES = {
    "A": {"food": 0, "books": 5, "standard": 20},
    "B": {"food": 7, "books": 7, "standard": 15},
}


def _cents(value: Decimal) -> Decimal:
    """Round to 2 decimal places, halves rounded up."""
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _as_decimal(value, name: str) -> Decimal:
    if isinstance(value, bool):
        raise TypeError(f"{name} must be a Decimal")
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    raise TypeError(f"{name} must be a Decimal")


def invoice_totals(lines: list[dict], region: str, credit: Decimal = Decimal("0")) -> dict:
    """Return the invoice totals. See spec.md."""
    if region not in TAX_RATES:
        raise ValueError(f"unknown region: {region!r}")
    rates = TAX_RATES[region]

    credit = _cents(_as_decimal(credit, "credit"))
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

        unit_price = _as_decimal(line["unit_price"], "unit_price")
        if unit_price < 0:
            raise ValueError("unit_price must not be negative")

        discount_pct = _as_decimal(line.get("discount_pct", Decimal("0")), "discount_pct")
        if discount_pct < 0 or discount_pct > HUNDRED:
            raise ValueError("discount_pct must be between 0 and 100")

        net = unit_price * qty
        net = net * (HUNDRED - discount_pct) / HUNDRED
        if category == "standard" and qty >= 10:
            net = net * (HUNDRED - Decimal("5")) / HUNDRED
        net = _cents(net)

        rate = rates[category]
        tax = _cents(net * Decimal(rate) / HUNDRED)

        net_total += net
        tax_total += tax
        tax_by_rate[rate] = tax_by_rate.get(rate, Decimal("0")) + tax

    net_total = _cents(net_total)
    tax_total = _cents(tax_total)
    gross = _cents(net_total + tax_total)
    credit_used = min(credit, gross)
    total_due = _cents(gross - credit_used)
    credit_left = _cents(credit - credit_used)

    return {
        "net": net_total,
        "tax": tax_total,
        "gross": gross,
        "credit_used": _cents(credit_used),
        "total_due": total_due,
        "credit_left": credit_left,
        "tax_by_rate": {r: _cents(v) for r, v in tax_by_rate.items()},
    }
