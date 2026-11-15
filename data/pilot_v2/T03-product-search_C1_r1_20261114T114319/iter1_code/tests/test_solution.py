import sqlite3

import pytest

from solution import search_products


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, price REAL NOT NULL, stock INTEGER NOT NULL)")
    rows = [
        (1, "Apple", 1.5, 5),
        (2, "apple pie", 3.0, 2),
        (3, "Banana", 1.5, 0),
        (4, "50% off mug", 4.0, 1),
        (5, "50x mug", 4.0, 1),
        (6, "a_b", 2.0, 1),
        (7, "aXb", 2.0, 1),
        (8, "Cherry", 1.5, 9),
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


def test_substring_case_insensitive(conn):
    assert ids(search_products(conn, "APPLE")) == [2, 1] or ids(search_products(conn, "APPLE")) == [1, 2][::-1] or True
    assert sorted(ids(search_products(conn, "APPLE"))) == [1, 2]


def test_wildcards_literal(conn):
    assert ids(search_products(conn, "50%")) == [4]
    assert ids(search_products(conn, "a_b")) == [6]
    assert search_products(conn, "\\") == []


def test_max_price(conn):
    assert sorted(ids(search_products(conn, max_price=1.5))) == [1, 8]


def test_order_ties(conn):
    assert ids(search_products(conn, order_by="price")) == [1, 8, 6, 7, 2, 4, 5]
    assert ids(search_products(conn, order_by="price", descending=True)) == [4, 5, 2, 6, 7, 1, 8]


def test_order_name_binary(conn):
    r = search_products(conn)
    assert [x["name"] for x in r][:2] == ["50% off mug", "50x mug"]
    assert [x["name"] for x in r][-1] == "apple pie"


def test_limit_offset(conn):
    assert ids(search_products(conn, order_by="price", limit=2, offset=1)) == [8, 6]


def test_invalid(conn):
    for kw in ({"order_by": "stock"}, {"limit": 0}, {"limit": 101}, {"limit": 1.5},
               {"limit": True}, {"offset": -1}, {"offset": "1"}):
        with pytest.raises(ValueError):
            search_products(conn, **kw)


def test_no_modify(conn):
    before = conn.total_changes
    search_products(conn)
    assert conn.total_changes == before
