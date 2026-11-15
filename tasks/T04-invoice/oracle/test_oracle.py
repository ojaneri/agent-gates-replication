from decimal import Decimal as D

import pytest

from solution import invoice_totals


def L(cat, price, qty, disc=None, sku="x"):
    d = {"sku": sku, "category": cat, "unit_price": D(price), "qty": qty}
    if disc is not None:
        d["discount_pct"] = D(disc)
    return d


def test_empty():
    r = invoice_totals([], "A")
    assert r == {"net": D("0.00"), "tax": D("0.00"), "gross": D("0.00"), "credit_used": D("0.00"),
                 "total_due": D("0.00"), "credit_left": D("0.00"), "tax_by_rate": {}}


def test_simple_standard():
    r = invoice_totals([L("standard", "10.00", 2)], "A")
    assert (r["net"], r["tax"], r["gross"], r["total_due"]) == (D("20.00"), D("4.00"), D("24.00"), D("24.00"))
    assert r["tax_by_rate"] == {20: D("4.00")}


def test_mixed_region_a_includes_zero_rate():
    r = invoice_totals([L("food", "5.00", 3), L("books", "12.50", 2), L("standard", "9.99", 1)], "A")
    assert (r["net"], r["tax"], r["gross"]) == (D("49.99"), D("3.25"), D("53.24"))
    assert r["tax_by_rate"] == {0: D("0.00"), 5: D("1.25"), 20: D("2.00")}


def test_mixed_region_b_merges_equal_rates():
    r = invoice_totals([L("food", "5.00", 3), L("books", "12.50", 2), L("standard", "9.99", 1)], "B")
    assert (r["net"], r["tax"], r["gross"]) == (D("49.99"), D("4.30"), D("54.29"))
    assert r["tax_by_rate"] == {7: D("2.80"), 15: D("1.50")}


def test_rounding_is_per_line_half_up():
    # each line: 0.25 with 50% off = 0.125 -> 0.13; two lines -> 0.26 (not 0.25)
    r = invoice_totals([L("food", "0.25", 1, "50"), L("food", "0.25", 1, "50")], "A")
    assert r["net"] == D("0.26") and r["gross"] == D("0.26")


def test_line_discount_fraction():
    # 19.99 x 3 x 0.85 = 50.9745 -> 50.97; tax 20% = 10.194 -> 10.19
    r = invoice_totals([L("standard", "19.99", 3, "15")], "A")
    assert (r["net"], r["tax"], r["gross"]) == (D("50.97"), D("10.19"), D("61.16"))


def test_bulk_at_exactly_ten():
    r = invoice_totals([L("standard", "10.00", 10)], "A")
    assert (r["net"], r["tax"], r["gross"]) == (D("95.00"), D("19.00"), D("114.00"))


def test_no_bulk_below_ten():
    r = invoice_totals([L("standard", "10.00", 9)], "A")
    assert (r["net"], r["tax"]) == (D("90.00"), D("18.00"))


def test_bulk_only_for_standard():
    r = invoice_totals([L("books", "10.00", 10)], "A")
    assert (r["net"], r["tax"]) == (D("100.00"), D("5.00"))


def test_bulk_compounds_with_line_discount():
    r = invoice_totals([L("standard", "100.00", 10, "10")], "A")
    assert (r["net"], r["tax"], r["gross"]) == (D("855.00"), D("171.00"), D("1026.00"))


def test_full_discount_allowed():
    r = invoice_totals([L("standard", "50.00", 1, "100")], "A")
    assert (r["net"], r["tax"]) == (D("0.00"), D("0.00"))
    assert r["tax_by_rate"] == {20: D("0.00")}


@pytest.mark.parametrize("disc", ["-1", "100.01"])
def test_invalid_discount(disc):
    with pytest.raises(ValueError):
        invoice_totals([L("standard", "1.00", 1, disc)], "A")


@pytest.mark.parametrize("qty", [0, -2, True, 2.0])
def test_invalid_qty(qty):
    with pytest.raises(ValueError):
        invoice_totals([L("standard", "1.00", qty)], "A")


def test_zero_price_is_valid():
    r = invoice_totals([L("food", "0.00", 1), L("standard", "0", 2)], "A")
    assert (r["net"], r["tax"]) == (D("0.00"), D("0.00"))


def test_negative_price():
    with pytest.raises(ValueError):
        invoice_totals([L("standard", "-0.01", 1)], "A")


def test_unknown_region_and_category():
    with pytest.raises(ValueError):
        invoice_totals([L("standard", "1.00", 1)], "C")
    with pytest.raises(ValueError):
        invoice_totals([L("toys", "1.00", 1)], "A")


def test_unknown_region_even_when_empty():
    with pytest.raises(ValueError):
        invoice_totals([], "Z")


def test_credit_partial():
    r = invoice_totals([L("standard", "10.00", 2)], "A", D("10.00"))
    assert (r["credit_used"], r["total_due"], r["credit_left"]) == (D("10.00"), D("14.00"), D("0.00"))


def test_credit_exceeds_gross():
    r = invoice_totals([L("standard", "10.00", 2)], "A", D("30.00"))
    assert (r["credit_used"], r["total_due"], r["credit_left"]) == (D("24.00"), D("0.00"), D("6.00"))


def test_negative_credit():
    with pytest.raises(ValueError):
        invoice_totals([], "A", D("-1"))


def test_money_has_two_places_and_rate_keys_are_ints():
    r = invoice_totals([L("books", "3.333", 3)], "B")
    for k in ("net", "tax", "gross", "credit_used", "total_due", "credit_left"):
        assert isinstance(r[k], D) and r[k].as_tuple().exponent == -2, k
    assert all(type(k) is int for k in r["tax_by_rate"])
