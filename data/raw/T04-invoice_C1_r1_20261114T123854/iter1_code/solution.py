from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")
HUNDRED = Decimal("100")
BULK_FACTOR = Decimal("0.95")  # extra 5% bulk discount
BULK_MIN_QTY = 10

# Tax rates in percent, keyed by region and then by category.
TAX_RATES = {
    "A": {"food": 0, "books": 5, "standard": 20},
    "B": {"food": 7, "books": 7, "standard": 15},
}


def _to_decimal(value) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _cents(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def invoice_totals(lines: list[dict], region: str, credit: Decimal = Decimal("0")) -> dict:
    """Return the invoice totals. See spec.md."""
    if region not in TAX_RATES:
        raise ValueError(f"unknown region: {region!r}")
    credit = _to_decimal(credit)
    if credit < 0:
        raise ValueError("credit must not be negative")

    rates = TAX_RATES[region]
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

        unit_price = _to_decimal(line["unit_price"])
        if unit_price < 0:
            raise ValueError("unit_price must not be negative")

        discount_pct = _to_decimal(line.get("discount_pct", Decimal("0")))
        if discount_pct < 0 or discount_pct > HUNDRED:
            raise ValueError("discount_pct must be between 0 and 100")

        # Line net: price * qty, less the line discount, then the bulk discount
        # (multiplied on top), rounded to cents.
        net = unit_price * qty * (1 - discount_pct / HUNDRED)
        if category == "standard" and qty >= BULK_MIN_QTY:
            net *= BULK_FACTOR
        net = _cents(net)

        # Line tax: rounded per line.
        rate = rates[category]
        tax = _cents(net * rate / HUNDRED)

        net_total += net
        tax_total += tax
        tax_by_rate[rate] = tax_by_rate.get(rate, Decimal("0")) + tax

    gross = net_total + tax_total
    credit_used = min(credit, gross)
    total_due = gross - credit_used
    credit_left = credit - credit_used

    return {
        "net": _cents(net_total),
        "tax": _cents(tax_total),
        "gross": _cents(gross),
        "credit_used": _cents(credit_used),
        "total_due": _cents(total_due),
        "credit_left": _cents(credit_left),
        "tax_by_rate": {rate: _cents(value) for rate, value in sorted(tax_by_rate.items())},
    }
