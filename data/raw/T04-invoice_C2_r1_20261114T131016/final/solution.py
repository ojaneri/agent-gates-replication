from decimal import Decimal, ROUND_HALF_UP

ZERO = Decimal("0")
HUNDRED = Decimal("100")
CENT = Decimal("0.01")
BULK_FACTOR = Decimal("0.95")  # an extra 5% off
BULK_CATEGORY = "standard"
BULK_MIN_QTY = 10
CATEGORIES = ("food", "books", "standard")

# Tax rates in percent, keyed by region then category.
TAX_RATES = {
    "A": {"food": 0, "books": 5, "standard": 20},
    "B": {"food": 7, "books": 7, "standard": 15},
}


def _cents(value: Decimal) -> Decimal:
    """Round to cents, halves up, and keep exactly two decimal places."""
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _validate_region(region) -> None:
    if region not in TAX_RATES:
        raise ValueError(f"unknown region: {region!r}")


def _validate_qty(qty) -> None:
    if isinstance(qty, bool) or not isinstance(qty, int) or qty < 1:
        raise ValueError(f"qty must be an integer >= 1, got {qty!r}")


def _validate_line(line: dict) -> None:
    if line["category"] not in CATEGORIES:
        raise ValueError(f"unknown category: {line['category']!r}")
    _validate_qty(line["qty"])
    if line["unit_price"] < 0:
        raise ValueError("unit_price must not be negative")
    if not ZERO <= line.get("discount_pct", ZERO) <= HUNDRED:
        raise ValueError("discount_pct must be between 0 and 100")


def _line_net(line: dict) -> Decimal:
    """Net of one line after its own discount and the bulk discount, in cents."""
    discount = line.get("discount_pct", ZERO)
    net = line["unit_price"] * line["qty"] * (HUNDRED - discount) / HUNDRED
    if line["category"] == BULK_CATEGORY and line["qty"] >= BULK_MIN_QTY:
        net = net * BULK_FACTOR
    return _cents(net)


def _line_tax(net: Decimal, rate: int) -> Decimal:
    """Tax on a rounded line net, in cents."""
    return _cents(net * rate / HUNDRED)


def _credit_split(gross: Decimal, credit: Decimal) -> tuple:
    """Return (credit_used, total_due, credit_left), all in cents."""
    credit_used = min(credit, gross)
    return (
        _cents(credit_used),
        _cents(gross - credit_used),
        _cents(credit - credit_used),
    )


def invoice_totals(lines: list[dict], region: str, credit: Decimal = Decimal("0")) -> dict:
    """Return the invoice totals. See spec.md."""
    _validate_region(region)
    if credit < 0:
        raise ValueError("credit must not be negative")
    rates = TAX_RATES[region]

    net_total = ZERO
    tax_total = ZERO
    tax_by_rate = {}
    for line in lines:
        _validate_line(line)
        net = _line_net(line)
        rate = rates[line["category"]]
        tax = _line_tax(net, rate)
        net_total += net
        tax_total += tax
        tax_by_rate[rate] = tax_by_rate.get(rate, ZERO) + tax

    gross = net_total + tax_total
    credit_used, total_due, credit_left = _credit_split(gross, credit)
    return {
        "net": _cents(net_total),
        "tax": _cents(tax_total),
        "gross": _cents(gross),
        "credit_used": credit_used,
        "total_due": total_due,
        "credit_left": credit_left,
        "tax_by_rate": {rate: _cents(tax) for rate, tax in tax_by_rate.items()},
    }
