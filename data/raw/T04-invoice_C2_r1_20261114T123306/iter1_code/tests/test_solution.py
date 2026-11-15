from decimal import Decimal as D

import pytest

from solution import invoice_totals


def line(cat="standard", price="10", qty=1, disc=None, sku="x"):
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
    r = invoice_totals([line("standard", "10", 2), line("books", "20"), line("food", "5")], "A")
    assert r["net"] == D("45.00")
    assert r["tax"] == D("5.00")
    assert r["gross"] == D("50.00")
    assert r["tax_by_rate"] == {20: D("4.00"), 5: D("1.00"), 0: D("0.00")}
    assert all(isinstance(k, int) for k in r["tax_by_rate"])


def test_region_b():
    r = invoice_totals([line("food", "100"), line("standard", "100")], "B")
    assert r["tax"] == D("22.00")
    assert r["tax_by_rate"] == {7: D("7.00"), 15: D("15.00")}


def test_bulk_discount_threshold():
    assert invoice_totals([line("standard", "10", 9)], "A")["net"] == D("90.00")
    assert invoice_totals([line("standard", "10", 10)], "A")["net"] == D("95.00")
    assert invoice_totals([line("books", "10", 10)], "A")["net"] == D("100.00")


def test_stacked_discount():
    r = invoice_totals([line("standard", "10", 10, "10")], "A")
    assert r["net"] == D("85.50")
    assert r["tax"] == D("17.10")


def test_discount_bounds():
    assert invoice_totals([line(disc="100")], "A")["net"] == D("0.00")
    assert invoice_totals([line(disc="0")], "A")["net"] == D("10.00")


def test_rounding_half_up_per_line():
    # 0.5 * 0.01... net 0.025 -> 0.03
    r = invoice_totals([line("food", "0.025")], "A")
    assert r["net"] == D("0.03")
    # tax: 0.10 * 5% = 0.005 -> 0.01
    r = invoice_totals([line("books", "0.10")], "A")
    assert r["tax"] == D("0.01")
    # per line, not on totals
    r = invoice_totals([line("books", "0.10"), line("books", "0.10")], "A")
    assert r["tax"] == D("0.02")
    assert r["tax_by_rate"][5] == D("0.02")


def test_credit_partial():
    r = invoice_totals([line("food", "10")], "A", D("4"))
    assert r["credit_used"] == D("4.00")
    assert r["total_due"] == D("6.00")
    assert r["credit_left"] == D("0.00")


def test_credit_exceeds():
    r = invoice_totals([line("food", "10")], "A", D("25"))
    assert r["credit_used"] == D("10.00")
    assert r["total_due"] == D("0.00")
    assert r["credit_left"] == D("15.00")


@pytest.mark.parametrize("bad", [
    line("toys"), line(qty=0), line(qty=True), line(qty=1.5), line(price="-1"),
    line(disc="-1"), line(disc="101"),
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
    assert invoice_totals([line(price="0")], "A")["gross"] == D("0.00")
