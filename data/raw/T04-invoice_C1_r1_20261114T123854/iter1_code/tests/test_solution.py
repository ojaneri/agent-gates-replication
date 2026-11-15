from decimal import Decimal

import pytest

from solution import invoice_totals

D = Decimal


def line(category="books", unit_price="10.00", qty=1, discount=None):
    item = {"sku": "X", "category": category, "unit_price": D(unit_price), "qty": qty}
    if discount is not None:
        item["discount_pct"] = D(discount)
    return item


def assert_cents(value):
    assert isinstance(value, Decimal)
    assert value == value.quantize(D("0.01"))
    assert value.as_tuple().exponent == -2


def check_money_fields(result):
    for key in ("net", "tax", "gross", "credit_used", "total_due", "credit_left"):
        assert_cents(result[key])
    for value in result["tax_by_rate"].values():
        assert_cents(value)


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
    check_money_fields(result)


def test_mixed_lines_region_a():
    lines = [
        line("books", "10.00", 1),
        line("standard", "100.00", 1, "10"),
    ]
    result = invoice_totals(lines, "A")
    assert result["net"] == D("100.00")
    assert result["tax"] == D("18.50")
    assert result["gross"] == D("118.50")
    assert result["credit_used"] == D("0.00")
    assert result["total_due"] == D("118.50")
    assert result["credit_left"] == D("0.00")
    assert result["tax_by_rate"] == {5: D("0.50"), 20: D("18.00")}
    check_money_fields(result)


def test_region_b_rates():
    result = invoice_totals([line("food", "100.00"), line("books", "100.00"), line("standard", "100.00")], "B")
    assert result["tax_by_rate"] == {7: D("14.00"), 15: D("15.00")}
    assert result["tax"] == D("29.00")
    assert result["net"] == D("300.00")


def test_zero_rate_included_when_present():
    result = invoice_totals([line("food", "50.00")], "A")
    assert result["tax_by_rate"] == {0: D("0.00")}
    assert result["tax"] == D("0.00")


def test_rates_absent_from_lines_not_included():
    result = invoice_totals([line("books", "10.00")], "A")
    assert list(result["tax_by_rate"].keys()) == [5]


def test_unknown_rate_key_not_present_for_region_b_food():
    result = invoice_totals([line("food", "10.00")], "B")
    assert result["tax_by_rate"] == {7: D("0.70")}


def test_line_discount_applies():
    result = invoice_totals([line("food", "200.00", 1, "25")], "A")
    assert result["net"] == D("150.00")


def test_discount_zero_and_hundred_allowed():
    free = invoice_totals([line("books", "10.00", 1, "100")], "A")
    assert free["net"] == D("0.00")
    full = invoice_totals([line("books", "10.00", 1, "0")], "A")
    assert full["net"] == D("10.00")


def test_default_discount_is_zero():
    result = invoice_totals([{"sku": "X", "category": "food", "unit_price": D("3.00"), "qty": 2}], "A")
    assert result["net"] == D("6.00")


def test_bulk_discount_applies_to_standard_at_ten():
    result = invoice_totals([line("standard", "100.00", 10)], "A")
    # 1000 * 0.95 = 950.00, tax 20% = 190.00
    assert result["net"] == D("950.00")
    assert result["tax"] == D("190.00")


def test_bulk_discount_not_below_ten():
    result = invoice_totals([line("standard", "100.00", 9)], "A")
    assert result["net"] == D("900.00")


def test_bulk_discount_only_for_standard():
    result = invoice_totals([line("food", "100.00", 10), line("books", "100.00", 10)], "A")
    assert result["net"] == D("2000.00")


def test_bulk_discount_stacks_multiplicatively_with_line_discount():
    result = invoice_totals([line("standard", "100.00", 10, "10")], "A")
    # 1000 * 0.9 = 900, * 0.95 = 855.00 (not 850.00)
    assert result["net"] == D("855.00")
    assert result["tax"] == D("171.00")


def test_line_net_rounded_half_up_before_tax():
    result = invoice_totals([line("standard", "0.01", 10)], "A")
    # 0.01 * 10 = 0.10, * 0.95 = 0.095 -> ROUND_HALF_UP -> 0.10
    assert result["net"] == D("0.10")
    # tax 20% of 0.10 = 0.02
    assert result["tax"] == D("0.02")


def test_rounding_half_up_on_tax():
    # 0.10 * 5% = 0.005 -> 0.01
    result = invoice_totals([line("books", "0.10", 1)], "A")
    assert result["tax"] == D("0.01")


def test_rounding_is_per_line_not_on_totals():
    lines = [line("books", "0.10", 1), line("books", "0.10", 1)]
    result = invoice_totals(lines, "A")
    # each line tax rounds to 0.01 -> total 0.02 (total-level rounding would give 0.01)
    assert result["tax"] == D("0.02")
    assert result["tax_by_rate"] == {5: D("0.02")}


def test_totals_sum_of_line_values():
    lines = [line("food", "1.01", 3), line("standard", "2.49", 2)]
    result = invoice_totals(lines, "B")
    assert result["net"] == D("3.03") + D("4.98")
    assert result["gross"] == result["net"] + result["tax"]


def test_credit_partial():
    result = invoice_totals([line("books", "100.00")], "A", D("20"))
    assert result["gross"] == D("105.00")
    assert result["credit_used"] == D("20.00")
    assert result["total_due"] == D("85.00")
    assert result["credit_left"] == D("0.00")


def test_credit_covers_all_and_leaves_remainder():
    result = invoice_totals([line("books", "10.00")], "A", D("200"))
    assert result["gross"] == D("10.50")
    assert result["credit_used"] == D("10.50")
    assert result["total_due"] == D("0.00")
    assert result["credit_left"] == D("189.50")


def test_credit_exactly_gross():
    result = invoice_totals([line("books", "10.00")], "A", D("10.50"))
    assert result["total_due"] == D("0.00")
    assert result["credit_left"] == D("0.00")


def test_credit_defaults_to_zero():
    result = invoice_totals([line("books", "10.00")], "A")
    assert result["credit_used"] == D("0.00")
    assert result["credit_left"] == D("0.00")


def test_int_inputs_accepted():
    result = invoice_totals([{"sku": "X", "category": "books", "unit_price": 10, "qty": 2}], "A", 0)
    assert result["net"] == D("20.00")


def test_unknown_region_raises():
    with pytest.raises(ValueError):
        invoice_totals([], "C")


def test_unknown_category_raises():
    with pytest.raises(ValueError):
        invoice_totals([line("toys")], "A")


def test_category_checked_per_region():
    # "food" is valid for both regions; an unknown category is always rejected
    with pytest.raises(ValueError):
        invoice_totals([line("Food")], "B")


@pytest.mark.parametrize("qty", [0, -1, 1.5, "2", None])
def test_invalid_qty_raises(qty):
    item = line()
    item["qty"] = qty
    with pytest.raises(ValueError):
        invoice_totals([item], "A")


def test_bool_qty_rejected():
    item = line()
    item["qty"] = True
    with pytest.raises(ValueError):
        invoice_totals([item], "A")


def test_negative_unit_price_raises():
    with pytest.raises(ValueError):
        invoice_totals([line(unit_price="-0.01")], "A")


def test_zero_unit_price_allowed():
    result = invoice_totals([line(unit_price="0")], "A")
    assert result["net"] == D("0.00")


@pytest.mark.parametrize("pct", ["-0.1", "100.01", "101"])
def test_discount_out_of_range_raises(pct):
    with pytest.raises(ValueError):
        invoice_totals([line(discount=pct)], "A")


def test_negative_credit_raises():
    with pytest.raises(ValueError):
        invoice_totals([], "A", D("-1"))


def test_float_input_converted():
    result = invoice_totals([{"sku": "X", "category": "books", "unit_price": 1.5, "qty": 2}], "A")
    assert result["net"] == D("3.00")
