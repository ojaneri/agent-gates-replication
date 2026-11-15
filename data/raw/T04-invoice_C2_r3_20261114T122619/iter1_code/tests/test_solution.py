from decimal import Decimal as D

import pytest

from solution import invoice_totals


def L(cat="standard", price="10", qty=1, disc=None, sku="x"):
    d = {"sku": sku, "category": cat, "unit_price": D(price), "qty": qty}
    if disc is not None:
        d["discount_pct"] = D(disc)
    return d


def test_empty():
    r = invoice_totals([], "A")
    assert r == {
        "net": D("0.00"), "tax": D("0.00"), "gross": D("0.00"),
        "credit_used": D("0.00"), "total_due": D("0.00"),
        "credit_left": D("0.00"), "tax_by_rate": {},
    }
    assert str(r["net"]) == "0.00"


def test_basic_region_a():
    r = invoice_totals([L("standard", "10", 2), L("books", "10"), L("food", "10")], "A")
    assert r["net"] == D("40.00")
    assert r["tax"] == D("4.50")
    assert r["gross"] == D("44.50")
    assert r["tax_by_rate"] == {20: D("4.00"), 5: D("0.50"), 0: D("0.00")}
    assert all(type(k) is int for k in r["tax_by_rate"])


def test_region_b():
    r = invoice_totals([L("food", "100"), L("books", "100"), L("standard", "100")], "B")
    assert r["tax_by_rate"] == {7: D("14.00"), 15: D("15.00")}
    assert r["tax"] == D("29.00")


def test_bulk_and_discount_multiply():
    r = invoice_totals([L("standard", "10", 10, "10")], "A")
    assert r["net"] == D("85.50")
    assert r["tax"] == D("17.10")


def test_bulk_threshold_and_category():
    assert invoice_totals([L("standard", "10", 9)], "A")["net"] == D("90.00")
    assert invoice_totals([L("standard", "10", 10)], "A")["net"] == D("95.00")
    assert invoice_totals([L("books", "10", 10)], "A")["net"] == D("100.00")


def test_discount_bounds():
    assert invoice_totals([L(disc="100")], "A")["net"] == D("0.00")
    assert invoice_totals([L(disc="0")], "A")["net"] == D("10.00")


def test_rounding_half_up_per_line():
    # 0.125 -> 0.13 net; tax 0.13*5% = 0.0065 -> 0.01
    r = invoice_totals([L("books", "0.125")], "A")
    assert r["net"] == D("0.13")
    assert r["tax"] == D("0.01")
    # per-line: two lines of 0.005 each round to 0.01 each
    r = invoice_totals([L("food", "0.005"), L("food", "0.005")], "A")
    assert r["net"] == D("0.02")


def test_credit_partial_and_full():
    r = invoice_totals([L("food", "10")], "A", D("4"))
    assert (r["credit_used"], r["total_due"], r["credit_left"]) == (D("4.00"), D("6.00"), D("0.00"))
    r = invoice_totals([L("food", "10")], "A", D("15"))
    assert (r["credit_used"], r["total_due"], r["credit_left"]) == (D("10.00"), D("0.00"), D("5.00"))
    r = invoice_totals([L("food", "10")], "A", D("10"))
    assert (r["credit_used"], r["total_due"], r["credit_left"]) == (D("10.00"), D("0.00"), D("0.00"))


@pytest.mark.parametrize("bad", [
    L(cat="toys"), L(qty=0), L(qty=True), L(qty=1.5), L(price="-1"),
    L(disc="-1"), L(disc="101"),
])
def test_invalid_lines(bad):
    with pytest.raises(ValueError):
        invoice_totals([bad], "A")


def test_invalid_region_and_credit():
    with pytest.raises(ValueError):
        invoice_totals([], "C")
    with pytest.raises(ValueError):
        invoice_totals([], "A", D("-1"))


def test_zero_price_ok():
    assert invoice_totals([L(price="0")], "A")["gross"] == D("0.00")
