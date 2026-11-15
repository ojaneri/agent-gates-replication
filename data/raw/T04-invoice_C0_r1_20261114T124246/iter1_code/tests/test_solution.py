from decimal import Decimal as D

import pytest

from solution import invoice_totals


def line(cat="standard", price="10", qty=1, disc=None):
    d = {"sku": "x", "category": cat, "unit_price": D(price), "qty": qty}
    if disc is not None:
        d["discount_pct"] = D(disc)
    return d


def test_empty():
    r = invoice_totals([], "A")
    assert r["net"] == D("0.00") and str(r["gross"]) == "0.00"
    assert r["tax_by_rate"] == {}


def test_basic_and_tax_by_rate():
    r = invoice_totals([line("food", "10"), line("standard", "10")], "A")
    assert r["net"] == D("20.00")
    assert r["tax"] == D("2.00")
    assert r["tax_by_rate"] == {0: D("0.00"), 20: D("2.00")}


def test_bulk_stacks():
    r = invoice_totals([line("standard", "10", 10, "10")], "A")
    assert r["net"] == D("85.50")


def test_no_bulk_for_other_category():
    assert invoice_totals([line("books", "10", 10)], "A")["net"] == D("100.00")


def test_half_up_per_line():
    r = invoice_totals([line("books", "0.10", 1), line("books", "0.10", 1)], "A")
    # tax per line 0.005 -> 0.01
    assert r["tax"] == D("0.02")


def test_credit():
    r = invoice_totals([line("food", "10")], "A", D("4"))
    assert (r["credit_used"], r["total_due"], r["credit_left"]) == (D("4.00"), D("6.00"), D("0.00"))
    r = invoice_totals([line("food", "10")], "A", D("15"))
    assert (r["credit_used"], r["total_due"], r["credit_left"]) == (D("10.00"), D("0.00"), D("5.00"))


@pytest.mark.parametrize("kw", [
    dict(lines=[line(qty=0)], region="A"),
    dict(lines=[line(qty=True)], region="A"),
    dict(lines=[line(qty=1.5)], region="A"),
    dict(lines=[line(price="-1")], region="A"),
    dict(lines=[line(disc="101")], region="A"),
    dict(lines=[line(disc="-1")], region="A"),
    dict(lines=[line(cat="toys")], region="A"),
    dict(lines=[], region="C"),
    dict(lines=[], region="A", credit=D("-1")),
])
def test_errors(kw):
    with pytest.raises(ValueError):
        invoice_totals(**kw)


def test_discount_bounds_ok():
    assert invoice_totals([line(disc="100")], "B")["net"] == D("0.00")
    assert invoice_totals([line(disc="0")], "B")["tax"] == D("1.50")
