from decimal import Decimal

import pytest

from solution import invoice_totals

D = Decimal


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


def money(result):
    """Return every money value as a string so the scale (2 dp) is checked too."""
    out = {k: str(v) for k, v in result.items() if k != "tax_by_rate"}
    out["tax_by_rate"] = {k: str(v) for k, v in result["tax_by_rate"].items()}
    return out


# ---------- worked examples and basic totals ----------

def test_example_region_a_mixed_categories():
    lines = [
        line("food", "1.00", 3),
        line("books", "10.00", 1),
        line("standard", "20.00", 1),
    ]
    result = invoice_totals(lines, "A")
    assert money(result) == {
        "net": "33.00",
        "tax": "4.50",
        "gross": "37.50",
        "credit_used": "0.00",
        "total_due": "37.50",
        "credit_left": "0.00",
        "tax_by_rate": {0: "0.00", 5: "0.50", 20: "4.00"},
    }


def test_region_b_rates():
    lines = [
        line("standard", "100.00", 1),
        line("food", "10.00", 1),
        line("books", "10.00", 1),
    ]
    result = invoice_totals(lines, "B")
    assert money(result) == {
        "net": "120.00",
        "tax": "16.40",
        "gross": "136.40",
        "credit_used": "0.00",
        "total_due": "136.40",
        "credit_left": "0.00",
        "tax_by_rate": {7: "1.40", 15: "15.00"},
    }


def test_region_b_food_and_books_share_rate_7_key():
    result = invoice_totals([line("food", "10.00"), line("books", "10.00")], "B")
    assert result["tax_by_rate"] == {7: D("1.40")}
    assert str(result["tax"]) == "1.40"


def test_region_a_standard_rate_is_20():
    result = invoice_totals([line("standard", "50.00")], "A")
    assert str(result["tax"]) == "10.00"
    assert result["tax_by_rate"] == {20: D("10.00")}


def test_region_b_standard_rate_is_15_not_20():
    result = invoice_totals([line("standard", "50.00")], "B")
    assert str(result["tax"]) == "7.50"
    assert result["tax_by_rate"] == {15: D("7.50")}


def test_zero_rate_line_is_included_in_tax_by_rate_with_zero_value():
    result = invoice_totals([line("food", "5.00")], "A")
    assert result["tax_by_rate"] == {0: D("0.00")}
    assert str(result["tax_by_rate"][0]) == "0.00"


def test_rates_not_present_are_omitted():
    result = invoice_totals([line("books", "5.00")], "A")
    assert set(result["tax_by_rate"]) == {5}


def test_all_seven_output_keys_present():
    result = invoice_totals([line("books", "1.00")], "A")
    assert set(result) == {
        "net", "tax", "gross", "credit_used", "total_due", "credit_left", "tax_by_rate",
    }


def test_gross_is_net_plus_tax():
    result = invoice_totals([line("standard", "33.33", 2), line("books", "7.77", 3)], "A")
    assert result["gross"] == result["net"] + result["tax"]


def test_multiple_lines_of_same_rate_sum_in_tax_by_rate():
    lines = [line("books", "10.00"), line("books", "20.00")]
    result = invoice_totals(lines, "A")
    assert result["tax_by_rate"] == {5: D("1.50")}
    assert str(result["tax"]) == "1.50"


def test_unit_price_times_qty_is_used():
    result = invoice_totals([line("standard", "2.50", 4)], "A")
    assert str(result["net"]) == "10.00"
    assert str(result["tax"]) == "2.00"


def test_empty_lines_gives_zeros_and_empty_tax_by_rate():
    result = invoice_totals([], "A")
    assert money(result) == {
        "net": "0.00",
        "tax": "0.00",
        "gross": "0.00",
        "credit_used": "0.00",
        "total_due": "0.00",
        "credit_left": "0.00",
        "tax_by_rate": {},
    }


def test_empty_lines_with_credit_leaves_credit_untouched():
    result = invoice_totals([], "B", D("5"))
    assert str(result["credit_used"]) == "0.00"
    assert str(result["total_due"]) == "0.00"
    assert str(result["credit_left"]) == "5.00"


# ---------- line discounts ----------

def test_line_discount_reduces_net():
    result = invoice_totals([line("standard", "100.00", 1, "10")], "A")
    assert str(result["net"]) == "90.00"
    assert str(result["tax"]) == "18.00"


def test_discount_zero_is_allowed_and_changes_nothing():
    result = invoice_totals([line("books", "10.00", 1, "0")], "A")
    assert str(result["net"]) == "10.00"


def test_discount_hundred_is_allowed_and_gives_zero_line():
    result = invoice_totals([line("standard", "10.00", 1, "100")], "A")
    assert str(result["net"]) == "0.00"
    assert str(result["tax"]) == "0.00"
    assert result["tax_by_rate"] == {20: D("0.00")}


def test_discount_applies_per_line_default_is_zero():
    result = invoice_totals([line("food", "10.00", 1)], "A")
    assert str(result["net"]) == "10.00"


def test_discount_pct_fractional_value():
    result = invoice_totals([line("food", "10.00", 1, "12.5")], "A")
    assert str(result["net"]) == "8.75"


# ---------- bulk discount ----------

def test_bulk_discount_applies_to_standard_at_qty_10():
    result = invoice_totals([line("standard", "10.00", 10)], "A")
    assert str(result["net"]) == "95.00"
    assert str(result["tax"]) == "19.00"


def test_bulk_discount_not_applied_at_qty_9():
    result = invoice_totals([line("standard", "10.00", 9)], "A")
    assert str(result["net"]) == "90.00"
    assert str(result["tax"]) == "18.00"


def test_bulk_discount_not_applied_to_food_or_books():
    lines = [line("food", "10.00", 10), line("books", "10.00", 10)]
    result = invoice_totals(lines, "A")
    assert str(result["net"]) == "200.00"


def test_bulk_discount_stacks_multiplicatively_with_line_discount():
    result = invoice_totals([line("standard", "100.00", 10, "10")], "A")
    assert str(result["net"]) == "855.00"
    assert str(result["tax"]) == "171.00"
    assert str(result["gross"]) == "1026.00"


def test_bulk_discount_multiplicative_not_additive():
    # 10% then 5% leaves 85.5%, not 85%.
    result = invoice_totals([line("standard", "1000.00", 10, "10")], "A")
    assert str(result["net"]) == "8550.00"


def test_bulk_discount_on_large_qty():
    result = invoice_totals([line("standard", "1.00", 100)], "B")
    assert str(result["net"]) == "95.00"
    assert str(result["tax"]) == "14.25"


# ---------- rounding ----------

def test_line_net_rounds_half_up():
    # 0.05 * (1 - 0.5) = 0.025 -> 0.03 (half up, not half even)
    result = invoice_totals([line("food", "0.05", 1, "50")], "A")
    assert str(result["net"]) == "0.03"


def test_line_tax_rounds_half_up():
    # 0.10 * 5% = 0.005 -> 0.01 (half up, not half even)
    result = invoice_totals([line("books", "0.10", 1)], "A")
    assert str(result["tax"]) == "0.01"
    assert result["tax_by_rate"] == {5: D("0.01")}


def test_rounding_happens_per_line_not_on_totals():
    # Each line tax 0.005 -> 0.01 each, total 0.02 (not round(0.01) of total 0.01).
    lines = [line("books", "0.10", 1), line("books", "0.10", 1)]
    result = invoice_totals(lines, "A")
    assert str(result["tax"]) == "0.02"


def test_line_net_rounded_before_tax_is_computed():
    # Net 0.025 rounds to 0.03 first; tax on 0.03 at 5% = 0.0015 -> 0.00.
    # Tax on unrounded 0.025 would be 0.00125 -> 0.00 too, so use a sharper case:
    # net 0.10 * 0.95 bulk = 0.095 -> 0.10 ; tax 0.10 * 5% = 0.005 -> 0.01.
    lines = [line("books", "0.10", 1, "5")]
    result = invoice_totals(lines, "A")
    assert str(result["net"]) == "0.10"
    assert str(result["tax"]) == "0.01"


def test_bulk_net_rounding_is_half_up():
    # standard, qty 10, unit 0.01: 0.10 * 0.95 = 0.095 -> 0.10 (half up)
    result = invoice_totals([line("standard", "0.01", 10)], "A")
    assert str(result["net"]) == "0.10"


def test_net_and_tax_always_two_decimal_places():
    result = invoice_totals([line("standard", "3.33", 3, "7")], "B")
    for key in ("net", "tax", "gross", "credit_used", "total_due", "credit_left"):
        assert len(str(result[key]).split(".")[1]) == 2, key
    for value in result["tax_by_rate"].values():
        assert len(str(value).split(".")[1]) == 2


# ---------- credit ----------

BASE = [line("food", "1.00", 3), line("books", "10.00", 1), line("standard", "20.00", 1)]


def test_no_credit_default():
    result = invoice_totals(BASE, "A")
    assert str(result["credit_used"]) == "0.00"
    assert str(result["total_due"]) == "37.50"
    assert str(result["credit_left"]) == "0.00"


def test_credit_partly_covers_gross():
    result = invoice_totals(BASE, "A", D("10"))
    assert str(result["credit_used"]) == "10.00"
    assert str(result["total_due"]) == "27.50"
    assert str(result["credit_left"]) == "0.00"


def test_credit_exactly_equal_to_gross():
    result = invoice_totals(BASE, "A", D("37.50"))
    assert str(result["credit_used"]) == "37.50"
    assert str(result["total_due"]) == "0.00"
    assert str(result["credit_left"]) == "0.00"


def test_credit_more_than_gross_leaves_remainder():
    result = invoice_totals(BASE, "A", D("50"))
    assert str(result["credit_used"]) == "37.50"
    assert str(result["total_due"]) == "0.00"
    assert str(result["credit_left"]) == "12.50"


def test_credit_zero_explicit():
    result = invoice_totals(BASE, "A", D("0"))
    assert str(result["total_due"]) == "37.50"


def test_credit_used_plus_total_due_equals_gross():
    result = invoice_totals(BASE, "A", D("12.34"))
    assert result["credit_used"] + result["total_due"] == result["gross"]


def test_credit_left_plus_used_equals_credit():
    result = invoice_totals(BASE, "A", D("12.34"))
    assert result["credit_used"] + result["credit_left"] == D("12.34")


def test_credit_with_extra_decimals_is_rounded_for_output():
    result = invoice_totals(BASE, "A", D("50.004"))
    assert str(result["credit_left"]) == "12.50"


# ---------- validation: region, category, qty, price, discount, credit ----------

@pytest.mark.parametrize("region", ["C", "a", "", None])
def test_unknown_region_raises(region):
    with pytest.raises(ValueError):
        invoice_totals([line()], region)


@pytest.mark.parametrize("category", ["toys", "Food", "", "standard "])
def test_unknown_category_raises(category):
    with pytest.raises(ValueError):
        invoice_totals([line(category)], "A")


@pytest.mark.parametrize("qty", [0, -1, True, False, 1.0, 2.5, "2", None])
def test_invalid_qty_raises(qty):
    item = line()
    item["qty"] = qty
    with pytest.raises(ValueError):
        invoice_totals([item], "A")


def test_qty_one_is_valid():
    result = invoice_totals([line("food", "2.00", 1)], "A")
    assert str(result["net"]) == "2.00"


@pytest.mark.parametrize("price", ["-0.01", "-5"])
def test_negative_unit_price_raises(price):
    with pytest.raises(ValueError):
        invoice_totals([line("food", price)], "A")


def test_zero_unit_price_is_valid():
    result = invoice_totals([line("food", "0")], "A")
    assert str(result["net"]) == "0.00"


@pytest.mark.parametrize("pct", ["-0.01", "100.01", "-1", "101"])
def test_discount_outside_range_raises(pct):
    with pytest.raises(ValueError):
        invoice_totals([line("food", "1.00", 1, pct)], "A")


@pytest.mark.parametrize("pct", ["0", "100", "0.5", "99.99"])
def test_discount_boundaries_and_inside_are_valid(pct):
    result = invoice_totals([line("food", "1.00", 1, pct)], "A")
    assert result["net"] >= 0


def test_negative_credit_raises():
    with pytest.raises(ValueError):
        invoice_totals(BASE, "A", D("-0.01"))


def test_negative_credit_raises_even_with_no_lines():
    with pytest.raises(ValueError):
        invoice_totals([], "A", D("-1"))


def test_validation_error_on_later_line_is_raised():
    bad = line("toys")
    with pytest.raises(ValueError):
        invoice_totals([line("food"), bad], "A")


def test_bool_qty_rejected_even_when_it_is_true_for_one():
    item = line()
    item["qty"] = True
    with pytest.raises(ValueError):
        invoice_totals([item], "B")


def test_lines_are_not_modified():
    lines = [line("standard", "10.00", 10, "10")]
    snapshot = dict(lines[0])
    invoice_totals(lines, "A")
    assert lines[0] == snapshot
