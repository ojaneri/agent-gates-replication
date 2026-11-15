from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")
ZERO = Decimal("0")
HUNDRED = Decimal("100")

# Tax rates in percent, per region and category.
TAX_RATES = {
    "A": {"food": 0, "books": 5, "standard": 20},
    "B": {"food": 7, "books": 7, "standard": 15},
}

BULK_MIN_QTY = 10
BULK_PCT = Decimal("5")  # extra percent off standard lines, applied multiplicatively


def _cents(value: Decimal) -> Decimal:
    """Round to 2 decimal places, halves rounded up."""
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _check_qty(qty) -> None:
    if isinstance(qty, bool) or not isinstance(qty, int) or qty < 1:
        raise ValueError(f"qty must be an integer >= 1, got {qty!r}")


def invoice_totals(lines: list[dict], region: str, credit: Decimal = Decimal("0")) -> dict:
    """Return the invoice totals. See spec.md."""
    if not isinstance(region, str) or region not in TAX_RATES:
        raise ValueError(f"unknown region: {region!r}")
    if credit < 0:
        raise ValueError("credit must not be negative")
    rates = TAX_RATES[region]

    net_total = ZERO
    tax_total = ZERO
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
        discount = line.get("discount_pct", ZERO)
        if discount < 0 or discount > 100:
            raise ValueError("discount_pct must be between 0 and 100")

        # Line net: unit_price * qty reduced by the line discount (exact, then rounded once).
        net = unit_price * qty * (HUNDRED - discount) / HUNDRED
        if category == "standard" and qty >= BULK_MIN_QTY:
            net = net * (HUNDRED - BULK_PCT) / HUNDRED
        net = _cents(net)

        rate = rates[category]
        tax = _cents(net * rate / HUNDRED)

        net_total += net
        tax_total += tax
        tax_by_rate[rate] = tax_by_rate.get(rate, ZERO) + tax

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
