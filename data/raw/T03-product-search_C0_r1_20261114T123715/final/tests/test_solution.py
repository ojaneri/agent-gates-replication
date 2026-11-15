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
        (3, "Banana", 1.0, 0),
        (4, "50% Off Mug", 5.0, 3),
        (5, "a_b", 3.0, 2),
        (6, "axb", 3.0, 2),
        (7, "Zed", 2.0, 9),
    ])
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
    assert ids(search_products(conn, "a_b")) == [5]
    assert ids(search_products(conn, "%")) == [4]


def test_max_price(conn):
    assert ids(search_products(conn, max_price=2.0, order_by="price")) == [1, 7]


def test_order_ties(conn):
    assert ids(search_products(conn, order_by="price")) == [1, 7, 5, 6, 2, 4]
    assert ids(search_products(conn, order_by="price", descending=True)) == [2, 4, 5, 6, 1, 7]


def test_name_binary_order(conn):
    r = search_products(conn)
    assert ids(r) == [4, 1, 7, 5, 2, 6]


def test_limit_offset(conn):
    assert ids(search_products(conn, order_by="price", limit=2, offset=1)) == [7, 5]


@pytest.mark.parametrize("kw", [
    {"order_by": "stock"}, {"limit": 0}, {"limit": 101}, {"limit": 1.5},
    {"offset": -1}, {"offset": "0"}, {"limit": True},
])
def test_invalid(conn, kw):
    with pytest.raises(ValueError):
        search_products(conn, **kw)
