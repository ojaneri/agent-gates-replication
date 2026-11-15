import sqlite3
import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from solution import search_products  # noqa: E402


ROWS = [
    (1, "Apple", 1.50, 10),
    (2, "apricot", 2.00, 5),
    (3, "Banana", 0.75, 0),      # out of stock
    (4, "50% off cherry", 3.00, 4),
    (5, "Under_score", 4.00, 2),
    (6, "UNDERSCORE plain", 4.00, 1),
    (7, "Blueberry", 2.00, 8),
    (8, "Zucchini", 1.50, 3),
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


def ids(results):
    return [r["id"] for r in results]


def test_excludes_out_of_stock(conn):
    assert 3 not in ids(search_products(conn))


def test_result_has_exact_keys(conn):
    for r in search_products(conn):
        assert set(r.keys()) == {"id", "name", "price"}


def test_default_order_is_name_binary(conn):
    # Binary ordering: uppercase before lowercase.
    names = [r["name"] for r in search_products(conn, limit=100)]
    assert names == sorted(names)


def test_name_contains_case_insensitive_ascii(conn):
    assert ids(search_products(conn, name_contains="APPLE")) == [1]
    assert ids(search_products(conn, name_contains="apr")) == [2]


def test_empty_name_contains_matches_all_in_stock(conn):
    assert len(search_products(conn, name_contains="", limit=100)) == 7


def test_percent_is_literal(conn):
    assert ids(search_products(conn, name_contains="50%")) == [4]
    assert ids(search_products(conn, name_contains="%")) == [4]
    assert search_products(conn, name_contains="5%x") == []


def test_underscore_is_literal(conn):
    assert ids(search_products(conn, name_contains="_")) == [5]
    assert search_products(conn, name_contains="e_p") == []


def test_max_price_inclusive(conn):
    res = search_products(conn, max_price=2.0, limit=100)
    assert all(r["price"] <= 2.0 for r in res)
    assert 2 in ids(res) and 7 in ids(res)
    assert 5 not in ids(res)


def test_order_by_price_ascending_tie_by_id(conn):
    res = search_products(conn, order_by="price", limit=100)
    assert ids(res) == [1, 8, 2, 7, 4, 5, 6]


def test_order_by_price_descending_tie_still_id_ascending(conn):
    res = search_products(conn, order_by="price", descending=True, limit=100)
    assert ids(res) == [5, 6, 4, 2, 7, 1, 8]


def test_order_by_name_descending(conn):
    res = search_products(conn, descending=True, limit=100)
    names = [r["name"] for r in res]
    assert names == sorted(names, reverse=True)


def test_invalid_order_by_raises(conn):
    with pytest.raises(ValueError):
        search_products(conn, order_by="stock")


@pytest.mark.parametrize("limit", [0, 101, -1, 1.0, "5", True])
def test_invalid_limit_raises(conn, limit):
    with pytest.raises(ValueError):
        search_products(conn, limit=limit)


@pytest.mark.parametrize("offset", [-1, 0.0, "1", False])
def test_invalid_offset_raises(conn, offset):
    with pytest.raises(ValueError):
        search_products(conn, offset=offset)


def test_limit_and_offset_applied_after_ordering(conn):
    all_ids = ids(search_products(conn, order_by="price", limit=100))
    page = ids(search_products(conn, order_by="price", limit=2, offset=2))
    assert page == all_ids[2:4]


def test_limit_bounds_accepted(conn):
    assert len(search_products(conn, limit=1)) == 1
    assert len(search_products(conn, limit=100)) == 7


def test_does_not_modify_database(conn):
    before = conn.execute("SELECT * FROM products ORDER BY id").fetchall()
    search_products(conn, name_contains="a", max_price=3, order_by="price", descending=True)
    after = conn.execute("SELECT * FROM products ORDER BY id").fetchall()
    assert before == after
