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
    assert r["net"] == D("0.00") and r["gross"] == D("0.00")
    assert r["tax_by_rate"] == {}
    assert str(r["total_due"]) == "0.00"


def test_basic_and_zero_rate():
    r = invoice_totals([line("food", "10"), line("standard", "10")], "A")
    assert r["net"] == D("20.00")
    assert r["tax"] == D("2.00")
    assert r["tax_by_rate"] == {0: D("0.00"), 20: D("2.00")}


def test_bulk_stacks():
    r = invoice_totals([line("standard", "10", 10, "10")], "A")
    assert r["net"] == D("85.50")
    assert r["tax"] == D("17.10")


def test_no_bulk_for_other_category():
    r = invoice_totals([line("books", "10", 10)], "A")
    assert r["net"] == D("100.00")


def test_per_line_rounding():
    r = invoice_totals([line("books", "0.10", 1), line("books", "0.10", 1)], "A")
    assert r["tax"] == D("0.02")  # 0.005 -> 0.01 each


def test_credit():
    r = invoice_totals([line("standard", "10")], "A", D("5"))
    assert (r["gross"], r["credit_used"], r["total_due"], r["credit_left"]) == (
        D("12.00"), D("5.00"), D("7.00"), D("0.00"))
    r = invoice_totals([line("standard", "10")], "A", D("20"))
    assert (r["credit_used"], r["total_due"], r["credit_left"]) == (D("12.00"), D("0.00"), D("8.00"))


def test_region_b():
    r = invoice_totals([line("food", "100")], "B")
    assert r["tax_by_rate"] == {7: D("7.00")}


@pytest.mark.parametrize("kw", [
    dict(lines=[line()], region="C"),
    dict(lines=[line("toys")], region="A"),
    dict(lines=[line(qty=0)], region="A"),
    dict(lines=[line(qty=True)], region="A"),
    dict(lines=[line(qty=1.5)], region="A"),
    dict(lines=[line(price="-1")], region="A"),
    dict(lines=[line(disc="101")], region="A"),
    dict(lines=[line(disc="-1")], region="A"),
    dict(lines=[], region="A", credit=D("-1")),
])
def test_errors(kw):
    with pytest.raises(ValueError):
        invoice_totals(**kw)


def test_discount_bounds_ok():
    assert invoice_totals([line(disc="100")], "A")["net"] == D("0.00")
    assert invoice_totals([line(disc="0")], "A")["net"] == D("10.00")
