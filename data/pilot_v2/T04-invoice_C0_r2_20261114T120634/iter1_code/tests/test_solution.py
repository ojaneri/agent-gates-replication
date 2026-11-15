from decimal import Decimal

import pytest

from solution import invoice_totals

D = Decimal


def line(category="food", unit_price="10", qty=1, discount_pct=None):
    item = {"sku": "X", "category": category, "unit_price": D(unit_price), "qty": qty}
    if discount_pct is not None:
        item["discount_pct"] = D(discount_pct)
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


def test_region_a_totals_and_tax_by_rate():
    lines = [
        line("food", "100", 1),      # 0%
        line("books", "100", 1),     # 5%
        line("standard", "100", 1),  # 20%
    ]
    result = invoice_totals(lines, "A")
    assert result["net"] == D("300.00")
    assert result["tax"] == D("25.00")
    assert result["gross"] == D("325.00")
    assert result["tax_by_rate"] == {0: D("0.00"), 5: D("5.00"), 20: D("20.00")}


def test_region_b_rates():
    lines = [line("food", "100", 1), line("books", "100", 1), line("standard", "100", 1)]
    result = invoice_totals(lines, "B")
    assert result["tax_by_rate"] == {7: D("14.00"), 15: D("15.00")}
    assert result["tax"] == D("29.00")


def test_rate_not_on_any_line_is_omitted():
    result = invoice_totals([line("books", "100", 1)], "A")
    assert result["tax_by_rate"] == {5: D("5.00")}


def test_zero_rate_line_is_included_with_zero():
    result = invoice_totals([line("food", "50", 2)], "A")
    assert result["tax_by_rate"] == {0: D("0.00")}


def test_line_discount_applies():
    result = invoice_totals([line("food", "10", 2, discount_pct="25")], "A")
    assert result["net"] == D("15.00")


def test_bulk_discount_applies_to_standard_qty_10():
    result = invoice_totals([line("standard", "10", 10)], "A")
    assert result["net"] == D("95.00")
    assert result["tax"] == D("19.00")


def test_bulk_discount_not_applied_below_10():
    result = invoice_totals([line("standard", "10", 9)], "A")
    assert result["net"] == D("90.00")


def test_bulk_discount_not_applied_to_other_categories():
    result = invoice_totals([line("food", "10", 10), line("books", "10", 10)], "A")
    assert result["net"] == D("200.00")


def test_bulk_and_line_discount_are_multiplicative():
    # 100 * 0.90 = 90, then * 0.95 = 85.50 (not 85.00)
    result = invoice_totals([line("standard", "10", 10, discount_pct="10")], "A")
    assert result["net"] == D("85.50")
    assert result["tax"] == D("17.10")


def test_rounding_is_per_line_half_up():
    # Line net 1.005 -> 1.01 (half up); tax 0.
    result = invoice_totals([line("food", "1.005", 1)], "A")
    assert result["net"] == D("1.01")


def test_line_tax_rounded_half_up_per_line():
    # Net 0.30, tax 5% = 0.015 -> 0.02
    result = invoice_totals([line("books", "0.10", 3)], "A")
    assert result["tax"] == D("0.02")
    assert result["tax_by_rate"] == {5: D("0.02")}


def test_totals_are_sums_of_rounded_line_values():
    # Each line tax is 0.02; sum of lines is 0.04, not round(0.03) = 0.03.
    lines = [line("books", "0.10", 3), line("books", "0.10", 3)]
    result = invoice_totals(lines, "A")
    assert result["tax"] == D("0.04")
    assert result["net"] == D("0.60")


def test_credit_partial():
    result = invoice_totals([line("books", "100", 1)], "A", credit=D("30"))
    assert result["gross"] == D("105.00")
    assert result["credit_used"] == D("30.00")
    assert result["total_due"] == D("75.00")
    assert result["credit_left"] == D("0.00")


def test_credit_exceeds_gross():
    result = invoice_totals([line("food", "100", 1)], "A", credit=D("250"))
    assert result["credit_used"] == D("100.00")
    assert result["total_due"] == D("0.00")
    assert result["credit_left"] == D("150.00")


def test_credit_defaults_to_zero():
    result = invoice_totals([line("food", "100", 1)], "A")
    assert result["credit_used"] == D("0.00")
    assert result["total_due"] == D("100.00")
    assert result["credit_left"] == D("0.00")


def test_money_values_have_two_decimal_places():
    result = invoice_totals([line("food", "3", 1)], "A", credit=D("1"))
    for key in ("net", "tax", "gross", "credit_used", "total_due", "credit_left"):
        assert result[key] == result[key].quantize(D("0.01"))
        assert str(result[key]).split(".")[1].__len__() == 2
    assert str(result["net"]) == "3.00"


def test_discount_bounds_inclusive():
    assert invoice_totals([line("food", "10", 1, discount_pct="0")], "A")["net"] == D("10.00")
    assert invoice_totals([line("food", "10", 1, discount_pct="100")], "A")["net"] == D("0.00")


@pytest.mark.parametrize("region", ["C", "a", "", None])
def test_unknown_region_raises(region):
    with pytest.raises(ValueError):
        invoice_totals([line()], region)


@pytest.mark.parametrize("category", ["toys", "Food", ""])
def test_unknown_category_raises(category):
    with pytest.raises(ValueError):
        invoice_totals([line(category)], "A")


@pytest.mark.parametrize("qty", [0, -1, 1.0, True, "2"])
def test_invalid_qty_raises(qty):
    with pytest.raises(ValueError):
        invoice_totals([line(qty=qty)], "A")


def test_negative_unit_price_raises():
    with pytest.raises(ValueError):
        invoice_totals([line(unit_price="-0.01")], "A")


def test_zero_unit_price_allowed():
    assert invoice_totals([line(unit_price="0")], "A")["net"] == D("0.00")


@pytest.mark.parametrize("pct", ["-0.01", "100.01", "101"])
def test_discount_out_of_range_raises(pct):
    with pytest.raises(ValueError):
        invoice_totals([line(discount_pct=pct)], "A")


def test_negative_credit_raises():
    with pytest.raises(ValueError):
        invoice_totals([line()], "A", credit=D("-1"))
