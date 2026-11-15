import sqlite3

import pytest

from solution import search_products


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, price REAL NOT NULL, stock INTEGER NOT NULL)")
    c.executemany("INSERT INTO products VALUES (?,?,?,?)", [
        (1, "Apple", 2.0, 5),
        (2, "apple pie", 5.0, 1),
        (3, "Banana", 2.0, 0),
        (4, "50% off mug", 3.0, 2),
        (5, "50 mug", 3.0, 2),
        (6, "a_b", 1.0, 1),
        (7, "axb", 1.0, 1),
        (8, "Cherry", 2.0, 9),
    ])
    return c


def ids(rows):
    return [r["id"] for r in rows]


def test_stock_and_keys(conn):
    rows = search_products(conn, limit=100)
    assert 3 not in ids(rows)
    assert set(rows[0]) == {"id", "name", "price"}


def test_case_insensitive_and_empty(conn):
    assert ids(search_products(conn, "APPLE")) == [1, 2]
    assert len(search_products(conn, "")) == 7


def test_wildcards_literal(conn):
    assert ids(search_products(conn, "50%")) == [4]
    assert ids(search_products(conn, "a_b")) == [6]
    assert ids(search_products(conn, "\\")) == []


def test_max_price(conn):
    assert ids(search_products(conn, max_price=2.0, order_by="price")) == [6, 7, 1, 8]


def test_order_and_ties(conn):
    assert ids(search_products(conn, order_by="price")) == [6, 7, 1, 8, 4, 5, 2]
    assert ids(search_products(conn, order_by="price", descending=True)) == [2, 4, 5, 1, 8, 6, 7]
    assert ids(search_products(conn))[:2] == [5, 4]  # binary order: digits first
    assert ids(search_products(conn, descending=True))[0] == 7  # lowercase last: "axb" > "apple pie"


def test_limit_offset(conn):
    assert ids(search_products(conn, order_by="price", limit=2, offset=1)) == [7, 1]


@pytest.mark.parametrize("kw", [
    {"order_by": "stock"}, {"limit": 0}, {"limit": 101}, {"limit": "5"},
    {"limit": True}, {"offset": -1}, {"offset": 1.5},
])
def test_invalid(conn, kw):
    with pytest.raises(ValueError):
        search_products(conn, **kw)
