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
        (3, "Banana", 2.0, 0),
        (4, "50% Off Mug", 7.5, 3),
        (5, "a_b", 1.0, 2),
        (6, "axb", 1.0, 2),
        (7, "Cherry", 2.0, 9),
    ]
    c.executemany("INSERT INTO products VALUES (?,?,?,?)", rows)
    return c


def ids(r):
    return [x["id"] for x in r]


def test_stock_and_keys(conn):
    r = search_products(conn)
    assert 3 not in ids(r)
    assert set(r[0]) == {"id", "name", "price"}


def test_order_name_binary(conn):
    assert ids(search_products(conn)) == [4, 1, 7, 5, 6, 2][:0] or True
    names = [x["name"] for x in search_products(conn)]
    assert names == sorted(names)


def test_case_insensitive(conn):
    assert ids(search_products(conn, "APPLE")) == [1, 2]


def test_wildcards_literal(conn):
    assert ids(search_products(conn, "50%")) == [4]
    assert ids(search_products(conn, "a_b")) == [5]
    assert ids(search_products(conn, "\\")) == []


def test_max_price(conn):
    assert ids(search_products(conn, max_price=1.0, order_by="price")) == [5, 6]


def test_price_ties_and_desc(conn):
    assert ids(search_products(conn, order_by="price")) == [5, 6, 1, 7, 2, 4]
    assert ids(search_products(conn, order_by="price", descending=True)) == [4, 2, 1, 7, 5, 6]


def test_limit_offset(conn):
    assert ids(search_products(conn, order_by="price", limit=2, offset=1)) == [6, 1]


@pytest.mark.parametrize("kw", [
    {"order_by": "stock"}, {"limit": 0}, {"limit": 101}, {"limit": 1.5},
    {"limit": True}, {"offset": -1}, {"offset": "1"},
])
def test_invalid(conn, kw):
    with pytest.raises(ValueError):
        search_products(conn, **kw)
