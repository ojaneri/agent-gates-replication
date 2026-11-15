from decimal import Decimal as D

import pytest

from solution import invoice_totals


def line(cat="standard", price="10", qty=1, **kw):
    d = {"sku": "x", "category": cat, "unit_price": D(price), "qty": qty}
    d.update(kw)
    return d


def test_empty():
    r = invoice_totals([], "A")
    assert r["net"] == D("0.00") and str(r["gross"]) == "0.00"
    assert r["tax_by_rate"] == {}
    assert str(r["credit_left"]) == "0.00"


def test_basic_and_rates():
    r = invoice_totals([line("food", "10"), line("books", "10"), line()], "A")
    assert r["net"] == D("30.00")
    assert r["tax"] == D("2.50")
    assert r["tax_by_rate"] == {0: D("0.00"), 5: D("0.50"), 20: D("2.00")}


def test_bulk_stacks():
    r = invoice_totals([line(price="10", qty=10, discount_pct=D("10"))], "A")
    assert r["net"] == D("85.50")
    assert r["tax"] == D("17.10")


def test_no_bulk_for_books():
    r = invoice_totals([line("books", "10", 10)], "A")
    assert r["net"] == D("100.00")


def test_half_up_per_line():
    r = invoice_totals([line("food", "0.125"), line("food", "0.125")], "B")
    assert r["net"] == D("0.26")
    assert r["tax"] == D("0.02")


def test_credit():
    r = invoice_totals([line()], "A", D("5"))
    assert r["gross"] == D("12.00")
    assert r["credit_used"] == D("5.00") and r["total_due"] == D("7.00")
    r = invoice_totals([line()], "A", D("20"))
    assert r["credit_used"] == D("12.00")
    assert r["total_due"] == D("0.00") and r["credit_left"] == D("8.00")
    assert str(r["total_due"]) == "0.00"


@pytest.mark.parametrize("kw,region", [
    ({"category": "toys"}, "A"),
    ({"qty": 0}, "A"),
    ({"qty": True}, "A"),
    ({"qty": 1.5}, "A"),
    ({"unit_price": D("-1")}, "A"),
    ({"discount_pct": D("101")}, "A"),
    ({"discount_pct": D("-1")}, "A"),
    ({}, "C"),
])
def test_errors(kw, region):
    with pytest.raises(ValueError):
        invoice_totals([line(**kw)], region)


def test_negative_credit():
    with pytest.raises(ValueError):
        invoice_totals([], "A", D("-1"))


def test_discount_bounds_ok():
    assert invoice_totals([line(discount_pct=D("100"))], "A")["net"] == D("0.00")
    assert invoice_totals([line(discount_pct=D("0"))], "B")["tax"] == D("1.50")
