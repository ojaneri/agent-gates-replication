from decimal import ROUND_HALF_UP, Decimal, localcontext

RATES = {
    "A": {"food": 0, "books": 5, "standard": 20},
    "B": {"food": 7, "books": 7, "standard": 15},
}
CENT = Decimal("0.01")
HUNDRED = Decimal(100)


def _round(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _validate_line(line: dict, rates: dict) -> None:
    if line["category"] not in rates:
        raise ValueError("unknown category")
    qty = line["qty"]
    if isinstance(qty, bool) or not isinstance(qty, int) or qty < 1:
        raise ValueError("invalid qty")
    if line["unit_price"] < 0:
        raise ValueError("negative unit price")
    if not Decimal(0) <= line.get("discount_pct", Decimal(0)) <= HUNDRED:
        raise ValueError("invalid discount")


def _line_values(line: dict, rates: dict) -> tuple:
    _validate_line(line, rates)
    rate = rates[line["category"]]
    discount = line.get("discount_pct", Decimal(0))
    net = line["unit_price"] * line["qty"] * (HUNDRED - discount) / HUNDRED
    if line["category"] == "standard" and line["qty"] >= 10:
        net = net * Decimal("0.95")
    net = _round(net)
    tax = _round(net * rate / HUNDRED)
    return rate, net, tax


def invoice_totals(lines: list[dict], region: str, credit: Decimal = Decimal("0")) -> dict:
    """Return the invoice totals. See spec.md."""
    if region not in RATES:
        raise ValueError("unknown region")
    if credit < 0:
        raise ValueError("negative credit")
    rates = RATES[region]
    net = tax = Decimal("0.00")
    tax_by_rate: dict = {}
    with localcontext() as ctx:
        ctx.prec = 60
        for line in lines:
            rate, line_net, line_tax = _line_values(line, rates)
            net += line_net
            tax += line_tax
            tax_by_rate[rate] = tax_by_rate.get(rate, Decimal("0.00")) + line_tax
        gross = net + tax
        credit_used = min(credit, gross)
        return {
            "net": _round(net),
            "tax": _round(tax),
            "gross": _round(gross),
            "credit_used": _round(credit_used),
            "total_due": _round(gross - credit_used),
            "credit_left": _round(credit - credit_used),
            "tax_by_rate": {r: _round(v) for r, v in tax_by_rate.items()},
        }
