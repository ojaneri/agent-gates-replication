from decimal import Decimal as D

import pytest

from solution import invoice_totals


def L(cat="standard", price="10", qty=1, **kw):
    return dict(sku="x", category=cat, unit_price=D(price), qty=qty, **kw)


def test_empty():
    r = invoice_totals([], "A")
    assert r["net"] == D("0.00") and r["gross"] == D("0.00")
    assert r["tax_by_rate"] == {}
    assert str(r["credit_left"]) == "0.00"


def test_basic_and_rates():
    r = invoice_totals([L("food"), L("standard")], "A")
    assert r["net"] == D("20.00")
    assert r["tax"] == D("2.00")
    assert r["tax_by_rate"] == {0: D("0.00"), 20: D("2.00")}


def test_bulk_stacking():
    r = invoice_totals([L(price="10", qty=10, discount_pct=D("10"))], "A")
    assert r["net"] == D("85.50")
    assert r["tax"] == D("17.10")


def test_bulk_not_for_books():
    r = invoice_totals([L("books", qty=10)], "B")
    assert r["net"] == D("100.00")
    assert r["tax"] == D("7.00")


def test_rounding_per_line():
    r = invoice_totals([L("books", "0.10", 1), L("books", "0.10", 1)], "A")
    assert r["tax"] == D("0.02")  # 0.005 -> 0.01 each


def test_credit():
    r = invoice_totals([L()], "A", D("5"))
    assert r["total_due"] == D("7.00") and r["credit_used"] == D("5.00")
    r = invoice_totals([L()], "A", D("50"))
    assert r["total_due"] == D("0.00") and r["credit_left"] == D("38.00")


@pytest.mark.parametrize("lines,region,credit", [
    ([L()], "C", D("0")),
    ([L("toys")], "A", D("0")),
    ([L(qty=0)], "A", D("0")),
    ([L(qty=True)], "A", D("0")),
    ([L(qty=1.5)], "A", D("0")),
    ([L(price="-1")], "A", D("0")),
    ([L(discount_pct=D("101"))], "A", D("0")),
    ([L(discount_pct=D("-1"))], "A", D("0")),
    ([L()], "A", D("-1")),
])
def test_errors(lines, region, credit):
    with pytest.raises(ValueError):
        invoice_totals(lines, region, credit)


def test_discount_bounds():
    assert invoice_totals([L(discount_pct=D("100"))], "A")["net"] == D("0.00")
    assert invoice_totals([L(discount_pct=D("0"))], "A")["net"] == D("10.00")
