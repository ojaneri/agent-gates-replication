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


def test_basic_region_a():
    r = invoice_totals([line("food", "10"), line("books", "10"), line(price="10")], "A")
    assert r["net"] == D("30.00")
    assert r["tax"] == D("2.50")
    assert r["gross"] == D("32.50")
    assert r["tax_by_rate"] == {0: D("0.00"), 5: D("0.50"), 20: D("2.00")}


def test_region_b():
    r = invoice_totals([line("food", "100"), line(price="100")], "B")
    assert r["tax_by_rate"] == {7: D("7.00"), 15: D("15.00")}


def test_bulk_and_discount_multiply():
    r = invoice_totals([line(price="10", qty=10, discount_pct=D("10"))], "A")
    assert r["net"] == D("85.50")
    assert r["tax"] == D("17.10")


def test_bulk_not_for_other_categories_or_below_10():
    assert invoice_totals([line("books", "10", 10)], "A")["net"] == D("100.00")
    assert invoice_totals([line("standard", "10", 9)], "A")["net"] == D("90.00")


def test_half_up_per_line():
    r = invoice_totals([line("food", "0.005"), line("food", "0.005")], "A")
    assert r["net"] == D("0.02")
    r = invoice_totals([line("books", "0.10")], "A")
    assert r["tax"] == D("0.01") * 1  # 0.005 -> 0.01


def test_credit_partial_and_full():
    r = invoice_totals([line(price="10")], "A", D("5"))
    assert (r["credit_used"], r["total_due"], r["credit_left"]) == (D("5.00"), D("7.00"), D("0.00"))
    r = invoice_totals([line(price="10")], "A", D("20"))
    assert (r["credit_used"], r["total_due"], r["credit_left"]) == (D("12.00"), D("0.00"), D("8.00"))


@pytest.mark.parametrize(
    "lines,region,credit",
    [
        ([], "C", D("0")),
        ([line("toys")], "A", D("0")),
        ([line(qty=0)], "A", D("0")),
        ([line(qty=True)], "A", D("0")),
        ([line(qty=1.5)], "A", D("0")),
        ([line(price="-1")], "A", D("0")),
        ([line(discount_pct=D("-1"))], "A", D("0")),
        ([line(discount_pct=D("100.01"))], "A", D("0")),
        ([], "A", D("-1")),
    ],
)
def test_errors(lines, region, credit):
    with pytest.raises(ValueError):
        invoice_totals(lines, region, credit)


def test_discount_bounds_allowed():
    assert invoice_totals([line(discount_pct=D("100"))], "A")["net"] == D("0.00")
    assert invoice_totals([line(discount_pct=D("0"))], "A")["net"] == D("10.00")
