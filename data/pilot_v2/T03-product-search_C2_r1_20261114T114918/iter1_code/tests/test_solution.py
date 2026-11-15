import sqlite3
import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from solution import search_products  # noqa: E402


ROWS = [
    # id, name, price, stock
    (1, "apple", 1.50, 10),
    (2, "Banana", 0.25, 5),
    (3, "cherry", 3.00, 0),      # out of stock: must never appear
    (4, "Apricot", 2.00, 7),
    (5, "50% off jam", 4.00, 2),
    (6, "500 off jam", 4.00, 2),
    (7, "under_score", 1.00, 1),
    (8, "underXscore", 1.00, 1),
    (9, "Zucchini", 2.00, 3),
    (10, "apple", 1.50, 4),      # duplicate name, ties broken by id
    (11, "Éclair", 5.00, 1),     # non-ASCII, only ASCII is case-folded
]


@pytest.fixture
def conn():
    connection = sqlite3.connect(":memory:")
    connection.execute(
        "CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, "
        "price REAL NOT NULL, stock INTEGER NOT NULL)"
    )
    connection.executemany("INSERT INTO products VALUES (?, ?, ?, ?)", ROWS)
    connection.commit()
    yield connection
    connection.close()


def ids(results):
    return [r["id"] for r in results]


# Rule 1: stock filter -----------------------------------------------------

def test_out_of_stock_products_are_excluded(conn):
    results = search_products(conn, limit=100)
    assert 3 not in ids(results)


def test_positive_stock_products_are_included(conn):
    assert 1 in ids(search_products(conn, limit=100))


# Rule 2: name substring ---------------------------------------------------

def test_empty_name_matches_everything_in_stock(conn):
    assert sorted(ids(search_products(conn, limit=100))) == [1, 2, 4, 5, 6, 7, 8, 9, 10, 11]


def test_name_filter_is_substring(conn):
    assert sorted(ids(search_products(conn, "ap", limit=100))) == [1, 4, 10]


def test_name_filter_is_case_insensitive_for_ascii(conn):
    assert sorted(ids(search_products(conn, "APPLE", limit=100))) == [1, 10]
    assert sorted(ids(search_products(conn, "banana", limit=100))) == [2]


def test_percent_is_literal(conn):
    results = search_products(conn, "50%", limit=100)
    assert ids(results) == [5]


def test_underscore_is_literal(conn):
    assert ids(search_products(conn, "under_score", limit=100)) == [7]


def test_underscore_does_not_match_any_character(conn):
    assert ids(search_products(conn, "under_score", limit=100)) != [8]
    assert ids(search_products(conn, "underXscore", limit=100)) == [8]


def test_non_ascii_is_not_case_folded(conn):
    assert search_products(conn, "éclair", limit=100) == []
    assert ids(search_products(conn, "Éclair", limit=100)) == [11]


def test_no_match_returns_empty_list(conn):
    assert search_products(conn, "nothing-like-this") == []


def test_name_filter_rejects_non_string(conn):
    with pytest.raises(ValueError):
        search_products(conn, name_contains=None)


# Rule 3: max_price --------------------------------------------------------

def test_max_price_is_inclusive(conn):
    results = search_products(conn, max_price=1.50, limit=100)
    assert sorted(ids(results)) == [1, 2, 7, 8, 10]


def test_max_price_none_means_no_limit(conn):
    assert 11 in ids(search_products(conn, max_price=None, limit=100))


def test_max_price_below_all_prices_returns_empty(conn):
    assert search_products(conn, max_price=0.10) == []


def test_max_price_zero_is_applied_not_ignored(conn):
    assert search_products(conn, max_price=0) == []


# Rule 4: order_by and descending -----------------------------------------

def test_default_order_is_name_ascending_binary(conn):
    results = search_products(conn, limit=100)
    names = [r["name"] for r in results]
    assert names == sorted(names)
    # Binary ordering: uppercase letters come before lowercase.
    assert names.index("Apricot") < names.index("apple")


def test_order_by_name_descending_reverses(conn):
    asc = [r["name"] for r in search_products(conn, limit=100)]
    desc = [r["name"] for r in search_products(conn, order_by="name", descending=True, limit=100)]
    assert desc != asc
    assert sorted(desc, reverse=False) == sorted(asc)
    assert desc[0] == max(asc)


def test_order_by_price_ascending(conn):
    results = search_products(conn, order_by="price", limit=100)
    prices = [r["price"] for r in results]
    assert prices == sorted(prices)


def test_order_by_price_descending(conn):
    results = search_products(conn, order_by="price", descending=True, limit=100)
    prices = [r["price"] for r in results]
    assert prices == sorted(prices, reverse=True)


def test_order_by_invalid_value_raises(conn):
    with pytest.raises(ValueError):
        search_products(conn, order_by="id")


def test_order_by_is_case_sensitive(conn):
    with pytest.raises(ValueError):
        search_products(conn, order_by="Name")


def test_order_by_none_raises(conn):
    with pytest.raises(ValueError):
        search_products(conn, order_by=None)


# Rule 5: ties broken by id ascending -------------------------------------

def test_price_ties_broken_by_id_ascending(conn):
    results = search_products(conn, order_by="price", limit=100)
    price_one = [r["id"] for r in results if r["price"] == 1.00]
    assert price_one == [7, 8]


def test_price_ties_stay_id_ascending_when_descending(conn):
    results = search_products(conn, order_by="price", descending=True, limit=100)
    price_two = [r["id"] for r in results if r["price"] == 2.00]
    assert price_two == [4, 9]


def test_name_ties_broken_by_id_ascending(conn):
    results = search_products(conn, "apple", limit=100)
    assert ids(results) == [1, 10]


def test_name_ties_stay_id_ascending_when_descending(conn):
    results = search_products(conn, "apple", descending=True, limit=100)
    assert ids(results) == [1, 10]


# Rule 6: limit and offset -------------------------------------------------

def test_default_limit_is_20(conn):
    for i in range(30):
        conn.execute("INSERT INTO products VALUES (?, ?, ?, ?)", (100 + i, f"bulk{i:02d}", 1.0, 1))
    assert len(search_products(conn)) == 20


def test_limit_applied_after_ordering(conn):
    results = search_products(conn, order_by="price", limit=2)
    assert ids(results) == [2, 7]


def test_offset_applied_after_ordering(conn):
    all_ids = ids(search_products(conn, order_by="price", limit=100))
    paged = ids(search_products(conn, order_by="price", limit=3, offset=2))
    assert paged == all_ids[2:5]


def test_offset_beyond_end_returns_empty(conn):
    assert search_products(conn, limit=5, offset=1000) == []


def test_limit_one_is_valid(conn):
    assert len(search_products(conn, limit=1)) == 1


def test_limit_100_is_valid(conn):
    assert len(search_products(conn, limit=100)) == 10


@pytest.mark.parametrize("bad", [0, -1, 101, 1000])
def test_limit_out_of_range_raises(conn, bad):
    with pytest.raises(ValueError):
        search_products(conn, limit=bad)


def test_limit_non_integer_raises(conn):
    with pytest.raises(ValueError):
        search_products(conn, limit=2.0)
    with pytest.raises(ValueError):
        search_products(conn, limit="5")


def test_limit_bool_raises(conn):
    with pytest.raises(ValueError):
        search_products(conn, limit=True)


def test_offset_zero_is_valid(conn):
    assert search_products(conn, offset=0, limit=100) == search_products(conn, limit=100)


def test_offset_negative_raises(conn):
    with pytest.raises(ValueError):
        search_products(conn, offset=-1)


def test_offset_non_integer_raises(conn):
    with pytest.raises(ValueError):
        search_products(conn, offset=1.5)


def test_offset_bool_raises(conn):
    with pytest.raises(ValueError):
        search_products(conn, offset=False)


# Rule 7: result shape -----------------------------------------------------

def test_result_dicts_have_exactly_id_name_price(conn):
    results = search_products(conn, limit=100)
    assert results
    for row in results:
        assert set(row.keys()) == {"id", "name", "price"}


def test_result_values_match_table(conn):
    results = search_products(conn, "zucchini")
    assert results == [{"id": 9, "name": "Zucchini", "price": 2.00}]


def test_result_is_list_of_dicts(conn):
    results = search_products(conn)
    assert isinstance(results, list)
    assert all(isinstance(r, dict) for r in results)


# Rule 8: read-only --------------------------------------------------------

def test_database_is_not_modified(conn):
    before = conn.execute("SELECT * FROM products ORDER BY id").fetchall()
    search_products(conn, "app", max_price=5, order_by="price", descending=True, limit=3, offset=1)
    search_products(conn, "%", limit=100)
    after = conn.execute("SELECT * FROM products ORDER BY id").fetchall()
    assert before == after


def test_injection_attempt_in_name_is_harmless(conn):
    assert search_products(conn, "' OR 1=1 --") == []
    count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    assert count == len(ROWS)
