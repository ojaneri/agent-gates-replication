from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")
HUNDRED = Decimal("100")
BULK_DISCOUNT_PCT = Decimal("5")
BULK_MIN_QTY = 10
BULK_CATEGORY = "standard"

CATEGORIES = ("food", "books", "standard")

# Tax rates in percent, per region and category.
TAX_RATES = {
    "A": {"food": 0, "books": 5, "standard": 20},
    "B": {"food": 7, "books": 7, "standard": 15},
}


def _cents(value: Decimal) -> Decimal:
    """Round a Decimal to 2 places, halves rounded up."""
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _to_decimal(value, name: str) -> Decimal:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a number, not bool")
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, str)):
        return Decimal(value)
    raise ValueError(f"{name} must be a Decimal")


def invoice_totals(lines: list[dict], region: str, credit: Decimal = Decimal("0")) -> dict:
    """Return the invoice totals. See spec.md."""
    if region not in TAX_RATES:
        raise ValueError(f"unknown region: {region!r}")

    credit = _to_decimal(credit, "credit")
    if credit < 0:
        raise ValueError("credit must not be negative")

    rates = TAX_RATES[region]
    net_total = Decimal("0")
    tax_total = Decimal("0")
    tax_by_rate: dict[int, Decimal] = {}

    for line in lines:
        category = line.get("category")
        if category not in CATEGORIES:
            raise ValueError(f"unknown category: {category!r}")

        qty = line.get("qty")
        if isinstance(qty, bool) or not isinstance(qty, int) or qty < 1:
            raise ValueError("qty must be an integer of at least 1")

        unit_price = _to_decimal(line.get("unit_price"), "unit_price")
        if unit_price < 0:
            raise ValueError("unit_price must not be negative")

        discount_pct = _to_decimal(line.get("discount_pct", Decimal("0")), "discount_pct")
        if discount_pct < 0 or discount_pct > HUNDRED:
            raise ValueError("discount_pct must be between 0 and 100")

        amount = unit_price * qty * (HUNDRED - discount_pct) / HUNDRED
        if category == BULK_CATEGORY and qty >= BULK_MIN_QTY:
            amount = amount * (HUNDRED - BULK_DISCOUNT_PCT) / HUNDRED
        line_net = _cents(amount)

        rate = rates[category]
        line_tax = _cents(line_net * rate / HUNDRED)

        net_total += line_net
        tax_total += line_tax
        tax_by_rate[rate] = tax_by_rate.get(rate, Decimal("0")) + line_tax

    net = _cents(net_total)
    tax = _cents(tax_total)
    gross = _cents(net + tax)
    credit_used = min(credit, gross)
    total_due = _cents(gross - credit_used)
    credit_left = _cents(credit - credit_used)

    return {
        "net": net,
        "tax": tax,
        "gross": gross,
        "credit_used": _cents(credit_used),
        "total_due": total_due,
        "credit_left": credit_left,
        "tax_by_rate": {rate: _cents(value) for rate, value in tax_by_rate.items()},
    }
