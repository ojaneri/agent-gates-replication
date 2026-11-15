from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")

TAX_RATES = {
    "A": {"food": 0, "books": 5, "standard": 20},
    "B": {"food": 7, "books": 7, "standard": 15},
}


def _cents(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _as_decimal(value) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        raise ValueError("boolean is not a valid money value")
    return Decimal(value)


def invoice_totals(lines: list[dict], region: str, credit: Decimal = Decimal("0")) -> dict:
    """Return the invoice totals. See spec.md."""
    if region not in TAX_RATES:
        raise ValueError(f"unknown region: {region!r}")
    rates = TAX_RATES[region]

    credit = _as_decimal(credit)
    if credit < 0:
        raise ValueError("credit must not be negative")

    net_total = Decimal("0.00")
    tax_total = Decimal("0.00")
    tax_by_rate: dict[int, Decimal] = {}

    for line in lines:
        category = line["category"]
        if category not in ("food", "books", "standard"):
            raise ValueError(f"unknown category: {category!r}")

        qty = line["qty"]
        if isinstance(qty, bool) or not isinstance(qty, int) or qty < 1:
            raise ValueError("qty must be an integer of at least 1")

        unit_price = _as_decimal(line["unit_price"])
        if unit_price < 0:
            raise ValueError("unit_price must not be negative")

        discount_pct = _as_decimal(line.get("discount_pct", Decimal("0")))
        if discount_pct < 0 or discount_pct > 100:
            raise ValueError("discount_pct must be between 0 and 100")

        amount = unit_price * qty * (Decimal("1") - discount_pct / Decimal("100"))
        if category == "standard" and qty >= 10:
            amount = amount * Decimal("0.95")
        line_net = _cents(amount)

        rate = rates[category]
        line_tax = _cents(line_net * Decimal(rate) / Decimal("100"))

        net_total += line_net
        tax_total += line_tax
        tax_by_rate[rate] = tax_by_rate.get(rate, Decimal("0.00")) + line_tax

    net = _cents(net_total)
    tax = _cents(tax_total)
    gross = _cents(net + tax)

    credit_used = min(credit, gross)
    total_due = gross - credit_used
    credit_left = credit - credit_used

    return {
        "net": net,
        "tax": tax,
        "gross": gross,
        "credit_used": _cents(credit_used),
        "total_due": _cents(total_due),
        "credit_left": _cents(credit_left),
        "tax_by_rate": {rate: _cents(value) for rate, value in tax_by_rate.items()},
    }
