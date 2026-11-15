from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")
HUNDRED = Decimal("100")

TAX_RATES = {
    "A": {"food": 0, "books": 5, "standard": 20},
    "B": {"food": 7, "books": 7, "standard": 15},
}

VALID_CATEGORIES = ("food", "books", "standard")


def _money(value: Decimal) -> Decimal:
    """Round a Decimal to 2 places, halves rounded up."""
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _to_decimal(value) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        raise ValueError("expected a Decimal, got bool")
    if isinstance(value, (int, str)):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(str(value))
    raise ValueError(f"expected a Decimal, got {type(value).__name__}")


def invoice_totals(lines: list[dict], region: str, credit: Decimal = Decimal("0")) -> dict:
    """Return the invoice totals. See spec.md."""
    if region not in TAX_RATES:
        raise ValueError(f"unknown region: {region!r}")
    rates = TAX_RATES[region]

    credit = _to_decimal(credit)
    if credit < 0:
        raise ValueError("credit must not be negative")

    net_total = Decimal("0")
    tax_total = Decimal("0")
    tax_by_rate: dict[int, Decimal] = {}

    for line in lines:
        category = line["category"]
        if category not in VALID_CATEGORIES:
            raise ValueError(f"unknown category: {category!r}")

        qty = line["qty"]
        if isinstance(qty, bool) or not isinstance(qty, int) or qty < 1:
            raise ValueError("qty must be an integer of at least 1")

        unit_price = _to_decimal(line["unit_price"])
        if unit_price < 0:
            raise ValueError("unit_price must not be negative")

        discount_pct = _to_decimal(line.get("discount_pct", Decimal("0")))
        if discount_pct < 0 or discount_pct > 100:
            raise ValueError("discount_pct must be between 0 and 100")

        # Line net: price * qty, less the line discount, then the bulk discount.
        net = unit_price * qty * (Decimal("1") - discount_pct / HUNDRED)
        if category == "standard" and qty >= 10:
            net = net * (Decimal("1") - Decimal("5") / HUNDRED)
        net = _money(net)

        rate = rates[category]
        tax = _money(net * Decimal(rate) / HUNDRED)

        net_total += net
        tax_total += tax
        tax_by_rate[rate] = tax_by_rate.get(rate, Decimal("0")) + tax

    net_total = _money(net_total)
    tax_total = _money(tax_total)
    gross = _money(net_total + tax_total)

    credit_used = _money(min(credit, gross))
    total_due = _money(gross - credit_used)
    credit_left = _money(credit - credit_used)

    return {
        "net": net_total,
        "tax": tax_total,
        "gross": gross,
        "credit_used": credit_used,
        "total_due": total_due,
        "credit_left": credit_left,
        "tax_by_rate": {rate: _money(value) for rate, value in tax_by_rate.items()},
    }
