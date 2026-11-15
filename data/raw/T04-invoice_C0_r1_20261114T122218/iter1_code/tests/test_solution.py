from decimal import Decimal

import pytest

from solution import invoice_totals


def line(category="food", unit_price="10.00", qty=1, discount_pct=None):
    d = {
        "sku": "X",
        "category": category,
        "unit_price": Decimal(unit_price),
        "qty": qty,
    }
    if discount_pct is not None:
        d["discount_pct"] = Decimal(discount_pct)
    return d


def assert_cents(result):
    for key in ("net", "tax", "gross", "credit_used", "total_due", "credit_left"):
        assert result[key].as_tuple().exponent == -2, key
    for value in result["tax_by_rate"].values():
        assert value.as_tuple().exponent == -2


def test_simple_food_region_a_zero_tax():
    r = invoice_totals([line("food", "10.00", 3)], "A")
    assert r["net"] == Decimal("30.00")
    assert r["tax"] == Decimal("0.00")
    assert r["gross"] == Decimal("30.00")
    assert r["credit_used"] == Decimal("0.00")
    assert r["total_due"] == Decimal("30.00")
    assert r["credit_left"] == Decimal("0.00")
    assert r["tax_by_rate"] == {0: Decimal("0.00")}
    assert_cents(r)


def test_bulk_discount_stacks_on_line_discount():
    # 100.00 less 10% = 90.00, then 5% bulk = 85.50; standard 20% tax = 17.10
    r = invoice_totals([line("standard", "10.00", 10, "10")], "A")
    assert r["net"] == Decimal("85.50")
    assert r["tax"] == Decimal("17.10")
    assert r["gross"] == Decimal("102.60")
    assert r["tax_by_rate"] == {20: Decimal("17.10")}
    assert_cents(r)


def test_bulk_discount_needs_standard_category():
    # food with qty 10 gets no bulk discount
    r = invoice_totals([line("food", "10.00", 10)], "B")
    assert r["net"] == Decimal("100.00")
    assert r["tax"] == Decimal("7.00")


def test_bulk_discount_needs_qty_10():
    # qty 9 standard: no bulk discount -> 9 * 10 = 90.00, tax 15% = 13.50
    r = invoice_totals([line("standard", "10.00", 9)], "B")
    assert r["net"] == Decimal("90.00")
    assert r["tax"] == Decimal("13.50")


def test_bulk_discount_rounds_half_up_per_line():
    # 1.01 * 10 = 10.10 * 0.95 = 9.595 -> 9.60; tax 20% of 9.60 = 1.92
    r = invoice_totals([line("standard", "1.01", 10)], "A")
    assert r["net"] == Decimal("9.60")
    assert r["tax"] == Decimal("1.92")


def test_tax_rounds_half_up_per_line():
    # net 0.50 at 7% = 0.035 -> 0.04
    r = invoice_totals([line("books", "0.50", 1)], "B")
    assert r["tax"] == Decimal("0.04")
    assert r["tax_by_rate"] == {7: Decimal("0.04")}


def test_rounding_is_per_line_not_on_totals():
    # two lines of 0.50 books in B: each tax 0.04 -> total 0.08 (not 0.07 from 1.00 * 7%)
    r = invoice_totals([line("books", "0.50", 1), line("books", "0.50", 1)], "B")
    assert r["tax"] == Decimal("0.08")
    assert r["net"] == Decimal("1.00")


def test_mixed_lines_tax_by_rate():
    lines = [
        line("food", "10.00", 1),       # rate 0
        line("books", "20.00", 2),      # rate 5 on 40.00 -> 2.00
        line("standard", "5.00", 1),    # rate 20 on 5.00 -> 1.00
    ]
    r = invoice_totals(lines, "A")
    assert r["net"] == Decimal("55.00")
    assert r["tax"] == Decimal("3.00")
    assert r["gross"] == Decimal("58.00")
    assert r["tax_by_rate"] == {
        0: Decimal("0.00"),
        5: Decimal("2.00"),
        20: Decimal("1.00"),
    }
    assert_cents(r)


def test_rates_not_present_are_omitted():
    r = invoice_totals([line("standard", "10.00", 1)], "B")
    assert r["tax_by_rate"] == {15: Decimal("1.50")}


def test_credit_partial():
    r = invoice_totals([line("standard", "10.00", 10, "10")], "A", Decimal("100"))
    assert r["gross"] == Decimal("102.60")
    assert r["credit_used"] == Decimal("100.00")
    assert r["total_due"] == Decimal("2.60")
    assert r["credit_left"] == Decimal("0.00")
    assert_cents(r)


def test_credit_exceeds_gross():
    r = invoice_totals([line("standard", "10.00", 10, "10")], "A", Decimal("500"))
    assert r["credit_used"] == Decimal("102.60")
    assert r["total_due"] == Decimal("0.00")
    assert r["credit_left"] == Decimal("397.40")
    assert_cents(r)


def test_default_credit_is_zero():
    r = invoice_totals([line("food", "1.00", 1)], "A")
    assert r["credit_used"] == Decimal("0.00")
    assert r["credit_left"] == Decimal("0.00")


def test_empty_lines():
    r = invoice_totals([], "A", Decimal("5"))
    assert r == {
        "net": Decimal("0.00"),
        "tax": Decimal("0.00"),
        "gross": Decimal("0.00"),
        "credit_used": Decimal("0.00"),
        "total_due": Decimal("0.00"),
        "credit_left": Decimal("5.00"),
        "tax_by_rate": {},
    }
    assert_cents(r)


def test_discount_boundaries_allowed():
    r = invoice_totals([line("food", "10.00", 1, "100")], "A")
    assert r["net"] == Decimal("0.00")
    r = invoice_totals([line("food", "10.00", 1, "0")], "A")
    assert r["net"] == Decimal("10.00")


@pytest.mark.parametrize(
    "bad_lines, region, credit",
    [
        ([line()], "C", Decimal("0")),                              # unknown region
        ([line("toys")], "A", Decimal("0")),                         # unknown category
        ([line(qty=0)], "A", Decimal("0")),                          # qty < 1
        ([line(qty=-2)], "A", Decimal("0")),
        ([line(qty=True)], "A", Decimal("0")),                       # bool is not accepted
        ([line(qty=1.0)], "A", Decimal("0")),                        # not an int
        ([line(unit_price="-1.00")], "A", Decimal("0")),             # negative price
        ([line(discount_pct="101")], "A", Decimal("0")),
        ([line(discount_pct="-0.01")], "A", Decimal("0")),
        ([line()], "A", Decimal("-1")),                              # negative credit
    ],
)
def test_validation_errors(bad_lines, region, credit):
    with pytest.raises(ValueError):
        invoice_totals(bad_lines, region, credit)
