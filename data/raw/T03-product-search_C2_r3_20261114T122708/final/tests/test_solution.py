import sqlite3

import pytest

from solution import search_products


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, price REAL NOT NULL, stock INTEGER NOT NULL)")
    rows = [
        (1, "Apple", 2.0, 5),
        (2, "apple pie", 5.0, 1),
        (3, "Banana", 1.0, 0),
        (4, "50% off", 3.0, 2),
        (5, "50x off", 3.0, 2),
        (6, "a_b", 2.0, 1),
        (7, "azb", 2.0, 1),
        (8, "back\\slash", 9.0, 1),
        (9, "Zed", 2.0, 1),
    ]
    c.executemany("INSERT INTO products VALUES (?,?,?,?)", rows)
    return c


def ids(res):
    return [r["id"] for r in res]


def test_stock_and_keys(conn):
    res = search_products(conn, limit=100)
    assert 3 not in ids(res)
    assert set(res[0]) == {"id", "name", "price"}
    assert res[0] == {"id": 4, "name": "50% off", "price": 3.0}


def test_substring_case_insensitive(conn):
    assert ids(search_products(conn, "APPLE")) == [1, 2]
    assert ids(search_products(conn, "pie")) == [2]


def test_wildcards_literal(conn):
    assert ids(search_products(conn, "50%")) == [4]
    assert ids(search_products(conn, "a_b")) == [6]
    assert ids(search_products(conn, "\\")) == [8]
    assert ids(search_products(conn, "%")) == [4]


def test_max_price(conn):
    assert ids(search_products(conn, max_price=2.0, order_by="price")) == [1, 6, 7, 9]
    assert 2 not in ids(search_products(conn, max_price=4.99))
    assert 2 in ids(search_products(conn, max_price=5.0))
    assert ids(search_products(conn, max_price=0)) == []


def test_ordering(conn):
    assert ids(search_products(conn, order_by="name")) == [4, 5, 1, 9, 6, 2, 7, 8]
    assert ids(search_products(conn, order_by="name", descending=True)) == [8, 7, 2, 6, 9, 1, 5, 4]
    assert ids(search_products(conn, order_by="price")) == [1, 6, 7, 9, 4, 5, 2, 8]
    assert ids(search_products(conn, order_by="price", descending=True)) == [8, 2, 4, 5, 1, 6, 7, 9]


def test_limit_offset(conn):
    assert ids(search_products(conn, order_by="price", limit=2)) == [1, 6]
    assert ids(search_products(conn, order_by="price", limit=2, offset=2)) == [7, 9]
    assert ids(search_products(conn, order_by="price", limit=100, offset=20)) == []


@pytest.mark.parametrize("kw", [
    {"order_by": "id"}, {"order_by": "name; DROP"}, {"limit": 0}, {"limit": 101},
    {"limit": 1.5}, {"limit": True}, {"offset": -1}, {"offset": 1.0}, {"offset": True},
])
def test_invalid(conn, kw):
    with pytest.raises(ValueError):
        search_products(conn, **kw)


def test_boundaries_valid(conn):
    assert len(search_products(conn, limit=1)) == 1
    assert len(search_products(conn, limit=100, offset=0)) == 8


def test_no_modification(conn):
    before = conn.total_changes
    search_products(conn)
    assert conn.total_changes == before
    assert conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 9
