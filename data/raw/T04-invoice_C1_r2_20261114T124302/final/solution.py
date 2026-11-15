from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")
ZERO = Decimal("0.00")
HUNDRED = Decimal("100")
BULK_MIN_QTY = 10
BULK_FACTOR = Decimal("0.95")

TAX_RATES = {
    "A": {"food": 0, "books": 5, "standard": 20},
    "B": {"food": 7, "books": 7, "standard": 15},
}


def _cents(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _check_qty(qty) -> None:
    if isinstance(qty, bool) or not isinstance(qty, int) or qty < 1:
        raise ValueError(f"qty must be an integer >= 1, got {qty!r}")


def invoice_totals(lines: list[dict], region: str, credit: Decimal = Decimal("0")) -> dict:
    """Return the invoice totals. See spec.md."""
    if region not in TAX_RATES:
        raise ValueError(f"unknown region: {region!r}")
    if credit < 0:
        raise ValueError("credit must not be negative")
    rates = TAX_RATES[region]

    net = ZERO
    tax = ZERO
    tax_by_rate: dict[int, Decimal] = {}

    for line in lines:
        category = line["category"]
        if category not in rates:
            raise ValueError(f"unknown category: {category!r}")
        qty = line["qty"]
        _check_qty(qty)
        unit_price = line["unit_price"]
        if unit_price < 0:
            raise ValueError("unit_price must not be negative")
        discount = line.get("discount_pct", Decimal("0"))
        if discount < 0 or discount > 100:
            raise ValueError("discount_pct must be between 0 and 100")

        amount = unit_price * qty * (HUNDRED - discount) / HUNDRED
        if category == "standard" and qty >= BULK_MIN_QTY:
            amount = amount * BULK_FACTOR
        line_net = _cents(amount)

        rate = rates[category]
        line_tax = _cents(line_net * rate / HUNDRED)

        net += line_net
        tax += line_tax
        tax_by_rate[rate] = tax_by_rate.get(rate, ZERO) + line_tax

    net = _cents(net)
    tax = _cents(tax)
    gross = net + tax
    credit_used = _cents(min(credit, gross))
    total_due = gross - credit_used
    credit_left = _cents(credit - credit_used)

    return {
        "net": net,
        "tax": tax,
        "gross": gross,
        "credit_used": credit_used,
        "total_due": total_due,
        "credit_left": credit_left,
        "tax_by_rate": {rate: _cents(value) for rate, value in tax_by_rate.items()},
    }
