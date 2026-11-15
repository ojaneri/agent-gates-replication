import sqlite3

import pytest

from solution import search_products


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, price REAL NOT NULL, stock INTEGER NOT NULL)")
    rows = [
        (1, "Apple", 2.0, 5),
        (2, "apple pie", 5.0, 3),
        (3, "Banana", 1.0, 0),
        (4, "banana split", 5.0, 2),
        (5, "50% off sale", 9.5, 1),
        (6, "a_b", 3.0, 1),
        (7, "axb", 3.0, 1),
        (8, "Zed", 5.0, 4),
    ]
    c.executemany("INSERT INTO products VALUES (?,?,?,?)", rows)
    c.commit()
    return c


def ids(res):
    return [r["id"] for r in res]


def test_stock_filter_and_keys(conn):
    res = search_products(conn)
    assert 3 not in ids(res)
    assert set(res[0]) == {"id", "name", "price"}
    assert res[0] == {"id": 5, "name": "50% off sale", "price": 9.5}


def test_name_order_binary(conn):
    assert ids(search_products(conn)) == [5, 1, 8, 6, 2, 7, 4]
    names = [r["name"] for r in search_products(conn)]
    assert names == sorted(names)
    assert names.index("Zed") < names.index("a_b")


def test_substring_case_insensitive(conn):
    assert ids(search_products(conn, "APPLE")) == [1, 2]
    assert ids(search_products(conn, "")) == ids(search_products(conn))


def test_wildcards_literal(conn):
    assert ids(search_products(conn, "50%")) == [5]
    assert ids(search_products(conn, "%")) == [5]
    assert ids(search_products(conn, "a_b")) == [6]
    assert ids(search_products(conn, "_")) == [6]


def test_backslash_literal(conn):
    conn.execute("INSERT INTO products VALUES (9, 'x\\y', 1.0, 1)")
    assert ids(search_products(conn, "\\")) == [9]
    assert ids(search_products(conn, "x\\y")) == [9]


def test_max_price_inclusive(conn):
    assert ids(search_products(conn, max_price=5.0, order_by="price")) == [1, 6, 7, 2, 4, 8]
    assert ids(search_products(conn, max_price=0.5)) == []
    assert ids(search_products(conn, max_price=0)) == []


def test_order_price_ties_by_id(conn):
    assert ids(search_products(conn, order_by="price")) == [1, 6, 7, 2, 4, 8, 5]
    assert ids(search_products(conn, order_by="price", descending=True)) == [5, 2, 4, 8, 6, 7, 1]


def test_descending_name(conn):
    names = [r["name"] for r in search_products(conn, descending=True)]
    assert names == sorted(names, reverse=True)


def test_limit_offset(conn):
    assert ids(search_products(conn, order_by="price", limit=2)) == [1, 6]
    assert ids(search_products(conn, order_by="price", limit=2, offset=2)) == [7, 2]
    assert search_products(conn, offset=100) == []


@pytest.mark.parametrize("kw", [
    {"order_by": "stock"}, {"order_by": ""}, {"limit": 0}, {"limit": 101}, {"limit": -1},
    {"limit": 1.5}, {"limit": "5"}, {"limit": True}, {"offset": -1}, {"offset": 1.0},
    {"offset": True},
])
def test_invalid(conn, kw):
    with pytest.raises(ValueError):
        search_products(conn, **kw)


def test_limit_bounds_ok(conn):
    assert len(search_products(conn, limit=1)) == 1
    assert len(search_products(conn, limit=100)) == 7


def test_no_modification(conn):
    before = conn.execute("SELECT * FROM products").fetchall()
    search_products(conn, "a")
    assert conn.execute("SELECT * FROM products").fetchall() == before
    assert not conn.in_transaction
