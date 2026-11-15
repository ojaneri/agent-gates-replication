from decimal import Decimal

import pytest

from solution import invoice_totals

D = Decimal


def line(category="food", unit_price=D("10.00"), qty=1, discount_pct=None):
    item = {"sku": "X", "category": category, "unit_price": unit_price, "qty": qty}
    if discount_pct is not None:
        item["discount_pct"] = discount_pct
    return item


def test_empty_lines_all_zero():
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


def test_food_region_a_has_zero_tax_and_zero_rate_is_included():
    r = invoice_totals([line("food", D("10.00"), 3)], "A")
    assert r["net"] == D("30.00")
    assert r["tax"] == D("0.00")
    assert r["gross"] == D("30.00")
    assert r["tax_by_rate"] == {0: D("0.00")}


def test_standard_region_b_with_bulk_and_discount_multiplied():
    # 100 * 10 = 1000; -10% = 900; bulk -5% = 855.00; tax 15% = 128.25
    r = invoice_totals([line("standard", D("100.00"), 10, D("10"))], "B")
    assert r["net"] == D("855.00")
    assert r["tax"] == D("128.25")
    assert r["gross"] == D("983.25")
    assert r["tax_by_rate"] == {15: D("128.25")}


def test_bulk_discount_only_for_standard_at_ten_or_more():
    # books with qty 10 gets no bulk discount
    r = invoice_totals([line("books", D("10.00"), 10)], "A")
    assert r["net"] == D("100.00")
    # standard with qty 9 gets no bulk discount
    r = invoice_totals([line("standard", D("10.00"), 9)], "A")
    assert r["net"] == D("90.00")


def test_bulk_discount_threshold_inclusive_at_ten():
    r = invoice_totals([line("standard", D("10.00"), 10)], "A")
    assert r["net"] == D("95.00")


def test_rounding_half_up_per_line_on_tax():
    # 0.10 * 1 = 0.10; 5% = 0.005 -> 0.01
    r = invoice_totals([line("books", D("0.10"), 1)], "A")
    assert r["tax"] == D("0.01")


def test_rounding_is_per_line_not_on_totals():
    # two lines each tax 0.005 -> 0.01 each, total 0.02
    lines = [line("books", D("0.10"), 1), line("books", D("0.10"), 1)]
    r = invoice_totals(lines, "A")
    assert r["tax"] == D("0.02")
    assert r["tax_by_rate"] == {5: D("0.02")}


def test_tax_by_rate_groups_and_omits_unused_rates():
    lines = [
        line("standard", D("10.00"), 1),
        line("books", D("20.00"), 1),
        line("standard", D("5.00"), 2),
    ]
    r = invoice_totals(lines, "A")
    # standard: 10 + 10 = 20 net -> tax 4.00; books 20 -> tax 1.00
    assert r["tax_by_rate"] == {20: D("4.00"), 5: D("1.00")}
    assert 0 not in r["tax_by_rate"]
    assert r["tax"] == D("5.00")
    assert r["net"] == D("40.00")
    assert r["gross"] == D("45.00")


def test_credit_partially_covers_gross():
    r = invoice_totals([line("food", D("10.00"), 1)], "A", credit=D("4.00"))
    assert r["credit_used"] == D("4.00")
    assert r["total_due"] == D("6.00")
    assert r["credit_left"] == D("0.00")


def test_credit_exceeds_gross():
    r = invoice_totals([line("food", D("10.00"), 1)], "A", credit=D("50.00"))
    assert r["credit_used"] == D("10.00")
    assert r["total_due"] == D("0.00")
    assert r["credit_left"] == D("40.00")


def test_default_credit_is_zero():
    r = invoice_totals([line("food", D("10.00"), 1)], "A")
    assert r["credit_used"] == D("0.00")
    assert r["credit_left"] == D("0.00")
    assert r["total_due"] == D("10.00")


def test_money_values_have_two_decimal_places():
    r = invoice_totals([line("food", D("3"), 1)], "A", credit=D("1"))
    for key in ("net", "tax", "gross", "credit_used", "total_due", "credit_left"):
        assert r[key].as_tuple().exponent == -2, key
    for v in r["tax_by_rate"].values():
        assert v.as_tuple().exponent == -2


def test_discount_100_percent_gives_zero_net():
    r = invoice_totals([line("standard", D("50.00"), 1, D("100"))], "B")
    assert r["net"] == D("0.00")
    assert r["tax"] == D("0.00")


def test_discount_zero_and_hundred_are_allowed():
    invoice_totals([line(discount_pct=D("0"))], "A")
    invoice_totals([line(discount_pct=D("100"))], "A")


@pytest.mark.parametrize(
    "lines, region, credit",
    [
        ([line()], "C", D("0")),
        ([line(category="toys")], "A", D("0")),
        ([line(qty=0)], "A", D("0")),
        ([line(qty=-1)], "A", D("0")),
        ([line(qty=True)], "A", D("0")),
        ([line(qty=1.5)], "A", D("0")),
        ([line(unit_price=D("-0.01"))], "A", D("0")),
        ([line(discount_pct=D("-1"))], "A", D("0")),
        ([line(discount_pct=D("100.01"))], "A", D("0")),
        ([line()], "A", D("-1")),
    ],
)
def test_invalid_inputs_raise_value_error(lines, region, credit):
    with pytest.raises(ValueError):
        invoice_totals(lines, region, credit)
