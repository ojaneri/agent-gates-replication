import sqlite3
import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from solution import search_products  # noqa: E402


ROWS = [
    (1, "apple", 1.50, 5),
    (2, "Apricot", 2.00, 3),
    (3, "Banana", 0.75, 0),      # out of stock
    (4, "cherry", 3.00, 10),
    (5, "50% off juice", 4.00, 2),
    (6, "50 percent", 4.00, 1),
    (7, "under_score", 1.00, 4),
    (8, "underXscore", 1.00, 4),
    (9, "Zucchini", 1.50, 7),
    (10, "apple pie", 6.00, 1),
    (11, "Éclair", 2.50, 2),     # non-ASCII, must not be folded
    (12, "éclair", 2.50, 2),
    (13, "ANT", 0.50, 1),
]


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, "
              "price REAL NOT NULL, stock INTEGER NOT NULL)")
    c.executemany("INSERT INTO products VALUES (?, ?, ?, ?)", ROWS)
    c.commit()
    yield c
    c.close()


def ids(rows):
    return [r["id"] for r in rows]


# --- stock filter -------------------------------------------------------

def test_out_of_stock_excluded(conn):
    assert 3 not in ids(search_products(conn, limit=100))


def test_zero_stock_excluded_and_positive_included(conn):
    assert 13 in ids(search_products(conn, limit=100))


# --- name_contains ------------------------------------------------------

def test_empty_name_matches_all_in_stock(conn):
    assert len(search_products(conn, limit=100)) == 12


def test_substring_match(conn):
    assert ids(search_products(conn, name_contains="pie")) == [10]


def test_match_is_case_insensitive_for_ascii(conn):
    assert ids(search_products(conn, name_contains="APPLE")) == [1, 10]


def test_match_is_substring_not_prefix(conn):
    assert ids(search_products(conn, name_contains="nana")) == []
    assert ids(search_products(conn, name_contains="ana")) == []  # Banana is out of stock
    assert ids(search_products(conn, name_contains="ant")) == [13]


def test_percent_is_literal(conn):
    assert ids(search_products(conn, name_contains="50%")) == [5]


def test_percent_not_wildcard(conn):
    # "%" alone would match everything if treated as a LIKE wildcard.
    assert ids(search_products(conn, name_contains="%")) == [5]


def test_underscore_is_literal(conn):
    assert ids(search_products(conn, name_contains="under_score")) == [7]


def test_underscore_not_wildcard(conn):
    # "_" as a wildcard would also match "underXscore".
    assert ids(search_products(conn, name_contains="_")) == [7]


def test_non_ascii_not_case_folded(conn):
    assert ids(search_products(conn, name_contains="éclair")) == [12]
    assert ids(search_products(conn, name_contains="ÉCLAIR")) == [11]


def test_no_match_returns_empty(conn):
    assert search_products(conn, name_contains="zzz") == []


# --- max_price ----------------------------------------------------------

def test_max_price_none_keeps_all(conn):
    assert len(search_products(conn, max_price=None, limit=100)) == 12


def test_max_price_is_inclusive(conn):
    assert 1 in ids(search_products(conn, max_price=1.50, limit=100))
    assert 9 in ids(search_products(conn, max_price=1.50, limit=100))


def test_max_price_excludes_above(conn):
    got = ids(search_products(conn, max_price=1.49, limit=100))
    assert 1 not in got and 9 not in got
    assert 13 in got


def test_max_price_zero_returns_none_cheap(conn):
    assert search_products(conn, max_price=0) == []


# --- order_by / descending ----------------------------------------------

def test_default_order_is_name_ascending_binary(conn):
    names = [r["name"] for r in search_products(conn, limit=100)]
    assert names == sorted(names)
    assert names[0] == "50 percent"  # ' ' (0x20) < '%' (0x25), digits before letters


def test_uppercase_sorts_before_lowercase(conn):
    got = [r["name"] for r in search_products(conn, name_contains="a", limit=100)]
    assert got.index("ANT") < got.index("apple")


def test_order_by_name_descending(conn):
    names_desc = [r["name"] for r in search_products(conn, order_by="name", descending=True, limit=100)]
    names_asc = [r["name"] for r in search_products(conn, order_by="name", limit=100)]
    assert names_desc == list(reversed(names_asc))


def test_order_by_price_ascending_ties_by_id(conn):
    got = ids(search_products(conn, order_by="price", limit=100))
    # price 0.50 (13), 1.00 (7,8), 1.50 (1,9), 2.00 (2), 2.50 (11,12), 3.00 (4), 4.00 (5,6), 6.00 (10)
    assert got == [13, 7, 8, 1, 9, 2, 11, 12, 4, 5, 6, 10]


def test_order_by_price_descending_ties_still_by_id_ascending(conn):
    got = ids(search_products(conn, order_by="price", descending=True, limit=100))
    assert got == [10, 5, 6, 4, 11, 12, 2, 1, 9, 7, 8, 13]


def test_descending_name_ties_by_id_ascending():
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, "
              "price REAL NOT NULL, stock INTEGER NOT NULL)")
    c.executemany("INSERT INTO products VALUES (?, ?, ?, ?)",
                  [(5, "same", 1.0, 1), (2, "same", 1.0, 1), (9, "other", 1.0, 1)])
    got = ids(search_products(c, order_by="name", descending=True))
    assert got == [2, 5, 9]
    c.close()


def test_invalid_order_by_raises(conn):
    with pytest.raises(ValueError):
        search_products(conn, order_by="id")


def test_order_by_is_case_sensitive(conn):
    with pytest.raises(ValueError):
        search_products(conn, order_by="Name")


def test_order_by_none_raises(conn):
    with pytest.raises(ValueError):
        search_products(conn, order_by=None)


def test_order_by_injection_attempt_raises(conn):
    with pytest.raises(ValueError):
        search_products(conn, order_by="name; DROP TABLE products")


# --- limit / offset -----------------------------------------------------

def test_default_limit_is_20(conn):
    rows = search_products(conn, name_contains="")
    assert len(rows) == 12  # fewer than 20 in stock, so no truncation
    for i in range(3, 20):
        conn.execute("INSERT INTO products VALUES (?, ?, ?, ?)", (100 + i, f"bulk{i:02d}", 1.0, 1))
    assert len(search_products(conn)) == 20


def test_limit_one(conn):
    assert len(search_products(conn, limit=1)) == 1


def test_limit_100_allowed(conn):
    assert len(search_products(conn, limit=100)) == 12


@pytest.mark.parametrize("bad", [0, -1, 101, 1000])
def test_limit_out_of_range_raises(conn, bad):
    with pytest.raises(ValueError):
        search_products(conn, limit=bad)


@pytest.mark.parametrize("bad", [1.0, "5", None, True])
def test_limit_wrong_type_raises(conn, bad):
    with pytest.raises(ValueError):
        search_products(conn, limit=bad)


def test_offset_zero_allowed(conn):
    assert search_products(conn, offset=0, limit=100) == search_products(conn, limit=100)


def test_offset_skips_rows(conn):
    all_ids = ids(search_products(conn, limit=100))
    assert ids(search_products(conn, offset=3, limit=100)) == all_ids[3:]


def test_offset_past_end_is_empty(conn):
    assert search_products(conn, offset=50) == []


def test_offset_applied_after_filter(conn):
    got = ids(search_products(conn, name_contains="apple", offset=1))
    assert got == [10]


def test_limit_applied_after_order(conn):
    got = ids(search_products(conn, order_by="price", descending=True, limit=2))
    assert got == [10, 5]


def test_limit_and_offset_window(conn):
    all_ids = ids(search_products(conn, order_by="price", limit=100))
    assert ids(search_products(conn, order_by="price", limit=3, offset=2)) == all_ids[2:5]


@pytest.mark.parametrize("bad", [-1, -100, 1.0, "0", None, False])
def test_offset_invalid_raises(conn, bad):
    with pytest.raises(ValueError):
        search_products(conn, offset=bad)


# --- result shape -------------------------------------------------------

def test_result_is_list_of_dicts_with_exact_keys(conn):
    rows = search_products(conn, name_contains="apple")
    assert isinstance(rows, list)
    assert all(isinstance(r, dict) for r in rows)
    assert all(set(r.keys()) == {"id", "name", "price"} for r in rows)


def test_result_values(conn):
    rows = search_products(conn, name_contains="apricot")
    assert rows == [{"id": 2, "name": "Apricot", "price": 2.00}]


def test_price_is_float_value(conn):
    rows = search_products(conn, name_contains="apple", limit=1)
    assert rows[0]["price"] == 1.5


# --- read-only ----------------------------------------------------------

def test_does_not_modify_database(conn):
    before = conn.execute("SELECT * FROM products ORDER BY id").fetchall()
    search_products(conn, name_contains="a", max_price=5, order_by="price", descending=True)
    after = conn.execute("SELECT * FROM products ORDER BY id").fetchall()
    assert before == after


def test_name_with_quote_is_safe(conn):
    assert search_products(conn, name_contains="' OR 1=1 --") == []
    assert len(conn.execute("SELECT * FROM products").fetchall()) == len(ROWS)
