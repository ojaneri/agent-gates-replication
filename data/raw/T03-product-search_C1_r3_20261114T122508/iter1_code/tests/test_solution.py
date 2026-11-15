import sqlite3

import pytest

from solution import search_products


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, price REAL NOT NULL, stock INTEGER NOT NULL)")
    rows = [
        (1, "Apple", 1.0, 5),
        (2, "apple pie", 5.0, 2),
        (3, "50% Off Mug", 3.0, 1),
        (4, "50 Off Mug", 3.0, 1),
        (5, "a_b", 2.0, 1),
        (6, "axb", 2.0, 1),
        (7, "Banana", 1.0, 0),
        (8, "Cherry", 1.0, 9),
    ]
    c.executemany("INSERT INTO products VALUES (?,?,?,?)", rows)
    return c


def ids(res):
    return [r["id"] for r in res]


def test_stock_filter_and_keys(conn):
    res = search_products(conn)
    assert 7 not in ids(res)
    assert set(res[0]) == {"id", "name", "price"}


def test_name_case_insensitive(conn):
    assert ids(search_products(conn, "APPLE")) == [1, 2]


def test_wildcards_literal(conn):
    assert ids(search_products(conn, "50%")) == [3]
    assert ids(search_products(conn, "a_b")) == [5]


def test_max_price(conn):
    assert ids(search_products(conn, max_price=2.0, order_by="price")) == [1, 8, 5, 6]


def test_order_desc_ties_by_id(conn):
    assert ids(search_products(conn, order_by="price", descending=True)) == [2, 3, 4, 5, 6, 1, 8]


def test_order_name_binary(conn):
    assert ids(search_products(conn))[:2] == [4, 3]
    assert ids(search_products(conn))[-2:] == [2, 6]


def test_limit_offset(conn):
    assert ids(search_products(conn, order_by="price", limit=2, offset=1)) == [8, 5]


@pytest.mark.parametrize("kw", [
    {"order_by": "stock"}, {"limit": 0}, {"limit": 101}, {"limit": 1.5},
    {"limit": True}, {"offset": -1}, {"offset": "1"},
])
def test_invalid(conn, kw):
    with pytest.raises(ValueError):
        search_products(conn, **kw)
