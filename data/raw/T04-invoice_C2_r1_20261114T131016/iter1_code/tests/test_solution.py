from decimal import Decimal as D

import pytest

from solution import invoice_totals


def line(category="food", unit_price="1.00", qty=1, discount_pct=None):
    item = {
        "sku": "SKU",
        "category": category,
        "unit_price": D(unit_price),
        "qty": qty,
    }
    if discount_pct is not None:
        item["discount_pct"] = D(discount_pct)
    return item


def assert_two_dp(value):
    assert value.as_tuple().exponent == -2


def test_empty_lines_gives_zeros_and_empty_tax_by_rate():
    out = invoice_totals([], "A")
    assert out == {
        "net": D("0.00"),
        "tax": D("0.00"),
        "gross": D("0.00"),
        "credit_used": D("0.00"),
        "total_due": D("0.00"),
        "credit_left": D("0.00"),
        "tax_by_rate": {},
    }
    for key in ("net", "tax", "gross", "credit_used", "total_due", "credit_left"):
        assert str(out[key]) == "0.00"


def test_result_has_exactly_the_documented_keys():
    out = invoice_totals([line()], "A")
    assert set(out) == {
        "net", "tax", "gross", "credit_used", "total_due", "credit_left", "tax_by_rate",
    }


# Tax rates per region and category

@pytest.mark.parametrize(
    "region, category, unit, expected_tax",
    [
        ("A", "food", "100.00", "0.00"),
        ("A", "books", "100.00", "5.00"),
        ("A", "standard", "100.00", "20.00"),
        ("B", "food", "100.00", "7.00"),
        ("B", "books", "100.00", "7.00"),
        ("B", "standard", "100.00", "15.00"),
    ],
)
def test_tax_rate_per_region_and_category(region, category, unit, expected_tax):
    out = invoice_totals([line(category=category, unit_price=unit)], region)
    assert str(out["net"]) == "100.00"
    assert str(out["tax"]) == expected_tax
    assert str(out["gross"]) == str(D("100.00") + D(expected_tax))


def test_zero_rate_line_is_included_in_tax_by_rate_as_zero():
    out = invoice_totals([line(category="food", unit_price="4.00")], "A")
    assert out["tax_by_rate"] == {0: D("0.00")}
    assert str(out["tax_by_rate"][0]) == "0.00"


def test_rates_not_on_any_line_are_absent_from_tax_by_rate():
    out = invoice_totals([line(category="standard", unit_price="10.00")], "B")
    assert list(out["tax_by_rate"]) == [15]
    assert 7 not in out["tax_by_rate"]
    assert 0 not in out["tax_by_rate"]


def test_tax_by_rate_sums_lines_sharing_a_rate():
    lines = [
        line(category="books", unit_price="10.00", qty=2),
        line(category="books", unit_price="3.00", qty=1),
        line(category="standard", unit_price="50.00"),
    ]
    out = invoice_totals(lines, "A")
    # books: 20.00 + 3.00 = 23.00 net at 5% = 1.15
    assert str(out["tax_by_rate"][5]) == "1.15"
    assert str(out["tax_by_rate"][20]) == "10.00"
    assert set(out["tax_by_rate"]) == {5, 20}


# Line net and discounts

def test_line_discount_reduces_net():
    out = invoice_totals([line(category="food", unit_price="10.00", qty=3, discount_pct="10")], "A")
    assert str(out["net"]) == "27.00"


def test_full_discount_gives_zero_net_and_tax():
    out = invoice_totals([line(category="standard", unit_price="99.99", discount_pct="100")], "A")
    assert str(out["net"]) == "0.00"
    assert str(out["tax"]) == "0.00"


def test_zero_discount_is_accepted_and_changes_nothing():
    out = invoice_totals([line(category="food", unit_price="10.00", discount_pct="0")], "A")
    assert str(out["net"]) == "10.00"


def test_missing_discount_defaults_to_zero():
    out = invoice_totals([line(category="food", unit_price="10.00", qty=2)], "A")
    assert str(out["net"]) == "20.00"


def test_bulk_discount_applies_to_standard_at_ten_units():
    out = invoice_totals([line(category="standard", unit_price="10.00", qty=10)], "A")
    assert str(out["net"]) == "95.00"
    assert str(out["tax"]) == "19.00"


def test_bulk_discount_not_applied_at_nine_units():
    out = invoice_totals([line(category="standard", unit_price="10.00", qty=9)], "A")
    assert str(out["net"]) == "90.00"


def test_bulk_discount_applies_above_ten_units():
    out = invoice_totals([line(category="standard", unit_price="10.00", qty=11)], "A")
    assert str(out["net"]) == "104.50"


@pytest.mark.parametrize("category", ["food", "books"])
def test_bulk_discount_not_applied_to_food_or_books(category):
    out = invoice_totals([line(category=category, unit_price="10.00", qty=10)], "A")
    assert str(out["net"]) == "100.00"


def test_bulk_discount_stacks_multiplicatively_with_line_discount():
    out = invoice_totals(
        [line(category="standard", unit_price="100.00", qty=10, discount_pct="10")], "A"
    )
    # 1000 * 0.90 = 900, then * 0.95 = 855 (not 850)
    assert str(out["net"]) == "855.00"
    assert str(out["tax"]) == "171.00"
    assert str(out["gross"]) == "1026.00"


# Rounding

def test_books_tax_half_cent_rounds_up():
    # 0.10 * 5% = 0.005 -> 0.01
    out = invoice_totals([line(category="books", unit_price="0.10")], "A")
    assert str(out["tax"]) == "0.01"


def test_books_tax_of_point_three_rounds_up():
    # 0.30 * 5% = 0.015 -> 0.02
    out = invoice_totals([line(category="books", unit_price="0.30")], "A")
    assert str(out["tax"]) == "0.02"


def test_tax_rounding_is_per_line_not_on_totals():
    # Each line's tax is 0.005 -> 0.01, so the total tax is 0.02, not 0.01.
    lines = [
        line(category="books", unit_price="0.10"),
        line(category="books", unit_price="0.10"),
    ]
    out = invoice_totals(lines, "A")
    assert str(out["tax"]) == "0.02"
    assert str(out["tax_by_rate"][5]) == "0.02"


def test_line_net_is_rounded_to_cents_before_tax():
    # 10 * 0.11 = 1.10; bulk 1.10 * 0.95 = 1.045 -> net rounds half up to 1.05.
    # Tax is then computed on the rounded 1.05: 1.05 * 20% = 0.21.
    out = invoice_totals([line(category="standard", unit_price="0.11", qty=10)], "A")
    assert str(out["net"]) == "1.05"
    assert str(out["tax"]) == "0.21"


def test_line_net_rounding_half_up_not_bankers():
    # 0.25 * 1 with 10% discount = 0.225 -> 0.23 (half up; bankers would give 0.22)
    out = invoice_totals([line(category="food", unit_price="0.25", discount_pct="10")], "A")
    assert str(out["net"]) == "0.23"


def test_tax_half_up_not_bankers():
    # 0.50 at 5% = 0.025 -> 0.03 (bankers would give 0.02)
    out = invoice_totals([line(category="books", unit_price="0.50")], "A")
    assert str(out["tax"]) == "0.03"


def test_money_outputs_always_have_two_decimal_places():
    lines = [
        line(category="standard", unit_price="7", qty=10),
        line(category="books", unit_price="3"),
    ]
    out = invoice_totals(lines, "B", credit=D("5"))
    for key in ("net", "tax", "gross", "credit_used", "total_due", "credit_left"):
        assert_two_dp(out[key])
    for value in out["tax_by_rate"].values():
        assert_two_dp(value)


# Totals and the worked example

def test_mixed_invoice_totals():
    lines = [
        line(category="food", unit_price="2.50", qty=4),
        line(category="books", unit_price="10.00", qty=1),
        line(category="standard", unit_price="100.00", qty=10, discount_pct="10"),
    ]
    out = invoice_totals(lines, "A", credit=D("100"))
    assert str(out["net"]) == "875.00"
    assert str(out["tax"]) == "171.50"
    assert str(out["gross"]) == "1046.50"
    assert str(out["credit_used"]) == "100.00"
    assert str(out["total_due"]) == "946.50"
    assert str(out["credit_left"]) == "0.00"
    assert {k: str(v) for k, v in out["tax_by_rate"].items()} == {
        0: "0.00",
        5: "0.50",
        20: "171.00",
    }


def test_region_b_totals_without_credit():
    lines = [
        line(category="food", unit_price="10.00"),
        line(category="standard", unit_price="20.00"),
    ]
    out = invoice_totals(lines, "B")
    assert str(out["net"]) == "30.00"
    assert str(out["tax"]) == "3.70"
    assert str(out["gross"]) == "33.70"
    assert str(out["credit_used"]) == "0.00"
    assert str(out["total_due"]) == "33.70"
    assert str(out["credit_left"]) == "0.00"


# Credit

def test_credit_smaller_than_gross_is_fully_used():
    out = invoice_totals([line(category="standard", unit_price="100.00")], "A", credit=D("50"))
    # gross 120.00
    assert str(out["gross"]) == "120.00"
    assert str(out["credit_used"]) == "50.00"
    assert str(out["total_due"]) == "70.00"
    assert str(out["credit_left"]) == "0.00"


def test_credit_larger_than_gross_is_capped_at_gross():
    out = invoice_totals([line(category="standard", unit_price="100.00")], "A", credit=D("200"))
    assert str(out["credit_used"]) == "120.00"
    assert str(out["total_due"]) == "0.00"
    assert str(out["credit_left"]) == "80.00"


def test_credit_equal_to_gross_leaves_nothing_due_or_left():
    out = invoice_totals([line(category="standard", unit_price="100.00")], "A", credit=D("120"))
    assert str(out["credit_used"]) == "120.00"
    assert str(out["total_due"]) == "0.00"
    assert str(out["credit_left"]) == "0.00"


def test_zero_credit_default_uses_nothing():
    out = invoice_totals([line(category="standard", unit_price="100.00")], "A")
    assert str(out["credit_used"]) == "0.00"
    assert str(out["total_due"]) == "120.00"
    assert str(out["credit_left"]) == "0.00"


def test_credit_with_empty_lines_is_left_untouched():
    out = invoice_totals([], "A", credit=D("12.50"))
    assert str(out["credit_used"]) == "0.00"
    assert str(out["total_due"]) == "0.00"
    assert str(out["credit_left"]) == "12.50"


def test_explicit_zero_credit_is_accepted():
    out = invoice_totals([line(category="food", unit_price="5.00")], "A", credit=D("0"))
    assert str(out["credit_left"]) == "0.00"


# Validation errors

def test_unknown_region_raises():
    with pytest.raises(ValueError):
        invoice_totals([line()], "C")


def test_unknown_region_raises_even_with_no_lines():
    with pytest.raises(ValueError):
        invoice_totals([], "")


def test_unknown_category_raises():
    with pytest.raises(ValueError):
        invoice_totals([line(category="toys")], "A")


def test_category_names_are_case_sensitive():
    with pytest.raises(ValueError):
        invoice_totals([line(category="Food")], "A")


@pytest.mark.parametrize("qty", [0, -1, 1.5, "2", None])
def test_invalid_qty_raises(qty):
    with pytest.raises(ValueError):
        invoice_totals([line(qty=qty)], "A")


def test_bool_qty_is_rejected():
    with pytest.raises(ValueError):
        invoice_totals([line(qty=True)], "A")


def test_qty_of_one_is_accepted():
    out = invoice_totals([line(category="food", unit_price="3.00", qty=1)], "A")
    assert str(out["net"]) == "3.00"


def test_negative_unit_price_raises():
    with pytest.raises(ValueError):
        invoice_totals([line(unit_price="-0.01")], "A")


def test_zero_unit_price_is_accepted():
    out = invoice_totals([line(unit_price="0")], "A")
    assert str(out["net"]) == "0.00"


@pytest.mark.parametrize("pct", ["-0.01", "100.01", "-5", "150"])
def test_discount_outside_range_raises(pct):
    with pytest.raises(ValueError):
        invoice_totals([line(discount_pct=pct)], "A")


@pytest.mark.parametrize("pct", ["0", "100", "99.99"])
def test_discount_at_or_inside_bounds_is_accepted(pct):
    invoice_totals([line(discount_pct=pct)], "A")


def test_negative_credit_raises():
    with pytest.raises(ValueError):
        invoice_totals([line()], "A", credit=D("-0.01"))


def test_negative_credit_raises_with_no_lines():
    with pytest.raises(ValueError):
        invoice_totals([], "A", credit=D("-1"))


def test_invalid_line_anywhere_in_list_raises():
    lines = [line(category="food"), line(qty=0)]
    with pytest.raises(ValueError):
        invoice_totals(lines, "A")
