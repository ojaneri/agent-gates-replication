from decimal import Decimal

import pytest

from solution import invoice_totals

D = Decimal


def line(category="standard", unit_price="10.00", qty=1, discount=None):
    item = {"sku": "X", "category": category, "unit_price": D(unit_price), "qty": qty}
    if discount is not None:
        item["discount_pct"] = D(discount)
    return item


def as_strings(result):
    out = {k: str(v) for k, v in result.items() if k != "tax_by_rate"}
    out["tax_by_rate"] = {k: str(v) for k, v in result["tax_by_rate"].items()}
    return out


def test_empty_lines_gives_zeros():
    result = invoice_totals([], "A")
    assert as_strings(result) == {
        "net": "0.00",
        "tax": "0.00",
        "gross": "0.00",
        "credit_used": "0.00",
        "total_due": "0.00",
        "credit_left": "0.00",
        "tax_by_rate": {},
    }


def test_single_standard_line_region_a():
    result = invoice_totals([line("standard", "100.00")], "A")
    assert as_strings(result) == {
        "net": "100.00",
        "tax": "20.00",
        "gross": "120.00",
        "credit_used": "0.00",
        "total_due": "120.00",
        "credit_left": "0.00",
        "tax_by_rate": {20: "20.00"},
    }


def test_multi_line_region_b_with_credit():
    lines = [
        line("standard", "50.00", qty=2),
        line("food", "3.33", qty=3),
        line("books", "1.00", qty=1),
    ]
    result = invoice_totals(lines, "B", credit=D("26.76"))
    assert as_strings(result) == {
        "net": "110.99",
        "tax": "15.77",
        "gross": "126.76",
        "credit_used": "26.76",
        "total_due": "100.00",
        "credit_left": "0.00",
        "tax_by_rate": {15: "15.00", 7: "0.77"},
    }


def test_bulk_discount_applies_at_qty_10_for_standard():
    result = invoice_totals([line("standard", "10.00", qty=10)], "A")
    assert str(result["net"]) == "95.00"
    assert str(result["tax"]) == "19.00"


def test_bulk_discount_not_applied_at_qty_9():
    result = invoice_totals([line("standard", "10.00", qty=9)], "A")
    assert str(result["net"]) == "90.00"
    assert str(result["tax"]) == "18.00"


def test_bulk_discount_not_applied_to_books():
    result = invoice_totals([line("books", "10.00", qty=10)], "A")
    assert str(result["net"]) == "100.00"
    assert str(result["tax"]) == "5.00"


def test_bulk_discount_stacks_multiplicatively_with_line_discount():
    result = invoice_totals([line("standard", "10.00", qty=10, discount="10")], "A")
    assert str(result["net"]) == "85.50"
    assert str(result["tax"]) == "17.10"


def test_line_discount_alone():
    result = invoice_totals([line("books", "10.00", qty=2, discount="25")], "A")
    assert str(result["net"]) == "15.00"
    assert str(result["tax"]) == "0.75"


def test_discount_zero_and_hundred_are_allowed():
    free = invoice_totals([line("food", "9.99", qty=1, discount="100")], "A")
    assert str(free["net"]) == "0.00"
    full = invoice_totals([line("food", "9.99", qty=1, discount="0")], "A")
    assert str(full["net"]) == "9.99"


def test_zero_unit_price_is_allowed():
    result = invoice_totals([line("books", "0.00")], "A")
    assert str(result["gross"]) == "0.00"


def test_tax_rounds_half_up_to_cent():
    result = invoice_totals([line("books", "0.10", qty=1)], "A")
    assert str(result["tax"]) == "0.01"


def test_net_rounds_half_up_to_cent():
    result = invoice_totals([line("food", "0.01", qty=1, discount="50")], "A")
    assert str(result["net"]) == "0.01"
    assert as_strings(result)["tax_by_rate"] == {0: "0.00"}


def test_rounding_is_per_line_not_on_totals():
    lines = [line("books", "0.10", qty=1), line("books", "0.10", qty=1)]
    result = invoice_totals(lines, "A")
    assert str(result["tax"]) == "0.02"
    assert str(result["gross"]) == "0.22"


def test_credit_partially_pays():
    result = invoice_totals([line("food", "10.00")], "A", credit=D("4"))
    assert str(result["credit_used"]) == "4.00"
    assert str(result["total_due"]) == "6.00"
    assert str(result["credit_left"]) == "0.00"


def test_credit_larger_than_gross_leaves_remainder():
    result = invoice_totals([line("food", "10.00")], "A", credit=D("25"))
    assert str(result["credit_used"]) == "10.00"
    assert str(result["total_due"]) == "0.00"
    assert str(result["credit_left"]) == "15.00"


def test_credit_defaults_to_zero():
    result = invoice_totals([line("food", "10.00")], "A")
    assert str(result["credit_used"]) == "0.00"
    assert str(result["credit_left"]) == "0.00"
    assert str(result["total_due"]) == "10.00"


def test_tax_by_rate_omits_unused_rates():
    result = invoice_totals([line("books", "10.00")], "A")
    assert as_strings(result)["tax_by_rate"] == {5: "0.50"}


def test_tax_by_rate_sums_lines_sharing_a_rate():
    lines = [line("food", "10.00"), line("books", "10.00")]
    result = invoice_totals(lines, "B")
    assert as_strings(result)["tax_by_rate"] == {7: "1.40"}


def test_zero_rate_is_reported_when_present():
    result = invoice_totals([line("food", "10.00")], "A")
    assert result["tax_by_rate"] == {0: D("0.00")}


@pytest.mark.parametrize(
    "lines, region, credit",
    [
        ([line()], "C", D("0")),
        ([line()], "", D("0")),
        ([{**line(), "category": "toys"}], "A", D("0")),
        ([line(qty=0)], "A", D("0")),
        ([line(qty=-1)], "A", D("0")),
        ([line(qty=True)], "A", D("0")),
        ([line(qty=1.5)], "A", D("0")),
        ([line(qty=2.0)], "A", D("0")),
        ([line(unit_price="-0.01")], "A", D("0")),
        ([line(discount="100.01")], "A", D("0")),
        ([line(discount="-0.01")], "A", D("0")),
        ([line()], "A", D("-1")),
    ],
)
def test_invalid_input_raises_value_error(lines, region, credit):
    with pytest.raises(ValueError):
        invoice_totals(lines, region, credit=credit)
