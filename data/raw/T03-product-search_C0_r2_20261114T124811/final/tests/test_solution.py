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
        (4, "50% off mug", 7.5, 1),
        (5, "50x mug", 2.0, 1),
        (6, "a_b", 3.0, 1),
        (7, "axb", 3.0, 1),
        (8, "Cherry", 1.0, 2),
    ]
    c.executemany("INSERT INTO products VALUES (?,?,?,?)", rows)
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
    assert ids(search_products(conn, max_price=2.0, order_by="price")) == [1, 8, 5]


def test_order_desc_ties_by_id(conn):
    assert ids(search_products(conn, order_by="price", descending=True))[:3] == [4, 2, 6]
    assert ids(search_products(conn, order_by="price", descending=True)) [3:5] == [7, 5]


def test_binary_name_order(conn):
    r = search_products(conn)
    assert r[0]["name"] == "50% off mug"
    assert [x["name"] for x in r].index("Cherry") < [x["name"] for x in r].index("a_b")


def test_limit_offset(conn):
    assert ids(search_products(conn, order_by="price", limit=2, offset=1)) == [8, 5]


@pytest.mark.parametrize("kw", [
    {"order_by": "stock"}, {"limit": 0}, {"limit": 101}, {"limit": 1.5},
    {"offset": -1}, {"offset": 1.0}, {"limit": True},
])
def test_invalid(conn, kw):
    with pytest.raises(ValueError):
        search_products(conn, **kw)
