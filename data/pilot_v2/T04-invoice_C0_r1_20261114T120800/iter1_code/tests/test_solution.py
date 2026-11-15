from decimal import Decimal as D

import pytest

from solution import invoice_totals


def L(cat="standard", price="10", qty=1, **kw):
    d = {"sku": "x", "category": cat, "unit_price": D(price), "qty": qty}
    d.update(kw)
    return d


def test_empty():
    r = invoice_totals([], "A")
    assert r["gross"] == D("0.00") and r["tax_by_rate"] == {}
    assert str(r["net"]) == "0.00"


def test_basic_and_zero_rate():
    r = invoice_totals([L("standard", "10", 2), L("food", "5", 1)], "A")
    assert r["net"] == D("25.00")
    assert r["tax"] == D("4.00")
    assert r["tax_by_rate"] == {20: D("4.00"), 0: D("0.00")}


def test_bulk_and_discount_compound():
    r = invoice_totals([L("standard", "10", 10, discount_pct=D("10"))], "A")
    assert r["net"] == D("85.50")
    assert r["tax"] == D("17.10")


def test_bulk_only_standard():
    r = invoice_totals([L("books", "10", 10)], "A")
    assert r["net"] == D("100.00")


def test_per_line_rounding_half_up():
    r = invoice_totals([L("books", "0.10", 1), L("books", "0.10", 1)], "A")
    # tax per line 0.005 -> 0.01
    assert r["tax"] == D("0.02")


def test_credit():
    r = invoice_totals([L("food", "10", 1)], "B", D("4"))
    assert r["gross"] == D("10.70")
    assert (r["credit_used"], r["total_due"], r["credit_left"]) == (D("4.00"), D("6.70"), D("0.00"))
    r = invoice_totals([L("food", "10", 1)], "B", D("20"))
    assert (r["credit_used"], r["total_due"], r["credit_left"]) == (D("10.70"), D("0.00"), D("9.30"))


@pytest.mark.parametrize("kw,region,credit", [
    ({}, "C", D("0")),
    ({"cat": "toys"}, "A", D("0")),
    ({"qty": 0}, "A", D("0")),
    ({"qty": True}, "A", D("0")),
    ({"price": "-1"}, "A", D("0")),
    ({"discount_pct": D("101")}, "A", D("0")),
    ({"discount_pct": D("-1")}, "A", D("0")),
    ({}, "A", D("-1")),
])
def test_errors(kw, region, credit):
    with pytest.raises(ValueError):
        invoice_totals([L(**kw)], region, credit)


def test_discount_bounds_ok():
    assert invoice_totals([L(discount_pct=D("100"))], "A")["net"] == D("0.00")
    assert invoice_totals([L(discount_pct=D("0"))], "A")["net"] == D("10.00")
