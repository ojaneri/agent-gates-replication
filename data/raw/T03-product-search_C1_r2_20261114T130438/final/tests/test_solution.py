import os
import sqlite3
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from solution import search_products  # noqa: E402


ROWS = [
    (1, "Apple", 1.50, 10),
    (2, "banana", 0.25, 5),
    (3, "Cherry", 3.00, 0),      # out of stock
    (4, "apricot", 2.00, 7),
    (5, "Dragonfruit", 5.00, 2),
    (6, "50% off mango", 4.00, 1),
    (7, "snake_case_item", 1.00, 3),
    (8, "Pear", 1.50, 4),        # ties with Apple on price
    (9, "BANANA split", 6.00, 9),
]


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, "
              "price REAL NOT NULL, stock INTEGER NOT NULL)")
    c.executemany("INSERT INTO products VALUES (?, ?, ?, ?)", ROWS)
    c.commit()
    yield c
    c.close()


def ids(results):
    return [r["id"] for r in results]


def test_default_returns_in_stock_sorted_by_name(conn):
    res = search_products(conn)
    # Binary ordering: uppercase before lowercase.
    assert [r["name"] for r in res] == [
        "50% off mango", "Apple", "BANANA split", "Dragonfruit", "Pear",
        "apricot", "banana", "snake_case_item",
    ]


def test_out_of_stock_excluded(conn):
    assert 3 not in ids(search_products(conn, limit=100))


def test_result_keys_exact(conn):
    res = search_products(conn, limit=1)
    assert set(res[0].keys()) == {"id", "name", "price"}
    assert res[0] == {"id": 6, "name": "50% off mango", "price": 4.0}


def test_name_contains_case_insensitive_ascii(conn):
    res = search_products(conn, name_contains="BaNaNa")
    assert ids(res) == [9, 2]


def test_name_contains_empty_matches_all_in_stock(conn):
    assert len(search_products(conn, name_contains="", limit=100)) == 8


def test_percent_is_literal(conn):
    assert ids(search_products(conn, name_contains="50%")) == [6]


def test_percent_alone_does_not_match_everything(conn):
    assert ids(search_products(conn, name_contains="%")) == [6]


def test_underscore_is_literal(conn):
    assert ids(search_products(conn, name_contains="_")) == [7]


def test_underscore_not_wildcard(conn):
    assert search_products(conn, name_contains="s_ake") == []
    assert ids(search_products(conn, name_contains="snake_case")) == [7]


def test_no_match_returns_empty(conn):
    assert search_products(conn, name_contains="zzz") == []


def test_non_ascii_not_folded(conn):
    conn.execute("INSERT INTO products VALUES (100, 'Éclair', 2.0, 1)")
    assert search_products(conn, name_contains="éclair") == []
    assert ids(search_products(conn, name_contains="Éclair")) == [100]


def test_max_price_filter_inclusive(conn):
    res = search_products(conn, max_price=1.5, limit=100)
    assert all(r["price"] <= 1.5 for r in res)
    assert {1, 2, 7, 8} == set(ids(res))


def test_max_price_none_no_filter(conn):
    assert len(search_products(conn, max_price=None, limit=100)) == 8


def test_order_by_price_ascending_ties_by_id(conn):
    res = search_products(conn, order_by="price", limit=100)
    assert ids(res) == [2, 7, 1, 8, 4, 6, 5, 9]


def test_order_by_price_descending_ties_still_by_id(conn):
    res = search_products(conn, order_by="price", descending=True, limit=100)
    assert ids(res) == [9, 5, 6, 4, 1, 8, 7, 2]


def test_order_by_name_descending(conn):
    res = search_products(conn, descending=True, limit=100)
    assert [r["name"] for r in res] == [
        "snake_case_item", "banana", "apricot", "Pear", "Dragonfruit",
        "BANANA split", "Apple", "50% off mango",
    ]


def test_name_ties_broken_by_id(conn):
    conn.execute("INSERT INTO products VALUES (50, 'Apple', 9.0, 1)")
    res = search_products(conn, name_contains="apple")
    assert ids(res) == [1, 50]
    res_desc = search_products(conn, name_contains="apple", descending=True)
    assert ids(res_desc) == [1, 50]


def test_price_ties_broken_by_id_when_descending(conn):
    conn.execute("INSERT INTO products VALUES (0, 'Zero', 1.5, 1)")
    res = search_products(conn, order_by="price", descending=True, limit=100)
    tied = [r["id"] for r in res if r["price"] == 1.5]
    assert tied == [0, 1, 8]


def test_invalid_order_by_raises(conn):
    with pytest.raises(ValueError):
        search_products(conn, order_by="stock")
    with pytest.raises(ValueError):
        search_products(conn, order_by="id")
    with pytest.raises(ValueError):
        search_products(conn, order_by="name; DROP TABLE products")


def test_order_by_non_string_raises(conn):
    with pytest.raises(ValueError):
        search_products(conn, order_by=None)


@pytest.mark.parametrize("limit", [0, -1, 101, 1.0, "5", None, True])
def test_invalid_limit_raises(conn, limit):
    with pytest.raises(ValueError):
        search_products(conn, limit=limit)


@pytest.mark.parametrize("limit", [1, 100])
def test_limit_bounds_accepted(conn, limit):
    assert len(search_products(conn, limit=limit)) <= limit


@pytest.mark.parametrize("offset", [-1, 1.0, "0", None, False])
def test_invalid_offset_raises(conn, offset):
    with pytest.raises(ValueError):
        search_products(conn, offset=offset)


def test_limit_and_offset_applied_after_ordering(conn):
    all_ids = ids(search_products(conn, limit=100))
    assert ids(search_products(conn, limit=3, offset=0)) == all_ids[0:3]
    assert ids(search_products(conn, limit=3, offset=3)) == all_ids[3:6]
    assert search_products(conn, limit=5, offset=100) == []


def test_limit_after_filter(conn):
    res = search_products(conn, name_contains="a", limit=2)
    assert len(res) == 2


def test_non_string_name_contains_raises(conn):
    with pytest.raises(ValueError):
        search_products(conn, name_contains=None)


def test_does_not_modify_database(conn):
    before = conn.execute("SELECT * FROM products ORDER BY id").fetchall()
    search_products(conn, name_contains="a", max_price=5, order_by="price", descending=True)
    after = conn.execute("SELECT * FROM products ORDER BY id").fetchall()
    assert before == after


def test_empty_table(conn):
    conn.execute("DELETE FROM products")
    assert search_products(conn) == []
