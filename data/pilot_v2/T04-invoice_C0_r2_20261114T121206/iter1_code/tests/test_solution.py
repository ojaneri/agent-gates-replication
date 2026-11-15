from decimal import Decimal as D

import pytest

from solution import invoice_totals


def line(cat="standard", price="10", qty=1, **kw):
    return {"sku": "x", "category": cat, "unit_price": D(price), "qty": qty, **kw}


def test_empty():
    r = invoice_totals([], "A")
    assert r["net"] == D("0.00") and r["tax_by_rate"] == {}
    assert str(r["gross"]) == "0.00"


def test_basic_and_tax_by_rate():
    r = invoice_totals([line("food", "10"), line("books", "20"), line(price="100")], "A")
    assert r["net"] == D("130.00")
    assert r["tax"] == D("21.00")
    assert r["tax_by_rate"] == {0: D("0.00"), 5: D("1.00"), 20: D("20.00")}


def test_stacked_discount():
    r = invoice_totals([line(price="10", qty=10, discount_pct=D("10"))], "A")
    assert r["net"] == D("85.50")
    assert r["tax"] == D("17.10")


def test_bulk_only_standard():
    r = invoice_totals([line("books", "10", 10)], "A")
    assert r["net"] == D("100.00")


def test_half_up_per_line():
    r = invoice_totals([line("books", "0.10", 1), line("books", "0.10", 1)], "A")
    assert r["tax"] == D("0.02")  # 0.005 -> 0.01 each
    r = invoice_totals([line(price="0.125")], "B")
    assert r["net"] == D("0.13")


def test_credit():
    r = invoice_totals([line(price="100")], "A", D("50"))
    assert (r["credit_used"], r["total_due"], r["credit_left"]) == (D("50.00"), D("70.00"), D("0.00"))
    r = invoice_totals([line(price="100")], "A", D("500"))
    assert (r["credit_used"], r["total_due"], r["credit_left"]) == (D("120.00"), D("0.00"), D("380.00"))


@pytest.mark.parametrize("bad", [
    dict(region="C"),
    dict(lines=[line("toys")]),
    dict(lines=[line(qty=0)]),
    dict(lines=[line(qty=True)]),
    dict(lines=[line(qty=1.5)]),
    dict(lines=[line(price="-1")]),
    dict(lines=[line(discount_pct=D("101"))]),
    dict(lines=[line(discount_pct=D("-1"))]),
    dict(credit=D("-1")),
])
def test_errors(bad):
    args = dict(lines=[line()], region="A", credit=D("0"))
    args.update(bad)
    with pytest.raises(ValueError):
        invoice_totals(**args)


def test_discount_bounds_ok():
    assert invoice_totals([line(discount_pct=D("100"))], "A")["net"] == D("0.00")
    assert invoice_totals([line(discount_pct=D("0"))], "B")["net"] == D("10.00")
