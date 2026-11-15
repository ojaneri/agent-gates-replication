from decimal import Decimal

import pytest

from solution import invoice_totals

D = Decimal


def line(category="books", unit_price="10.00", qty=1, discount_pct=None):
    d = {
        "sku": "SKU",
        "category": category,
        "unit_price": D(unit_price),
        "qty": qty,
    }
    if discount_pct is not None:
        d["discount_pct"] = D(discount_pct)
    return d


def test_simple_books_region_a():
    r = invoice_totals([line("books", "10.00", 2)], "A")
    assert r["net"] == D("20.00")
    assert r["tax"] == D("1.00")
    assert r["gross"] == D("21.00")
    assert r["credit_used"] == D("0.00")
    assert r["total_due"] == D("21.00")
    assert r["credit_left"] == D("0.00")
    assert r["tax_by_rate"] == {5: D("1.00")}


def test_output_has_two_decimal_places():
    r = invoice_totals([line("books", "10", 2)], "A")
    for key in ("net", "tax", "gross", "credit_used", "total_due", "credit_left"):
        assert str(r[key]) == str(r[key].quantize(D("0.01"))), key
        assert r[key].as_tuple().exponent == -2, key
    for v in r["tax_by_rate"].values():
        assert v.as_tuple().exponent == -2


def test_empty_lines_gives_zeros():
    r = invoice_totals([], "A")
    assert r["net"] == D("0.00")
    assert r["tax"] == D("0.00")
    assert r["gross"] == D("0.00")
    assert r["credit_used"] == D("0.00")
    assert r["total_due"] == D("0.00")
    assert r["credit_left"] == D("0.00")
    assert r["tax_by_rate"] == {}


def test_region_b_rates():
    r = invoice_totals([line("food", "10.00", 1), line("standard", "10.00", 1)], "B")
    # food 7% -> 0.70, standard 15% -> 1.50
    assert r["tax_by_rate"] == {7: D("0.70"), 15: D("1.50")}
    assert r["tax"] == D("2.20")
    assert r["net"] == D("20.00")
    assert r["gross"] == D("22.20")


def test_zero_rate_is_included():
    r = invoice_totals([line("food", "10.00", 1)], "A")
    assert r["tax_by_rate"] == {0: D("0.00")}
    assert r["tax"] == D("0.00")


def test_rates_not_on_any_line_are_excluded():
    r = invoice_totals([line("standard", "10.00", 1)], "A")
    assert r["tax_by_rate"] == {20: D("2.00")}


def test_tax_by_rate_sums_same_rate_lines():
    r = invoice_totals(
        [line("standard", "10.00", 1), line("standard", "5.00", 2)], "A"
    )
    # 10.00*20% = 2.00, 10.00*20% = 2.00
    assert r["tax_by_rate"] == {20: D("4.00")}
    assert r["tax"] == D("4.00")


def test_line_discount_applies():
    r = invoice_totals([line("books", "10.00", 1, discount_pct="25")], "A")
    assert r["net"] == D("7.50")
    assert r["tax"] == D("0.38")  # 0.375 -> 0.38 half up


def test_discount_bounds_allowed():
    r0 = invoice_totals([line("books", "10.00", 1, discount_pct="0")], "A")
    assert r0["net"] == D("10.00")
    r100 = invoice_totals([line("books", "10.00", 1, discount_pct="100")], "A")
    assert r100["net"] == D("0.00")
    assert r100["tax"] == D("0.00")


def test_bulk_discount_standard_qty_10_multiplies():
    # 1.00 * 10 = 10.00; 10% -> 9.00; then 5% -> 8.55
    r = invoice_totals(
        [line("standard", "1.00", 10, discount_pct="10")], "A"
    )
    assert r["net"] == D("8.55")
    assert r["tax"] == D("1.71")  # 8.55 * 20%
    assert r["gross"] == D("10.26")


def test_bulk_discount_threshold_is_10_for_standard_only():
    r9 = invoice_totals([line("standard", "10.00", 9)], "A")
    assert r9["net"] == D("90.00")
    r10 = invoice_totals([line("standard", "10.00", 10)], "A")
    assert r10["net"] == D("95.00")
    rb = invoice_totals([line("books", "10.00", 10)], "A")
    assert rb["net"] == D("100.00")
    rf = invoice_totals([line("food", "10.00", 10)], "A")
    assert rf["net"] == D("100.00")


def test_line_net_rounded_half_up_before_tax():
    # 0.05 * 1 with 50% discount = 0.025 -> 0.03 (half up)
    r = invoice_totals([line("food", "0.05", 1, discount_pct="50")], "B")
    assert r["net"] == D("0.03")
    # tax on 0.03 at 7% = 0.0021 -> 0.00
    assert r["tax"] == D("0.00")


def test_line_tax_rounded_half_up():
    # 0.10 books in region A at 5% = 0.005 -> 0.01
    r = invoice_totals([line("books", "0.10", 1)], "A")
    assert r["tax"] == D("0.01")
    assert r["tax_by_rate"] == {5: D("0.01")}


def test_rounding_is_per_line_not_on_totals():
    # two lines of 0.10 books A: each tax rounds to 0.01 -> total 0.02
    r = invoice_totals([line("books", "0.10", 1), line("books", "0.10", 1)], "A")
    assert r["tax"] == D("0.02")


def test_credit_partial():
    r = invoice_totals([line("books", "10.00", 2)], "A", credit=D("5.00"))
    assert r["gross"] == D("21.00")
    assert r["credit_used"] == D("5.00")
    assert r["total_due"] == D("16.00")
    assert r["credit_left"] == D("0.00")


def test_credit_exceeds_gross():
    r = invoice_totals([line("books", "10.00", 2)], "A", credit=D("50.00"))
    assert r["credit_used"] == D("21.00")
    assert r["total_due"] == D("0.00")
    assert r["credit_left"] == D("29.00")


def test_credit_default_is_zero():
    r = invoice_totals([line("books", "10.00", 2)], "A")
    assert r["credit_used"] == D("0.00")
    assert r["credit_left"] == D("0.00")


@pytest.mark.parametrize(
    "lines, region, credit",
    [
        ([line()], "C", D("0")),
        ([line(category="toys")], "A", D("0")),
        ([line(qty=0)], "A", D("0")),
        ([line(qty=-1)], "A", D("0")),
        ([line(qty=True)], "A", D("0")),
        ([line(qty=1.5)], "A", D("0")),
        ([line(unit_price="-0.01")], "A", D("0")),
        ([line(discount_pct="101")], "A", D("0")),
        ([line(discount_pct="-0.01")], "A", D("0")),
        ([line()], "A", D("-1")),
    ],
)
def test_validation_errors(lines, region, credit):
    with pytest.raises(ValueError):
        invoice_totals(lines, region, credit)
