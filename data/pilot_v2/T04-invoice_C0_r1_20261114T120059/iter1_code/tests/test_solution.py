import os
import sys
from decimal import Decimal

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from solution import invoice_totals  # noqa: E402

D = Decimal


def line(category="food", unit_price="1.00", qty=1, discount_pct=None):
    item = {"sku": "x", "category": category, "unit_price": D(unit_price), "qty": qty}
    if discount_pct is not None:
        item["discount_pct"] = D(discount_pct)
    return item


def test_empty_lines():
    result = invoice_totals([], "A")
    assert result == {
        "net": D("0.00"),
        "tax": D("0.00"),
        "gross": D("0.00"),
        "credit_used": D("0.00"),
        "total_due": D("0.00"),
        "credit_left": D("0.00"),
        "tax_by_rate": {},
    }


def test_single_standard_line_region_a():
    result = invoice_totals([line("standard", "10.00", 2)], "A")
    assert result["net"] == D("20.00")
    assert result["tax"] == D("4.00")
    assert result["gross"] == D("24.00")
    assert result["tax_by_rate"] == {20: D("4.00")}


def test_zero_rate_food_included_with_zero():
    result = invoice_totals([line("food", "5.00", 1)], "A")
    assert result["tax"] == D("0.00")
    assert result["tax_by_rate"] == {0: D("0.00")}


def test_rates_not_present_are_omitted():
    result = invoice_totals([line("books", "10.00", 1)], "B")
    assert result["tax_by_rate"] == {7: D("0.70")}


def test_region_b_standard_rate():
    result = invoice_totals([line("standard", "100.00", 1)], "B")
    assert result["tax"] == D("15.00")
    assert result["tax_by_rate"] == {15: D("15.00")}


def test_bulk_discount_applies_to_standard_at_ten_units():
    result = invoice_totals([line("standard", "1.00", 10)], "A")
    # 10.00 * 0.95 = 9.50 ; tax 20% = 1.90
    assert result["net"] == D("9.50")
    assert result["tax"] == D("1.90")


def test_bulk_discount_not_below_ten_units():
    result = invoice_totals([line("standard", "1.00", 9)], "A")
    assert result["net"] == D("9.00")


def test_bulk_discount_not_for_food_or_books():
    result = invoice_totals([line("food", "1.00", 10), line("books", "1.00", 10)], "A")
    assert result["net"] == D("20.00")


def test_line_discount_and_bulk_discount_multiply():
    # 10% then 5% leaves 85.5%, not 85%
    result = invoice_totals([line("standard", "100.00", 10, discount_pct="10")], "A")
    # 1000 * 0.9 * 0.95 = 855.00
    assert result["net"] == D("855.00")


def test_half_up_rounding_per_line():
    # 0.125 rounds up to 0.13 at the line level
    result = invoice_totals([line("books", "0.25", 1, discount_pct="50")], "A")
    # net = 0.125 -> 0.13 ; tax 5% of 0.13 = 0.0065 -> 0.01
    assert result["net"] == D("0.13")
    assert result["tax"] == D("0.01")


def test_rounding_is_per_line_not_on_totals():
    lines = [line("books", "0.05", 1), line("books", "0.05", 1)]
    result = invoice_totals(lines, "A")
    # each line tax: 0.05 * 5% = 0.0025 -> 0.00
    assert result["tax"] == D("0.00")
    assert result["net"] == D("0.10")


def test_credit_partial_payment():
    result = invoice_totals([line("standard", "10.00", 1)], "A", credit=D("5.00"))
    # gross = 12.00
    assert result["gross"] == D("12.00")
    assert result["credit_used"] == D("5.00")
    assert result["total_due"] == D("7.00")
    assert result["credit_left"] == D("0.00")


def test_credit_more_than_gross():
    result = invoice_totals([line("food", "3.00", 1)], "A", credit=D("10.00"))
    assert result["credit_used"] == D("3.00")
    assert result["total_due"] == D("0.00")
    assert result["credit_left"] == D("7.00")


def test_zero_credit_default():
    result = invoice_totals([line("food", "3.00", 1)], "A")
    assert result["credit_used"] == D("0.00")
    assert result["total_due"] == D("3.00")
    assert result["credit_left"] == D("0.00")


def test_money_values_have_two_decimal_places():
    result = invoice_totals([line("food", "1", 1)], "B", credit=D("2"))
    for key in ("net", "tax", "gross", "credit_used", "total_due", "credit_left"):
        assert result[key].as_tuple().exponent == -2
    for value in result["tax_by_rate"].values():
        assert value.as_tuple().exponent == -2


def test_tax_by_rate_sums_multiple_lines_same_rate():
    lines = [line("standard", "10.00", 1), line("standard", "5.00", 2)]
    result = invoice_totals(lines, "A")
    assert result["tax_by_rate"] == {20: D("4.00")}


def test_invalid_region():
    with pytest.raises(ValueError):
        invoice_totals([], "C")


def test_invalid_category():
    with pytest.raises(ValueError):
        invoice_totals([line("toys")], "A")


@pytest.mark.parametrize("qty", [0, -1, 1.5, True, False])
def test_invalid_qty(qty):
    with pytest.raises(ValueError):
        invoice_totals([line(qty=qty)], "A")


def test_negative_unit_price():
    with pytest.raises(ValueError):
        invoice_totals([line(unit_price="-1.00")], "A")


@pytest.mark.parametrize("pct", ["-0.01", "100.01"])
def test_discount_out_of_range(pct):
    with pytest.raises(ValueError):
        invoice_totals([line(discount_pct=pct)], "A")


def test_discount_bounds_inclusive():
    assert invoice_totals([line("food", "10.00", 1, discount_pct="0")], "A")["net"] == D("10.00")
    assert invoice_totals([line("food", "10.00", 1, discount_pct="100")], "A")["net"] == D("0.00")


def test_negative_credit():
    with pytest.raises(ValueError):
        invoice_totals([], "A", credit=D("-1"))
