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
        (7, "axb", 2.0, 1),
        (8, "Zed", 2.0, 3),
        (9, "back\\slash", 9.0, 1),
    ]
    c.executemany("INSERT INTO products VALUES (?,?,?,?)", rows)
    return c


def ids(r):
    return [x["id"] for x in r]


def test_stock_and_keys(conn):
    r = search_products(conn)
    assert 3 not in ids(r)
    assert set(r[0]) == {"id", "name", "price"}
    assert r[0] == {"id": 4, "name": "50% off", "price": 3.0}


def test_name_order_binary(conn):
    names = [x["name"] for x in search_products(conn)]
    assert names == sorted(names)


def test_case_insensitive(conn):
    assert ids(search_products(conn, "APPLE")) == [1, 2]


def test_wildcards_literal(conn):
    assert ids(search_products(conn, "50%")) == [4]
    assert ids(search_products(conn, "a_b")) == [6]
    assert ids(search_products(conn, "\\")) == [9]


def test_max_price(conn):
    assert ids(search_products(conn, max_price=2.0, order_by="price")) == [1, 6, 7, 8]
    assert ids(search_products(conn, max_price=1.5)) == []


def test_price_order_ties(conn):
    assert ids(search_products(conn, order_by="price")) == [1, 6, 7, 8, 4, 5, 2, 9]
    assert ids(search_products(conn, order_by="price", descending=True)) == [9, 2, 4, 5, 1, 6, 7, 8]


def test_name_desc(conn):
    names = [x["name"] for x in search_products(conn, descending=True)]
    assert names == sorted(names, reverse=True)


def test_limit_offset(conn):
    assert ids(search_products(conn, order_by="price", limit=2)) == [1, 6]
    assert ids(search_products(conn, order_by="price", limit=2, offset=2)) == [7, 8]
    assert search_products(conn, limit=100, offset=50) == []


@pytest.mark.parametrize("kw", [
    {"order_by": "stock"}, {"limit": 0}, {"limit": 101}, {"limit": 1.5},
    {"limit": True}, {"offset": -1}, {"offset": 1.0}, {"offset": True},
])
def test_invalid(conn, kw):
    with pytest.raises(ValueError):
        search_products(conn, **kw)


def test_limit_bounds_ok(conn):
    assert len(search_products(conn, limit=1)) == 1
    assert len(search_products(conn, limit=100)) == 8


def test_no_modification(conn):
    before = conn.total_changes
    search_products(conn, "a")
    assert conn.total_changes == before
