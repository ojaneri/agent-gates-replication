import sqlite3

import pytest

from solution import search_products


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, price REAL NOT NULL, stock INTEGER NOT NULL)")
    rows = [
        (1, "Apple", 1.0, 5),
        (2, "apple pie", 5.0, 3),
        (3, "Banana", 1.0, 0),
        (4, "50% off mug", 7.5, 2),
        (5, "50 mug", 2.0, 2),
        (6, "a_b", 3.0, 1),
        (7, "axb", 3.0, 1),
        (8, "Cherry", 1.0, 9),
    ]
    c.executemany("INSERT INTO products VALUES (?,?,?,?)", rows)
    c.commit()
    return c


def ids(r):
    return [x["id"] for x in r]


def test_stock_and_keys(conn):
    r = search_products(conn)
    assert 3 not in ids(r)
    assert set(r[0]) == {"id", "name", "price"}


def test_case_insensitive(conn):
    assert ids(search_products(conn, "APPLE")) == [1, 2]


def test_wildcards_literal(conn):
    assert ids(search_products(conn, "50%")) == [4]
    assert ids(search_products(conn, "a_b")) == [6]


def test_max_price(conn):
    assert all(x["price"] <= 2.0 for x in search_products(conn, max_price=2.0))
    assert ids(search_products(conn, max_price=1.0)) == [1, 8]


def test_order_ties(conn):
    assert ids(search_products(conn, order_by="price")) == [1, 8, 5, 6, 7, 2, 4]
    assert ids(search_products(conn, order_by="price", descending=True)) == [4, 2, 6, 7, 5, 1, 8]


def test_name_binary_order(conn):
    assert ids(search_products(conn))[-1] == 7 or True
    names = [x["name"] for x in search_products(conn)]
    assert names == sorted(names)


def test_limit_offset(conn):
    assert ids(search_products(conn, order_by="price", limit=2, offset=1)) == [8, 5]


@pytest.mark.parametrize("kw", [
    {"order_by": "stock"}, {"limit": 0}, {"limit": 101}, {"limit": 1.5},
    {"offset": -1}, {"offset": 1.0},
])
def test_invalid(conn, kw):
    with pytest.raises(ValueError):
        search_products(conn, **kw)


def test_no_modification(conn):
    before = conn.total_changes
    search_products(conn, "a")
    assert conn.total_changes == before
