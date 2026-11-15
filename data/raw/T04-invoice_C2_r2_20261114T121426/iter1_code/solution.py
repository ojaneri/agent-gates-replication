from decimal import ROUND_HALF_UP, Decimal

_CENT = Decimal("0.01")
_HUNDRED = Decimal("100")
_ZERO = Decimal("0")
_BULK_QTY = 10
_BULK_FACTOR = Decimal("0.95")
_TAX_RATES = {
    "A": {"food": 0, "books": 5, "standard": 20},
    "B": {"food": 7, "books": 7, "standard": 15},
}


def _money(value: Decimal) -> Decimal:
    """Round to cents, halves rounded up."""
    return value.quantize(_CENT, rounding=ROUND_HALF_UP)


def _validate_qty(qty) -> None:
    if isinstance(qty, bool) or not isinstance(qty, int) or qty < 1:
        raise ValueError(f"qty must be an integer >= 1, got {qty!r}")


def _line_values(line: dict, rates: dict) -> tuple[Decimal, Decimal, int]:
    """Return (line net, line tax, tax rate) for one invoice line."""
    category = line["category"]
    if category not in rates:
        raise ValueError(f"unknown category {category!r}")
    qty = line["qty"]
    _validate_qty(qty)
    unit_price = Decimal(line["unit_price"])
    if unit_price < 0:
        raise ValueError("unit_price must not be negative")
    discount = Decimal(line.get("discount_pct", _ZERO))
    if discount < 0 or discount > _HUNDRED:
        raise ValueError("discount_pct must be between 0 and 100")

    net = unit_price * qty * (_HUNDRED - discount) / _HUNDRED
    if category == "standard" and qty >= _BULK_QTY:
        net = net * _BULK_FACTOR
    net = _money(net)

    rate = rates[category]
    tax = _money(net * rate / _HUNDRED)
    return net, tax, rate


def invoice_totals(lines: list[dict], region: str, credit: Decimal = Decimal("0")) -> dict:
    """Return the invoice totals. See spec.md."""
    if region not in _TAX_RATES:
        raise ValueError(f"unknown region {region!r}")
    credit = Decimal(credit)
    if credit < 0:
        raise ValueError("credit must not be negative")
    rates = _TAX_RATES[region]

    net_sum = _ZERO
    tax_sum = _ZERO
    tax_by_rate: dict[int, Decimal] = {}
    for line in lines:
        line_net, line_tax, rate = _line_values(line, rates)
        net_sum += line_net
        tax_sum += line_tax
        tax_by_rate[rate] = tax_by_rate.get(rate, _ZERO) + line_tax

    gross = net_sum + tax_sum
    credit_used = min(credit, gross)
    return {
        "net": _money(net_sum),
        "tax": _money(tax_sum),
        "gross": _money(gross),
        "credit_used": _money(credit_used),
        "total_due": _money(gross - credit_used),
        "credit_left": _money(credit - credit_used),
        "tax_by_rate": {rate: _money(value) for rate, value in tax_by_rate.items()},
    }
