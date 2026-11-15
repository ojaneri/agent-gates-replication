from decimal import ROUND_HALF_UP, Decimal

RATES = {
    "A": {"food": 0, "books": 5, "standard": 20},
    "B": {"food": 7, "books": 7, "standard": 15},
}
CENT = Decimal("0.01")
HUNDRED = Decimal("100")


def _q(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _validate_line(line: dict, region: str) -> None:
    if line["category"] not in RATES[region]:
        raise ValueError("unknown category")
    qty = line["qty"]
    if isinstance(qty, bool) or not isinstance(qty, int) or qty < 1:
        raise ValueError("invalid qty")
    if line["unit_price"] < 0:
        raise ValueError("negative price")
    if not 0 <= line.get("discount_pct", Decimal("0")) <= 100:
        raise ValueError("invalid discount")


def _line_net(line: dict) -> Decimal:
    disc = line.get("discount_pct", Decimal("0"))
    net = line["unit_price"] * line["qty"] * (HUNDRED - disc) / HUNDRED
    if line["category"] == "standard" and line["qty"] >= 10:
        net = net * Decimal("0.95")
    return _q(net)


def invoice_totals(lines: list[dict], region: str, credit: Decimal = Decimal("0")) -> dict:
    """Return the invoice totals. See spec.md."""
    if region not in RATES:
        raise ValueError("unknown region")
    if credit < 0:
        raise ValueError("negative credit")
    net = Decimal("0.00")
    tax = Decimal("0.00")
    by_rate: dict = {}
    for line in lines:
        _validate_line(line, region)
        rate = RATES[region][line["category"]]
        line_net = _line_net(line)
        line_tax = _q(line_net * rate / HUNDRED)
        net += line_net
        tax += line_tax
        by_rate[rate] = by_rate.get(rate, Decimal("0.00")) + line_tax
    gross = net + tax
    used = min(credit, gross)
    return {
        "net": _q(net),
        "tax": _q(tax),
        "gross": _q(gross),
        "credit_used": _q(used),
        "total_due": _q(gross - used),
        "credit_left": _q(credit - used),
        "tax_by_rate": {k: _q(v) for k, v in by_rate.items()},
    }
