import sqlite3

import pytest

from solution import search_products

ROWS = [
    (1, "Widget", 10.0, 5),
    (2, "widget pro", 25.0, 3),
    (3, "Gadget", 10.0, 0),
    (4, "50% Off Banner", 5.0, 2),
    (5, "500 Club", 7.5, 1),
    (6, "snake_case mug", 12.0, 4),
    (7, "snake-case mug", 12.0, 4),
    (8, "Bolt", 10.0, 9),
    (9, "Anchor", 30.0, 1),
]


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, price REAL NOT NULL, "
              "stock INTEGER NOT NULL)")
    c.executemany("INSERT INTO products VALUES (?, ?, ?, ?)", ROWS)
    c.commit()
    yield c
    c.close()


def ids(rows):
    return [r["id"] for r in rows]


def test_default_in_stock_ordered_by_name(conn):
    assert ids(search_products(conn)) == [4, 5, 9, 8, 1, 7, 6, 2]


def test_out_of_stock_excluded(conn):
    assert 3 not in ids(search_products(conn, "gadget"))


def test_case_insensitive_substring(conn):
    assert ids(search_products(conn, "WIDGET")) == [1, 2]


def test_percent_is_literal(conn):
    assert ids(search_products(conn, "50%")) == [4]


def test_underscore_is_literal(conn):
    assert ids(search_products(conn, "snake_case")) == [6]


def test_backslash_does_not_break(conn):
    assert search_products(conn, "a\\b") == []


def test_quote_in_search_is_safe(conn):
    assert search_products(conn, "it's") == []


def test_max_price_inclusive(conn):
    assert ids(search_products(conn, max_price=10.0)) == [4, 5, 8, 1]


def test_order_by_price_ties_by_id(conn):
    assert ids(search_products(conn, order_by="price")) == [4, 5, 1, 8, 6, 7, 2, 9]


def test_order_by_price_descending_ties_still_by_id_ascending(conn):
    assert ids(search_products(conn, order_by="price", descending=True)) == [9, 2, 6, 7, 1, 8, 5, 4]


def test_order_by_name_descending(conn):
    assert ids(search_products(conn, descending=True)) == [2, 6, 7, 1, 8, 9, 5, 4]


def test_limit_and_offset(conn):
    assert ids(search_products(conn, order_by="price", limit=3, offset=2)) == [1, 8, 6]


def test_limit_bounds_accepted(conn):
    assert len(search_products(conn, limit=1)) == 1
    assert len(search_products(conn, limit=100)) == 8


@pytest.mark.parametrize("limit", [0, 101, -1, True, 2.5])
def test_invalid_limit(conn, limit):
    with pytest.raises(ValueError):
        search_products(conn, limit=limit)


def test_invalid_offset(conn):
    with pytest.raises(ValueError):
        search_products(conn, offset=-1)


@pytest.mark.parametrize("order_by", ["id", "stock", "", "NAME"])
def test_invalid_order_by(conn, order_by):
    with pytest.raises(ValueError):
        search_products(conn, order_by=order_by)


def test_injection_in_order_by_rejected_and_harmless(conn):
    with pytest.raises(ValueError):
        search_products(conn, order_by="name; DROP TABLE products")
    with pytest.raises(ValueError):
        search_products(conn, order_by="(SELECT 1)")
    assert conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 9


def test_result_shape(conn):
    r = search_products(conn, "Bolt")
    assert r == [{"id": 8, "name": "Bolt", "price": 10.0}]


def test_does_not_modify_database(conn):
    before = conn.total_changes
    search_products(conn, "w", max_price=50, order_by="price", descending=True, limit=5, offset=1)
    assert conn.total_changes == before


def test_empty_table():
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, price REAL NOT NULL, "
              "stock INTEGER NOT NULL)")
    assert search_products(c) == []
