from decimal import Decimal as D

import pytest

from solution import invoice_totals


def line(category="food", unit_price="1.00", qty=1, discount_pct=None):
    d = {"sku": "X", "category": category, "unit_price": D(unit_price), "qty": qty}
    if discount_pct is not None:
        d["discount_pct"] = D(discount_pct)
    return d


def test_empty_lines_gives_zeros():
    r = invoice_totals([], "A")
    assert r == {
        "net": D("0.00"),
        "tax": D("0.00"),
        "gross": D("0.00"),
        "credit_used": D("0.00"),
        "total_due": D("0.00"),
        "credit_left": D("0.00"),
        "tax_by_rate": {},
    }


def test_single_standard_line_region_a():
    r = invoice_totals([line("standard", "10.00", 2)], "A")
    assert r["net"] == D("20.00")
    assert r["tax"] == D("4.00")
    assert r["gross"] == D("24.00")
    assert r["tax_by_rate"] == {20: D("4.00")}


def test_zero_rate_included_with_zero_value():
    r = invoice_totals([line("food", "3.00", 1)], "A")
    assert r["tax"] == D("0.00")
    assert r["tax_by_rate"] == {0: D("0.00")}


def test_rates_not_present_are_omitted():
    r = invoice_totals([line("books", "10.00", 1)], "B")
    assert r["tax_by_rate"] == {7: D("0.70")}


def test_region_b_standard_rate():
    r = invoice_totals([line("standard", "100.00", 1)], "B")
    assert r["tax"] == D("15.00")
    assert r["tax_by_rate"] == {15: D("15.00")}


def test_bulk_discount_applies_only_to_standard_at_ten_or_more():
    r = invoice_totals([line("standard", "1.00", 10)], "A")
    # 10 * 1.00 = 10.00, 5% off = 9.50
    assert r["net"] == D("9.50")
    assert r["tax"] == D("1.90")

    r = invoice_totals([line("standard", "1.00", 9)], "A")
    assert r["net"] == D("9.00")

    r = invoice_totals([line("books", "1.00", 10)], "A")
    assert r["net"] == D("10.00")


def test_line_discount_and_bulk_discount_multiply():
    # 10% then 5% leaves 85.5%, not 85%
    r = invoice_totals([line("standard", "100.00", 10, discount_pct="10")], "A")
    assert r["net"] == D("855.00")


def test_discount_zero_and_hundred():
    r = invoice_totals([line("food", "5.00", 2, discount_pct="100")], "B")
    assert r["net"] == D("0.00")
    r = invoice_totals([line("food", "5.00", 2, discount_pct="0")], "B")
    assert r["net"] == D("10.00")


def test_rounding_half_up_per_line_not_on_totals():
    # 0.005 rounds up to 0.01 at line level
    r = invoice_totals([line("standard", "0.05", 1, discount_pct="10")], "A")
    # net 0.045 -> 0.05 ; tax 0.05 * 0.20 = 0.01
    assert r["net"] == D("0.05")
    assert r["tax"] == D("0.01")

    # Per-line rounding: two lines of 0.125 net each round to 0.13 each
    lines = [line("food", "0.125", 1), line("food", "0.125", 1)]
    r = invoice_totals(lines, "A")
    assert r["net"] == D("0.26")


def test_tax_rounding_per_line():
    # books 5% of 0.10 = 0.005 -> 0.01 per line; two lines => 0.02
    lines = [line("books", "0.10", 1), line("books", "0.10", 1)]
    r = invoice_totals(lines, "A")
    assert r["tax"] == D("0.02")
    assert r["tax_by_rate"] == {5: D("0.02")}


def test_totals_sum_multiple_lines_and_tax_by_rate():
    lines = [
        line("food", "10.00", 1),
        line("standard", "20.00", 1),
        line("books", "30.00", 2),
    ]
    r = invoice_totals(lines, "A")
    assert r["net"] == D("90.00")
    # food 0, standard 4.00, books 3.00
    assert r["tax"] == D("7.00")
    assert r["gross"] == D("97.00")
    assert r["tax_by_rate"] == {0: D("0.00"), 20: D("4.00"), 5: D("3.00")}


def test_credit_partially_covers_gross():
    r = invoice_totals([line("standard", "10.00", 1)], "A", credit=D("5.00"))
    # gross 12.00
    assert r["gross"] == D("12.00")
    assert r["credit_used"] == D("5.00")
    assert r["total_due"] == D("7.00")
    assert r["credit_left"] == D("0.00")


def test_credit_exceeds_gross():
    r = invoice_totals([line("standard", "10.00", 1)], "A", credit=D("50.00"))
    assert r["credit_used"] == D("12.00")
    assert r["total_due"] == D("0.00")
    assert r["credit_left"] == D("38.00")


def test_zero_credit_default():
    r = invoice_totals([line("food", "2.00", 1)], "A")
    assert r["credit_used"] == D("0.00")
    assert r["total_due"] == D("2.00")
    assert r["credit_left"] == D("0.00")


def test_money_values_have_two_decimal_places():
    r = invoice_totals([line("food", "1", 3)], "B", credit=D("1"))
    for key in ("net", "tax", "gross", "credit_used", "total_due", "credit_left"):
        assert r[key].as_tuple().exponent == -2, key
    for v in r["tax_by_rate"].values():
        assert v.as_tuple().exponent == -2


def test_unknown_region_raises():
    with pytest.raises(ValueError):
        invoice_totals([], "C")


def test_unknown_category_raises():
    with pytest.raises(ValueError):
        invoice_totals([line("toys")], "A")


@pytest.mark.parametrize("qty", [0, -1, 1.5, True, False])
def test_invalid_qty_raises(qty):
    bad = line("food", "1.00", 1)
    bad["qty"] = qty
    with pytest.raises(ValueError):
        invoice_totals([bad], "A")


def test_negative_unit_price_raises():
    with pytest.raises(ValueError):
        invoice_totals([line("food", "-1.00", 1)], "A")


@pytest.mark.parametrize("pct", ["-0.01", "100.01"])
def test_discount_out_of_range_raises(pct):
    with pytest.raises(ValueError):
        invoice_totals([line("food", "1.00", 1, discount_pct=pct)], "A")


def test_negative_credit_raises():
    with pytest.raises(ValueError):
        invoice_totals([], "A", credit=D("-1"))
