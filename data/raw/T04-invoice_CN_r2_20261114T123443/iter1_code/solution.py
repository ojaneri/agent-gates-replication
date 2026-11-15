from decimal import Decimal, ROUND_HALF_UP


CENT = Decimal("0.01")
HUNDRED = Decimal("100")
BULK_DISCOUNT = Decimal("0.05")
BULK_MIN_QTY = 10

# Tax rates in percent, per region and category.
TAX_RATES = {
    "A": {"food": 0, "books": 5, "standard": 20},
    "B": {"food": 7, "books": 7, "standard": 15},
}


def _cents(value: Decimal) -> Decimal:
    """Round a Decimal to 2 places, halves rounded up."""
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def invoice_totals(lines: list[dict], region: str, credit: Decimal = Decimal("0")) -> dict:
    """Return the invoice totals. See spec.md."""
    if region not in TAX_RATES:
        raise ValueError(f"unknown region: {region!r}")
    rates = TAX_RATES[region]

    if credit < 0:
        raise ValueError("credit must not be negative")

    net_total = Decimal("0.00")
    tax_total = Decimal("0.00")
    tax_by_rate: dict[int, Decimal] = {}

    for line in lines:
        category = line["category"]
        if category not in rates:
            raise ValueError(f"unknown category: {category!r}")

        qty = line["qty"]
        if not _is_int(qty) or qty < 1:
            raise ValueError("qty must be an integer of at least 1")

        unit_price = Decimal(line["unit_price"])
        if unit_price < 0:
            raise ValueError("unit_price must not be negative")

        discount_pct = line.get("discount_pct")
        if discount_pct is None:
            discount_pct = Decimal("0")
        discount_pct = Decimal(discount_pct)
        if discount_pct < 0 or discount_pct > 100:
            raise ValueError("discount_pct must be between 0 and 100")

        # Line net: price * qty, reduced by the line's own discount.
        net = unit_price * qty * (Decimal("1") - discount_pct / HUNDRED)

        # Extra bulk discount on standard lines of 10 or more, multiplied on top.
        if category == "standard" and qty >= BULK_MIN_QTY:
            net = net * (Decimal("1") - BULK_DISCOUNT)

        net = _cents(net)

        rate = rates[category]
        tax = _cents(net * rate / HUNDRED)

        net_total += net
        tax_total += tax
        tax_by_rate[rate] = _cents(tax_by_rate.get(rate, Decimal("0")) + tax)

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
        "tax_by_rate": tax_by_rate,
    }
