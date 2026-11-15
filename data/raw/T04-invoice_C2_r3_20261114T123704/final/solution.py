from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")
HUNDRED = Decimal("100")
ZERO = Decimal("0.00")
BULK_MIN_QTY = 10
BULK_PCT = Decimal("5")

# Tax rates in percent, keyed by region and then by category.
TAX_RATES = {
    "A": {"food": 0, "books": 5, "standard": 20},
    "B": {"food": 7, "books": 7, "standard": 15},
}


def _cents(value: Decimal) -> Decimal:
    """Round to 2 decimal places, halves rounded up."""
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _check_qty(qty) -> None:
    if isinstance(qty, bool) or not isinstance(qty, int) or qty < 1:
        raise ValueError(f"qty must be an integer of at least 1, got {qty!r}")


def _check_pct(pct) -> None:
    if pct < 0 or pct > HUNDRED:
        raise ValueError(f"discount_pct must be between 0 and 100, got {pct!r}")


def _validate_line(line: dict, rates: dict) -> int:
    """Validate one line and return its tax rate (percent)."""
    category = line["category"]
    if category not in rates:
        raise ValueError(f"unknown category: {category!r}")
    _check_qty(line["qty"])
    if line["unit_price"] < 0:
        raise ValueError("unit_price must not be negative")
    _check_pct(line.get("discount_pct", Decimal("0")))
    return rates[category]


def _line_net(line: dict) -> Decimal:
    """Net value of one line, rounded to cents."""
    pct = line.get("discount_pct", Decimal("0"))
    net = line["unit_price"] * line["qty"] * (HUNDRED - pct) / HUNDRED
    if line["category"] == "standard" and line["qty"] >= BULK_MIN_QTY:
        net = net * (HUNDRED - BULK_PCT) / HUNDRED
    return _cents(net)


def invoice_totals(lines: list[dict], region: str, credit: Decimal = Decimal("0")) -> dict:
    """Return the invoice totals. See spec.md."""
    if region not in TAX_RATES:
        raise ValueError(f"unknown region: {region!r}")
    if credit < 0:
        raise ValueError("credit must not be negative")

    rates = TAX_RATES[region]
    net_total = ZERO
    tax_total = ZERO
    tax_by_rate: dict[int, Decimal] = {}

    for line in lines:
        rate = _validate_line(line, rates)
        line_net = _line_net(line)
        line_tax = _cents(line_net * rate / HUNDRED)
        net_total += line_net
        tax_total += line_tax
        tax_by_rate[rate] = tax_by_rate.get(rate, ZERO) + line_tax

    gross = net_total + tax_total
    credit_used = min(credit, gross)

    return {
        "net": _cents(net_total),
        "tax": _cents(tax_total),
        "gross": _cents(gross),
        "credit_used": _cents(credit_used),
        "total_due": _cents(gross - credit_used),
        "credit_left": _cents(credit - credit_used),
        "tax_by_rate": {rate: _cents(value) for rate, value in tax_by_rate.items()},
    }
