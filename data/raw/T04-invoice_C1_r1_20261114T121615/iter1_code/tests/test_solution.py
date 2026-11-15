from decimal import Decimal as D

import pytest

from solution import invoice_totals


def L(cat="standard", price="10", qty=1, **kw):
    d = {"sku": "x", "category": cat, "unit_price": D(price), "qty": qty}
    d.update(kw)
    return d


def test_empty():
    r = invoice_totals([], "A")
    assert r["net"] == D("0.00") and r["gross"] == D("0.00")
    assert r["tax_by_rate"] == {}
    assert str(r["credit_left"]) == "0.00"


def test_basic_and_rates():
    r = invoice_totals([L("food", "10"), L("books", "10"), L("standard", "10")], "A")
    assert r["net"] == D("30.00")
    assert r["tax"] == D("2.50")
    assert r["gross"] == D("32.50")
    assert r["tax_by_rate"] == {0: D("0.00"), 5: D("0.50"), 20: D("2.00")}


def test_region_b_merges_rate():
    r = invoice_totals([L("food", "10"), L("books", "10")], "B")
    assert r["tax_by_rate"] == {7: D("1.40")}


def test_bulk_and_discount():
    r = invoice_totals([L(price="10", qty=10, discount_pct=D("10"))], "A")
    assert r["net"] == D("85.50")
    assert r["tax"] == D("17.10")
    r = invoice_totals([L("books", "10", 10)], "A")
    assert r["net"] == D("100.00")
    r = invoice_totals([L(price="10", qty=9)], "A")
    assert r["net"] == D("90.00")


def test_per_line_rounding():
    r = invoice_totals([L("books", "0.10"), L("books", "0.10")], "A")
    # each tax 0.005 -> 0.01
    assert r["tax"] == D("0.02")
    r = invoice_totals([L(price="0.025")], "A")
    assert r["net"] == D("0.03")


def test_credit():
    r = invoice_totals([L(price="10")], "A", D("5"))
    assert (r["credit_used"], r["total_due"], r["credit_left"]) == (D("5.00"), D("7.00"), D("0.00"))
    r = invoice_totals([L(price="10")], "A", D("20"))
    assert (r["credit_used"], r["total_due"], r["credit_left"]) == (D("12.00"), D("0.00"), D("8.00"))


@pytest.mark.parametrize("kw,region,credit", [
    ({}, "C", D("0")),
    ({"cat": "toys"}, "A", D("0")),
    ({"qty": 0}, "A", D("0")),
    ({"qty": True}, "A", D("0")),
    ({"qty": 1.5}, "A", D("0")),
    ({"price": "-1"}, "A", D("0")),
    ({"discount_pct": D("-1")}, "A", D("0")),
    ({"discount_pct": D("101")}, "A", D("0")),
    ({}, "A", D("-1")),
])
def test_errors(kw, region, credit):
    with pytest.raises(ValueError):
        invoice_totals([L(**kw)], region, credit)


def test_discount_bounds_ok():
    assert invoice_totals([L(discount_pct=D("100"))], "A")["net"] == D("0.00")
    assert invoice_totals([L(discount_pct=D("0"))], "A")["net"] == D("10.00")
