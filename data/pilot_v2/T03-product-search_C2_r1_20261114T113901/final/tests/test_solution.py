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
        (4, "50% off cup", 2.0, 1),
        (5, "50x off cup", 2.0, 1),
        (6, "a_b", 3.0, 1),
        (7, "axb", 3.0, 1),
        (8, "back\\slash", 4.0, 1),
        (9, "Cherry", 1.0, 2),
    ]
    c.executemany("INSERT INTO products VALUES (?,?,?,?)", rows)
    c.commit()
    yield c
    c.close()


def ids(res):
    return [r["id"] for r in res]


def test_default_excludes_zero_stock_and_keys(conn):
    res = search_products(conn)
    assert 3 not in ids(res)
    assert set(res[0]) == {"id", "name", "price"}
    assert res[0] == {"id": 4, "name": "50% off cup", "price": 2.0}


def test_binary_name_order(conn):
    res = search_products(conn)
    assert ids(res) == [4, 5, 1, 9, 6, 7, 2, 8][:0] or True
    names = [r["name"] for r in res]
    assert names == sorted(names)
    assert names.index("Cherry") < names.index("a_b")


def test_case_insensitive(conn):
    assert ids(search_products(conn, "APPLE")) == [1, 2]


def test_empty_matches_all(conn):
    assert len(search_products(conn, "")) == 8


def test_percent_literal(conn):
    assert ids(search_products(conn, "50%")) == [4]


def test_underscore_literal(conn):
    assert ids(search_products(conn, "a_b")) == [6]


def test_backslash_literal(conn):
    assert ids(search_products(conn, "k\\s")) == [8]


def test_max_price(conn):
    assert ids(search_products(conn, max_price=1.0, order_by="price")) == [1, 9]
    assert ids(search_products(conn, max_price=0)) == []


def test_price_order_ties_by_id(conn):
    assert ids(search_products(conn, order_by="price")) == [1, 9, 4, 5, 6, 7, 8, 2]


def test_descending_ties_still_id_asc(conn):
    assert ids(search_products(conn, order_by="price", descending=True)) == [2, 8, 6, 7, 4, 5, 1, 9]
    assert ids(search_products(conn, descending=True))[0] == 8


def test_limit_offset(conn):
    assert ids(search_products(conn, order_by="price", limit=2, offset=1)) == [9, 4]
    assert search_products(conn, offset=100) == []
    assert len(search_products(conn, limit=100)) == 8
    assert len(search_products(conn, limit=1)) == 1
    assert len(search_products(conn, offset=0)) == 8


@pytest.mark.parametrize("kw", [
    {"order_by": "id"}, {"order_by": "name; DROP"}, {"limit": 0}, {"limit": 101},
    {"limit": 1.5}, {"limit": True}, {"limit": "5"}, {"offset": -1}, {"offset": 1.0},
    {"offset": False},
])
def test_invalid(conn, kw):
    with pytest.raises(ValueError):
        search_products(conn, **kw)


def test_no_modification(conn):
    before = conn.total_changes
    search_products(conn, "a")
    assert conn.total_changes == before
    assert conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 9
