from decimal import ROUND_HALF_UP, Decimal

RATES = {
    "A": {"food": 0, "books": 5, "standard": 20},
    "B": {"food": 7, "books": 7, "standard": 15},
}
CENT = Decimal("0.01")
HUNDRED = Decimal("100")


def _money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _check_line(line: dict, table: dict) -> None:
    if line["category"] not in table:
        raise ValueError("unknown category")
    qty = line["qty"]
    if isinstance(qty, bool) or not isinstance(qty, int) or qty < 1:
        raise ValueError("invalid qty")
    if line["unit_price"] < 0:
        raise ValueError("negative price")
    if not 0 <= line.get("discount_pct", Decimal("0")) <= 100:
        raise ValueError("invalid discount")


def _line_values(line: dict, table: dict) -> tuple:
    _check_line(line, table)
    pct = line.get("discount_pct", Decimal("0"))
    net = line["unit_price"] * line["qty"] * (HUNDRED - pct) / HUNDRED
    if line["category"] == "standard" and line["qty"] >= 10:
        net = net * Decimal("95") / HUNDRED
    net = _money(net)
    rate = table[line["category"]]
    tax = _money(net * rate / HUNDRED)
    return net, tax, rate


def invoice_totals(lines: list[dict], region: str, credit: Decimal = Decimal("0")) -> dict:
    """Return the invoice totals. See spec.md."""
    if region not in RATES:
        raise ValueError("unknown region")
    if credit < 0:
        raise ValueError("negative credit")
    table = RATES[region]
    net_total = Decimal("0.00")
    tax_total = Decimal("0.00")
    by_rate: dict = {}
    for line in lines:
        net, tax, rate = _line_values(line, table)
        net_total += net
        tax_total += tax
        by_rate[rate] = by_rate.get(rate, Decimal("0.00")) + tax
    gross = net_total + tax_total
    used = min(credit, gross)
    return {
        "net": _money(net_total),
        "tax": _money(tax_total),
        "gross": _money(gross),
        "credit_used": _money(used),
        "total_due": _money(gross - used),
        "credit_left": _money(credit - used),
        "tax_by_rate": {r: _money(v) for r, v in by_rate.items()},
    }
