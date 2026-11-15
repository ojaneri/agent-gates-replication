from decimal import Decimal as D

import pytest

from solution import invoice_totals


def L(cat="standard", price="10", qty=1, **kw):
    d = {"sku": "x", "category": cat, "unit_price": D(price), "qty": qty}
    d.update({k: D(v) for k, v in kw.items()})
    return d


def test_empty():
    r = invoice_totals([], "A")
    assert r["net"] == D("0.00") and r["tax_by_rate"] == {}
    assert str(r["total_due"]) == "0.00"


def test_basic_and_credit():
    r = invoice_totals([L(price="10.00", qty=2)], "A", D("5"))
    assert r["net"] == D("20.00") and r["tax"] == D("4.00")
    assert r["gross"] == D("24.00")
    assert r["credit_used"] == D("5.00") and r["total_due"] == D("19.00")
    assert r["credit_left"] == D("0.00")
    assert r["tax_by_rate"] == {20: D("4.00")}


def test_credit_exceeds():
    r = invoice_totals([L(price="10")], "A", D("100"))
    assert r["credit_used"] == D("12.00") and r["credit_left"] == D("88.00")
    assert r["total_due"] == D("0.00")


def test_bulk_stacked():
    r = invoice_totals([L(price="10", qty=10, discount_pct="10")], "A")
    assert r["net"] == D("85.50")


def test_bulk_not_for_food_and_zero_rate():
    r = invoice_totals([L("food", "10", 10)], "A")
    assert r["net"] == D("100.00")
    assert r["tax_by_rate"] == {0: D("0.00")}


def test_rounding_half_up_per_line():
    r = invoice_totals([L("books", "0.10", 1, discount_pct="5")] * 2, "A")
    assert r["net"] == D("0.20")  # 0.095 -> 0.10 each
    r = invoice_totals([L("books", "0.10", 1)] * 3, "B")
    assert r["tax"] == D("0.03")  # 0.007 -> 0.01 each


def test_region_b_rates():
    r = invoice_totals([L("food", "100"), L("standard", "100")], "B")
    assert r["tax_by_rate"] == {7: D("7.00"), 15: D("15.00")}


@pytest.mark.parametrize("lines,region,credit", [
    ([L()], "C", D("0")),
    ([L("toys")], "A", D("0")),
    ([L(qty=0)], "A", D("0")),
    ([L(qty=True)], "A", D("0")),
    ([L(qty=1.5)], "A", D("0")),
    ([L(price="-1")], "A", D("0")),
    ([L(discount_pct="-1")], "A", D("0")),
    ([L(discount_pct="101")], "A", D("0")),
    ([L()], "A", D("-1")),
])
def test_errors(lines, region, credit):
    with pytest.raises(ValueError):
        invoice_totals(lines, region, credit)


def test_discount_bounds():
    assert invoice_totals([L(discount_pct="100")], "A")["net"] == D("0.00")
    assert invoice_totals([L(discount_pct="0")], "A")["net"] == D("10.00")
