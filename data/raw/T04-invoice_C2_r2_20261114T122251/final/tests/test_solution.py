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
    assert str(r["credit_left"]) == "0.00"


def test_basic_region_a():
    r = invoice_totals([line("food"), line("books"), line("standard")], "A")
    assert r["net"] == D("30.00")
    assert r["tax"] == D("2.50")
    assert r["gross"] == D("32.50")
    assert r["tax_by_rate"] == {0: D("0.00"), 5: D("0.50"), 20: D("2.00")}
    assert str(r["tax_by_rate"][0]) == "0.00"


def test_region_b():
    r = invoice_totals([line("food"), line("books"), line("standard")], "B")
    assert r["tax_by_rate"] == {7: D("1.40"), 15: D("1.50")}


def test_discount_and_bulk():
    r = invoice_totals([line(price="10", qty=10, disc="10")], "A")
    assert r["net"] == D("85.50")
    assert r["tax"] == D("17.10")


def test_bulk_threshold():
    assert invoice_totals([line(qty=9)], "A")["net"] == D("90.00")
    assert invoice_totals([line(qty=10)], "A")["net"] == D("95.00")
    assert invoice_totals([line("books", qty=10)], "A")["net"] == D("100.00")


def test_discount_bounds():
    assert invoice_totals([line(disc="100")], "A")["net"] == D("0.00")
    assert invoice_totals([line(disc="0")], "A")["net"] == D("10.00")


def test_half_up_per_line():
    r = invoice_totals([line("food", price="0.005")] * 2, "A")
    assert r["net"] == D("0.02")
    r = invoice_totals([line("books", price="0.10")], "A")
    assert r["tax"] == D("0.01")  # 0.005 -> 0.01
    r = invoice_totals([line("books", price="0.09")], "A")
    assert r["tax"] == D("0.00")  # 0.0045


def test_credit():
    r = invoice_totals([line("food")], "A", D("4"))
    assert (r["credit_used"], r["total_due"], r["credit_left"]) == (D("4.00"), D("6.00"), D("0.00"))
    r = invoice_totals([line("food")], "A", D("15"))
    assert (r["credit_used"], r["total_due"], r["credit_left"]) == (D("10.00"), D("0.00"), D("5.00"))
    assert str(r["credit_left"]) == "5.00"


def test_credit_zero_ok():
    assert invoice_totals([], "A", D("0"))["credit_used"] == D("0")


@pytest.mark.parametrize(
    "bad",
    [
        line(cat="toys"),
        line(qty=0),
        line(qty=True),
        line(qty=1.5),
        line(price="-1"),
        line(disc="-1"),
        line(disc="101"),
    ],
)
def test_invalid_lines(bad):
    with pytest.raises(ValueError):
        invoice_totals([bad], "A")


def test_invalid_region_credit():
    with pytest.raises(ValueError):
        invoice_totals([], "C")
    with pytest.raises(ValueError):
        invoice_totals([], "A", D("-1"))


def test_zero_price_ok():
    assert invoice_totals([line(price="0")], "A")["gross"] == D("0.00")
