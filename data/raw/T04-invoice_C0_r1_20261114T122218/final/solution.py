from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")
HUNDRED = Decimal("100")
BULK_FACTOR = Decimal("0.95")

# Tax rates in percent, by region and category.
TAX_RATES = {
    "A": {"food": 0, "books": 5, "standard": 20},
    "B": {"food": 7, "books": 7, "standard": 15},
}


def _cents(value: Decimal) -> Decimal:
    """Round to 2 decimal places, halves rounded up."""
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def invoice_totals(lines: list[dict], region: str, credit: Decimal = Decimal("0")) -> dict:
    """Return the invoice totals. See spec.md."""
    if region not in TAX_RATES:
        raise ValueError(f"unknown region: {region!r}")
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

        unit_price = Decimal(line["unit_price"])
        if unit_price < 0:
            raise ValueError("unit_price must not be negative")

        discount_pct = line.get("discount_pct")
        discount_pct = Decimal("0") if discount_pct is None else Decimal(discount_pct)
        if discount_pct < 0 or discount_pct > HUNDRED:
            raise ValueError("discount_pct must be between 0 and 100")

        # Line net: price * qty, less the line's own discount.
        net = unit_price * qty * (Decimal("1") - discount_pct / HUNDRED)
        # Extra 5% bulk discount on standard lines of 10 or more, applied on top.
        if category == "standard" and qty >= 10:
            net = net * BULK_FACTOR
        line_net = _cents(net)

        rate = rates[category]
        line_tax = _cents(line_net * rate / HUNDRED)

        net_total += line_net
        tax_total += line_tax
        tax_by_rate[rate] = tax_by_rate.get(rate, Decimal("0")) + line_tax

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
