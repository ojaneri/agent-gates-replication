from decimal import Decimal

import pytest

from solution import invoice_totals

D = Decimal


def line(category="food", unit_price="1.00", qty=1, **extra):
    d = {"sku": "X", "category": category, "unit_price": D(unit_price), "qty": qty}
    d.update(extra)
    return d


# --- basic totals and credit -------------------------------------------------

def test_example_mixed_lines_region_a_with_partial_credit():
    lines = [
        line("food", "1.00", 3),
        line("books", "10.00", 1),
        line("standard", "20.00", 1),
    ]
    r = invoice_totals(lines, "A", D("10"))
    assert r["net"] == D("33.00")
    assert r["tax"] == D("4.50")
    assert r["gross"] == D("37.50")
    assert r["credit_used"] == D("10.00")
    assert r["total_due"] == D("27.50")
    assert r["credit_left"] == D("0.00")
    assert r["tax_by_rate"] == {0: D("0.00"), 5: D("0.50"), 20: D("4.00")}


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


def test_default_credit_is_zero():
    r = invoice_totals([line("standard", "100.00", 1)], "A")
    assert r["credit_used"] == D("0.00")
    assert r["total_due"] == D("120.00")
    assert r["credit_left"] == D("0.00")


def test_credit_larger_than_gross_leaves_credit():
    r = invoice_totals([line("standard", "100.00", 1)], "A", D("150"))
    assert r["gross"] == D("120.00")
    assert r["credit_used"] == D("120.00")
    assert r["total_due"] == D("0.00")
    assert r["credit_left"] == D("30.00")


def test_credit_equal_to_gross():
    r = invoice_totals([line("standard", "100.00", 1)], "A", D("120"))
    assert r["credit_used"] == D("120.00")
    assert r["total_due"] == D("0.00")
    assert r["credit_left"] == D("0.00")


def test_credit_smaller_than_gross():
    r = invoice_totals([line("standard", "100.00", 1)], "A", D("50"))
    assert r["credit_used"] == D("50.00")
    assert r["total_due"] == D("70.00")
    assert r["credit_left"] == D("0.00")


def test_all_values_have_two_decimal_places():
    r = invoice_totals([line("food", "1", 2)], "B", D("1"))
    for key in ("net", "tax", "gross", "credit_used", "total_due", "credit_left"):
        assert len(str(r[key]).split(".")[1]) == 2, key
    for v in r["tax_by_rate"].values():
        assert len(str(v).split(".")[1]) == 2


def test_return_has_exact_keys():
    r = invoice_totals([], "B")
    assert set(r) == {"net", "tax", "gross", "credit_used", "total_due", "credit_left", "tax_by_rate"}


# --- tax rates ---------------------------------------------------------------

@pytest.mark.parametrize(
    "region,category,expected_rate",
    [
        ("A", "food", 0),
        ("A", "books", 5),
        ("A", "standard", 20),
        ("B", "food", 7),
        ("B", "books", 7),
        ("B", "standard", 15),
    ],
)
def test_tax_table(region, category, expected_rate):
    r = invoice_totals([line(category, "100.00", 1)], region)
    # 100.00 net at the given rate gives a tax equal to the rate in currency units
    assert r["tax_by_rate"] == {expected_rate: D(expected_rate)}
    assert r["tax"] == D(expected_rate)


def test_tax_by_rate_sums_per_rate():
    lines = [
        line("food", "10.00", 1),
        line("books", "20.00", 1),
        line("standard", "50.00", 1),
        line("books", "20.00", 1),
    ]
    r = invoice_totals(lines, "A")
    assert r["tax_by_rate"] == {0: D("0.00"), 5: D("2.00"), 20: D("10.00")}
    assert r["tax"] == D("12.00")


def test_rates_not_present_are_omitted():
    r = invoice_totals([line("food", "10.00", 1)], "B")
    assert r["tax_by_rate"] == {7: D("0.70")}


def test_zero_rate_on_line_is_included_with_zero():
    r = invoice_totals([line("food", "10.00", 1)], "A")
    assert r["tax_by_rate"] == {0: D("0.00")}
    assert 0 in r["tax_by_rate"]


# --- discounts ---------------------------------------------------------------

def test_line_discount_applies():
    r = invoice_totals([line("food", "10.00", 2, discount_pct=D("25"))], "A")
    assert r["net"] == D("15.00")


def test_discount_default_zero_when_missing():
    r = invoice_totals([line("food", "10.00", 2)], "A")
    assert r["net"] == D("20.00")


def test_discount_zero_and_hundred_allowed():
    r0 = invoice_totals([line("food", "10.00", 1, discount_pct=D("0"))], "A")
    assert r0["net"] == D("10.00")
    r100 = invoice_totals([line("food", "10.00", 1, discount_pct=D("100"))], "A")
    assert r100["net"] == D("0.00")
    assert r100["tax"] == D("0.00")


def test_bulk_discount_on_standard_stacks_multiplicatively():
    # 100 * 0.90 = 90, then * 0.95 = 85.50 (not 85)
    r = invoice_totals([line("standard", "10.00", 10, discount_pct=D("10"))], "B")
    assert r["net"] == D("85.50")
    # 85.50 * 15% = 12.825 -> 12.83 (half up)
    assert r["tax"] == D("12.83")
    assert r["gross"] == D("98.33")


def test_bulk_discount_only_at_exactly_ten_or_more():
    r9 = invoice_totals([line("standard", "10.00", 9)], "A")
    assert r9["net"] == D("90.00")
    r10 = invoice_totals([line("standard", "10.00", 10)], "A")
    assert r10["net"] == D("95.00")
    r11 = invoice_totals([line("standard", "10.00", 11)], "A")
    assert r11["net"] == D("104.50")


def test_bulk_discount_not_applied_to_food_or_books():
    rf = invoice_totals([line("food", "10.00", 10)], "A")
    assert rf["net"] == D("100.00")
    rb = invoice_totals([line("books", "10.00", 10)], "A")
    assert rb["net"] == D("100.00")


# --- rounding ----------------------------------------------------------------

def test_line_tax_rounds_half_up():
    # 0.50 * 7% = 0.035 -> 0.04
    r = invoice_totals([line("food", "0.50", 1)], "B")
    assert r["tax"] == D("0.04")


def test_small_line_tax_rounds_down_when_below_half():
    # 0.10 * 5% = 0.005 -> 0.01 (half up), but 0.09 * 5% = 0.0045 -> 0.00
    r = invoice_totals([line("books", "0.09", 1)], "A")
    assert r["tax"] == D("0.00")


def test_rounding_is_per_line_not_on_totals():
    # each line tax 0.0045 -> 0.00 individually; total would be 0.01 if summed first
    lines = [line("books", "0.09", 1), line("books", "0.09", 1)]
    r = invoice_totals(lines, "A")
    assert r["tax"] == D("0.00")
    assert r["net"] == D("0.18")


def test_line_net_rounded_before_tax():
    # net 0.125 -> rounds to 0.13 (half up); tax on the rounded net: 0.13 * 5% = 0.0065 -> 0.01
    r = invoice_totals([line("books", "0.125", 1)], "A")
    assert r["net"] == D("0.13")
    assert r["tax"] == D("0.01")


def test_discount_produces_fraction_rounded_half_up():
    # 0.05 * 1 with 50% off = 0.025 -> 0.03
    r = invoice_totals([line("food", "0.05", 1, discount_pct=D("50"))], "A")
    assert r["net"] == D("0.03")


# --- validation --------------------------------------------------------------

def test_unknown_region_raises():
    with pytest.raises(ValueError):
        invoice_totals([], "C")


def test_region_not_string_raises():
    with pytest.raises(ValueError):
        invoice_totals([], None)
    with pytest.raises(ValueError):
        invoice_totals([], ["A"])


def test_unknown_category_raises():
    with pytest.raises(ValueError):
        invoice_totals([line("toys")], "A")


@pytest.mark.parametrize("qty", [0, -1, 1.0, "2", None, True, False])
def test_invalid_qty_raises(qty):
    with pytest.raises(ValueError):
        invoice_totals([line("food", "1.00", qty)], "A")


def test_negative_unit_price_raises():
    with pytest.raises(ValueError):
        invoice_totals([line("food", "-0.01", 1)], "A")


def test_zero_unit_price_allowed():
    r = invoice_totals([line("food", "0", 1)], "A")
    assert r["net"] == D("0.00")


@pytest.mark.parametrize("pct", ["-0.01", "100.01", "101"])
def test_discount_out_of_range_raises(pct):
    with pytest.raises(ValueError):
        invoice_totals([line("food", "1.00", 1, discount_pct=D(pct))], "A")


def test_negative_credit_raises():
    with pytest.raises(ValueError):
        invoice_totals([], "A", D("-1"))
