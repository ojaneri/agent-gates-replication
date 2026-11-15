from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")
ZERO = Decimal("0.00")
HUNDRED = Decimal("100")
BULK_FACTOR = Decimal("0.95")  # extra 5% bulk discount

# Tax rates in percent, per region and category.
TAX_RATES = {
    "A": {"food": 0, "books": 5, "standard": 20},
    "B": {"food": 7, "books": 7, "standard": 15},
}


def _cents(value: Decimal) -> Decimal:
    """Round to 2 decimal places, halves rounded up."""
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _to_decimal(value) -> Decimal:
    """Convert a numeric value to Decimal, rejecting non-finite values."""
    if isinstance(value, bool):
        raise ValueError("boolean is not a valid amount")
    if isinstance(value, Decimal):
        result = value
    elif isinstance(value, float):
        result = Decimal(str(value))
    else:
        result = Decimal(value)
    if not result.is_finite():
        raise ValueError("amount must be finite")
    return result


def invoice_totals(lines: list[dict], region: str, credit: Decimal = Decimal("0")) -> dict:
    """Return the invoice totals. See spec.md."""
    if region not in TAX_RATES:
        raise ValueError(f"unknown region: {region!r}")
    rates = TAX_RATES[region]

    credit = _cents(_to_decimal(credit))
    if credit < 0:
        raise ValueError("credit must not be negative")

    net_total = ZERO
    tax_total = ZERO
    tax_by_rate: dict[int, Decimal] = {}

    for line in lines:
        category = line["category"]
        if category not in rates:
            raise ValueError(f"unknown category: {category!r}")

        qty = line["qty"]
        if isinstance(qty, bool) or not isinstance(qty, int) or qty < 1:
            raise ValueError("qty must be an integer of at least 1")

        unit_price = _to_decimal(line["unit_price"])
        if unit_price < 0:
            raise ValueError("unit_price must not be negative")

        discount = _to_decimal(line.get("discount_pct", Decimal("0")))
        if not (Decimal("0") <= discount <= HUNDRED):
            raise ValueError("discount_pct must be between 0 and 100")

        # Line net: price * qty, less the line discount, then the bulk discount
        # (multiplicative, so the two discounts stack).
        amount = unit_price * qty * (1 - discount / HUNDRED)
        if category == "standard" and qty >= 10:
            amount *= BULK_FACTOR
        line_net = _cents(amount)

        rate = rates[category]
        line_tax = _cents(line_net * rate / HUNDRED)

        net_total += line_net
        tax_total += line_tax
        tax_by_rate[rate] = tax_by_rate.get(rate, ZERO) + line_tax

    net = _cents(net_total)
    tax = _cents(tax_total)
    gross = _cents(net + tax)

    credit_used = _cents(min(credit, gross))
    total_due = _cents(gross - credit_used)
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
