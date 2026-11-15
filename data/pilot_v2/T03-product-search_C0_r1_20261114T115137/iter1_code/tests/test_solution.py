import sqlite3
import sys
import os

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from solution import search_products  # noqa: E402


ROWS = [
    # id, name, price, stock
    (1, "apple", 1.50, 10),
    (2, "Banana", 0.75, 5),
    (3, "cherry", 3.00, 0),      # out of stock: never returned
    (4, "Apple Pie", 4.25, 2),
    (5, "50% off coupon", 9.99, 1),
    (6, "grape_juice", 2.00, 7),
    (7, "Zucchini", 1.50, 3),
    (8, "apple", 1.50, 4),       # same name and price as id 1
    (9, "Melon", 5.00, -1),      # negative stock: never returned
]


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.execute(
        "CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, "
        "price REAL NOT NULL, stock INTEGER NOT NULL)"
    )
    c.executemany("INSERT INTO products VALUES (?, ?, ?, ?)", ROWS)
    c.commit()
    yield c
    c.close()


def ids(results):
    return [r["id"] for r in results]


# --- Defaults and basic behaviour -------------------------------------------

def test_default_returns_in_stock_items_ordered_by_name(conn):
    result = search_products(conn)
    # Binary ordering: "5" < "A" < "B" < "Z" < "a" < "g".
    # Name ties ("apple" ids 1 and 8) are broken by id ascending.
    assert ids(result) == [5, 4, 2, 7, 1, 8, 6]


def test_out_of_stock_and_negative_stock_excluded(conn):
    result = search_products(conn, limit=100)
    assert 3 not in ids(result)
    assert 9 not in ids(result)
    assert len(result) == 7


def test_result_dict_has_exactly_id_name_price(conn):
    result = search_products(conn, limit=1)
    assert len(result) == 1
    assert set(result[0].keys()) == {"id", "name", "price"}
    assert isinstance(result[0]["price"], float)


def test_returns_list_of_dicts(conn):
    result = search_products(conn)
    assert isinstance(result, list)
    assert all(isinstance(r, dict) for r in result)


# --- name_contains -----------------------------------------------------------

def test_empty_name_contains_matches_everything(conn):
    assert ids(search_products(conn, name_contains="", limit=100)) == ids(
        search_products(conn, limit=100)
    )


def test_name_contains_is_case_insensitive_for_ascii(conn):
    lower = search_products(conn, name_contains="apple", limit=100)
    upper = search_products(conn, name_contains="APPLE", limit=100)
    assert ids(lower) == ids(upper)
    assert set(ids(lower)) == {1, 4, 8}


def test_name_contains_substring_match(conn):
    result = search_products(conn, name_contains="an", limit=100)
    assert ids(result) == [2]  # only "Banana" (in stock)


def test_percent_is_literal_not_wildcard(conn):
    result = search_products(conn, name_contains="50%", limit=100)
    assert ids(result) == [5]


def test_percent_alone_matches_only_names_containing_percent(conn):
    # Only "50% off coupon" contains a literal '%'.
    assert ids(search_products(conn, name_contains="%", limit=100)) == [5]


def test_underscore_is_literal_not_wildcard(conn):
    result = search_products(conn, name_contains="grape_juice", limit=100)
    assert ids(result) == [6]
    # "_" must not match arbitrary characters such as the space in "grape juice"
    assert search_products(conn, name_contains="grape juice", limit=100) == []


def test_underscore_alone_matches_only_literal_underscore(conn):
    assert ids(search_products(conn, name_contains="_", limit=100)) == [6]


def test_no_matches_returns_empty_list(conn):
    assert search_products(conn, name_contains="xyz") == []


def test_out_of_stock_name_not_returned(conn):
    assert search_products(conn, name_contains="cherry") == []


# --- max_price --------------------------------------------------------------

def test_max_price_is_inclusive(conn):
    result = search_products(conn, max_price=1.50, limit=100)
    assert set(ids(result)) == {1, 2, 7, 8}
    assert all(r["price"] <= 1.50 for r in result)


def test_max_price_none_means_no_limit(conn):
    assert ids(search_products(conn, max_price=None, limit=100)) == ids(
        search_products(conn, limit=100)
    )


def test_max_price_below_all_prices_returns_empty(conn):
    assert search_products(conn, max_price=0.10) == []


def test_max_price_zero_is_applied_not_ignored(conn):
    assert search_products(conn, max_price=0) == []


# --- order_by and descending -------------------------------------------------

def test_order_by_price_ascending_ties_broken_by_id(conn):
    result = search_products(conn, order_by="price", limit=100)
    # prices: 0.75(2), 1.50(1), 1.50(7), 1.50(8), 2.00(6), 4.25(4), 9.99(5)
    assert ids(result) == [2, 1, 7, 8, 6, 4, 5]


def test_order_by_price_descending_ties_still_id_ascending(conn):
    result = search_products(conn, order_by="price", descending=True, limit=100)
    assert ids(result) == [5, 4, 6, 1, 7, 8, 2]


def test_order_by_name_descending(conn):
    result = search_products(conn, order_by="name", descending=True, limit=100)
    assert [r["name"] for r in result] == sorted(
        [r["name"] for r in search_products(conn, limit=100)], reverse=True
    )


def test_order_by_name_uses_binary_ordering(conn):
    names = [r["name"] for r in search_products(conn, limit=100)]
    # Uppercase letters sort before lowercase in binary ordering.
    assert names.index("Banana") < names.index("apple")
    assert names == sorted(names)


def test_name_ascending_orders_by_binary_name_then_id(conn):
    # Matches "apple" case-insensitively: "Apple Pie"(4), "apple"(1), "apple"(8).
    result = search_products(conn, name_contains="apple", limit=100)
    assert ids(result) == [4, 1, 8]


def test_name_ties_broken_by_id_ascending_when_descending(conn):
    # Descending name order: "apple"(1), "apple"(8) tie -> id ascending, then "Apple Pie"(4).
    result = search_products(conn, name_contains="apple", descending=True, limit=100)
    assert ids(result) == [1, 8, 4]


@pytest.mark.parametrize("bad", ["Name", "price ", "", "id", None, 1])
def test_invalid_order_by_raises(conn, bad):
    with pytest.raises(ValueError):
        search_products(conn, order_by=bad)


# --- limit and offset ------------------------------------------------------

def test_limit_applies_after_filtering_and_ordering(conn):
    result = search_products(conn, order_by="price", limit=2)
    assert ids(result) == [2, 1]


def test_offset_applies_after_ordering(conn):
    all_ids = ids(search_products(conn, order_by="price", limit=100))
    page = search_products(conn, order_by="price", limit=3, offset=2)
    assert ids(page) == all_ids[2:5]


def test_offset_beyond_results_returns_empty(conn):
    assert search_products(conn, limit=10, offset=1000) == []


def test_default_limit_is_20(conn):
    # Only 7 in-stock rows exist, so this just confirms it does not error.
    assert len(search_products(conn)) == 7


@pytest.mark.parametrize("limit", [1, 50, 100])
def test_valid_limit_bounds_accepted(conn, limit):
    search_products(conn, limit=limit)


@pytest.mark.parametrize("limit", [0, -1, 101, 1000])
def test_limit_out_of_range_raises(conn, limit):
    with pytest.raises(ValueError):
        search_products(conn, limit=limit)


@pytest.mark.parametrize("limit", [1.5, "10", None])
def test_limit_non_integer_raises(conn, limit):
    with pytest.raises(ValueError):
        search_products(conn, limit=limit)


@pytest.mark.parametrize("offset", [-1, -100])
def test_negative_offset_raises(conn, offset):
    with pytest.raises(ValueError):
        search_products(conn, offset=offset)


@pytest.mark.parametrize("offset", [1.0, "0", None])
def test_non_integer_offset_raises(conn, offset):
    with pytest.raises(ValueError):
        search_products(conn, offset=offset)


def test_offset_zero_accepted(conn):
    assert search_products(conn, offset=0, limit=1)


# --- Read-only guarantee -----------------------------------------------------

def test_does_not_modify_database(conn):
    before = conn.execute("SELECT * FROM products ORDER BY id").fetchall()
    changes_before = conn.total_changes
    search_products(conn, name_contains="a", max_price=5, order_by="price",
                    descending=True, limit=100, offset=0)
    after = conn.execute("SELECT * FROM products ORDER BY id").fetchall()
    assert before == after
    assert conn.total_changes == changes_before  # no rows written by the call


def test_does_not_commit_or_change_row_count(conn):
    search_products(conn, limit=100)
    count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    assert count == len(ROWS)


# --- Robustness to connection settings ---------------------------------------

def test_works_when_connection_has_row_factory(conn):
    conn.row_factory = sqlite3.Row
    result = search_products(conn, limit=100)
    assert all(isinstance(r, dict) for r in result)
    assert set(result[0].keys()) == {"id", "name", "price"}
