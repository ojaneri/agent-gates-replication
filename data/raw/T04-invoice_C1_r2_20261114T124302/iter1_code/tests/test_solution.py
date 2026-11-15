from decimal import Decimal

import pytest

from solution import invoice_totals

D = Decimal


def line(category, unit_price, qty, discount=None):
    item = {"sku": "X", "category": category, "unit_price": D(unit_price), "qty": qty}
    if discount is not None:
        item["discount_pct"] = D(discount)
    return item


def test_empty_lines_gives_zeros():
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


def test_zero_rate_food_line_is_included_in_tax_by_rate():
    result = invoice_totals([line("food", "10.00", 2)], "A")
    assert result["net"] == D("20.00")
    assert result["tax"] == D("0.00")
    assert result["gross"] == D("20.00")
    assert result["tax_by_rate"] == {0: D("0.00")}


def test_standard_line_region_a_tax_20_percent():
    result = invoice_totals([line("standard", "10.00", 1)], "A")
    assert result["net"] == D("10.00")
    assert result["tax"] == D("2.00")
    assert result["gross"] == D("12.00")
    assert result["tax_by_rate"] == {20: D("2.00")}


def test_region_b_rates():
    result = invoice_totals(
        [line("food", "100.00", 1), line("books", "100.00", 1), line("standard", "100.00", 1)],
        "B",
    )
    assert result["tax_by_rate"] == {7: D("14.00"), 15: D("15.00")}
    assert result["tax"] == D("29.00")
    assert result["gross"] == D("329.00")


def test_bulk_discount_applies_on_top_of_line_discount():
    # 10 * 1.00 = 10.00; minus 10% = 9.00; minus 5% = 8.55
    result = invoice_totals([line("standard", "1.00", 10, "10")], "A")
    assert result["net"] == D("8.55")
    assert result["tax"] == D("1.71")
    assert result["gross"] == D("10.26")


def test_bulk_discount_without_line_discount():
    # 10 * 10.00 = 100.00 -> 95.00
    result = invoice_totals([line("standard", "10.00", 10)], "A")
    assert result["net"] == D("95.00")
    assert result["tax"] == D("19.00")


def test_no_bulk_discount_below_ten():
    result = invoice_totals([line("standard", "10.00", 9)], "A")
    assert result["net"] == D("90.00")
    assert result["tax"] == D("18.00")


def test_bulk_discount_only_for_standard_category():
    result = invoice_totals([line("books", "1.00", 10)], "A")
    assert result["net"] == D("10.00")
    assert result["tax"] == D("0.50")


def test_line_discount_without_bulk():
    result = invoice_totals([line("books", "20.00", 1, "25")], "A")
    assert result["net"] == D("15.00")
    assert result["tax"] == D("0.75")


def test_discount_zero_and_hundred_allowed():
    result = invoice_totals([line("standard", "10.00", 1, "0"), line("books", "10.00", 1, "100")], "A")
    assert result["net"] == D("10.00")
    assert result["tax"] == D("2.00")
    assert result["tax_by_rate"] == {5: D("0.00"), 20: D("2.00")}


def test_rounding_half_up_per_line():
    # 0.50 * 5% = 0.025 -> 0.03
    result = invoice_totals([line("books", "0.50", 1)], "A")
    assert result["tax"] == D("0.03")


def test_rounding_is_per_line_not_on_totals():
    # two lines each tax 0.025 -> 0.03 each, total 0.06 (not 0.05)
    result = invoice_totals([line("books", "0.50", 1), line("books", "0.50", 1)], "A")
    assert result["net"] == D("1.00")
    assert result["tax"] == D("0.06")
    assert result["tax_by_rate"] == {5: D("0.06")}


def test_line_net_rounded_before_tax():
    # 0.05 * 0.90 (10% off) = 0.045 -> net 0.05 (half up); tax 5% of 0.05 = 0.0025 -> 0.00
    result = invoice_totals([line("books", "0.05", 1, "10")], "A")
    assert result["net"] == D("0.05")
    assert result["tax"] == D("0.00")


def test_tax_by_rate_aggregates_same_rate():
    result = invoice_totals(
        [line("standard", "10.00", 1), line("standard", "5.00", 1), line("food", "3.00", 1)],
        "A",
    )
    assert result["tax_by_rate"] == {20: D("3.00"), 0: D("0.00")}
    assert result["tax"] == D("3.00")


def test_credit_partial():
    result = invoice_totals([line("standard", "10.00", 1)], "A", D("5.00"))
    assert result["credit_used"] == D("5.00")
    assert result["total_due"] == D("7.00")
    assert result["credit_left"] == D("0.00")


def test_credit_exceeds_gross():
    result = invoice_totals([line("standard", "10.00", 1)], "A", D("20"))
    assert result["credit_used"] == D("12.00")
    assert result["total_due"] == D("0.00")
    assert result["credit_left"] == D("8.00")


def test_credit_default_is_zero():
    result = invoice_totals([line("food", "1.00", 1)], "A")
    assert result["credit_used"] == D("0.00")
    assert result["total_due"] == D("1.00")
    assert result["credit_left"] == D("0.00")


def test_output_has_two_decimal_places():
    result = invoice_totals([line("food", "10", 1)], "A", D("3"))
    for key in ("net", "tax", "gross", "credit_used", "total_due", "credit_left"):
        assert result[key].as_tuple().exponent == -2, key
    assert str(result["net"]) == "10.00"
    assert str(result["credit_used"]) == "3.00"
    assert str(result["total_due"]) == "7.00"
    assert str(result["credit_left"]) == "0.00"
    assert str(result["tax_by_rate"][0]) == "0.00"


def test_credit_with_extra_decimals_is_quantized():
    result = invoice_totals([line("standard", "10.00", 1)], "A", D("1.234"))
    assert result["credit_used"] == D("1.23")
    assert result["credit_left"] == D("0.00")
    assert result["total_due"] == D("10.77")


@pytest.mark.parametrize("region", ["C", "a", "", None])
def test_unknown_region_raises(region):
    with pytest.raises(ValueError):
        invoice_totals([], region)


def test_unknown_category_raises():
    with pytest.raises(ValueError):
        invoice_totals([line("toys", "1.00", 1)], "A")


@pytest.mark.parametrize("qty", [0, -1, True, False, 1.0, "2", None])
def test_invalid_qty_raises(qty):
    item = {"sku": "X", "category": "food", "unit_price": D("1.00"), "qty": qty}
    with pytest.raises(ValueError):
        invoice_totals([item], "A")


def test_negative_unit_price_raises():
    with pytest.raises(ValueError):
        invoice_totals([line("food", "-1.00", 1)], "A")


def test_zero_unit_price_allowed():
    result = invoice_totals([line("food", "0.00", 1)], "A")
    assert result["gross"] == D("0.00")


@pytest.mark.parametrize("discount", ["-0.01", "100.01", "150"])
def test_discount_out_of_range_raises(discount):
    with pytest.raises(ValueError):
        invoice_totals([line("food", "1.00", 1, discount)], "A")


def test_negative_credit_raises():
    with pytest.raises(ValueError):
        invoice_totals([], "A", D("-0.01"))
