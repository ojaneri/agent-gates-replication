import sqlite3

import pytest

from solution import search_products


ROWS = [
    (1, "Apple", 1.50, 10),
    (2, "apricot", 2.00, 5),
    (3, "Banana", 0.75, 0),      # out of stock: must never appear
    (4, "cherry 50% off", 3.00, 2),
    (5, "Date_palm", 4.00, 1),
    (6, "Elderberry", 2.00, 7),
    (7, "fig", 1.50, 3),
    (8, "Grape", 2.50, 4),
    (9, "grapefruit", 1.50, 1),
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


def test_default_returns_in_stock_sorted_by_name_binary(conn):
    # Binary ordering: uppercase before lowercase.
    res = search_products(conn, limit=100)
    assert ids(res) == [1, 5, 6, 8, 2, 4, 7, 9]
    assert 3 not in ids(res)


def test_result_dict_has_exact_keys(conn):
    res = search_products(conn, limit=1)
    assert res == [{"id": 1, "name": "Apple", "price": 1.5}]
    assert set(res[0].keys()) == {"id", "name", "price"}


def test_name_filter_case_insensitive_ascii(conn):
    res = search_products(conn, name_contains="GRAPE")
    assert ids(res) == [8, 9]


def test_name_filter_empty_string_matches_all_in_stock(conn):
    assert len(search_products(conn, name_contains="", limit=100)) == 8


def test_name_filter_percent_is_literal(conn):
    assert ids(search_products(conn, name_contains="50%")) == [4]
    assert ids(search_products(conn, name_contains="%")) == [4]
    assert ids(search_products(conn, name_contains="50%o")) == []


def test_name_filter_underscore_is_literal(conn):
    assert ids(search_products(conn, name_contains="_")) == [5]
    assert ids(search_products(conn, name_contains="e_p")) == [5]
    assert ids(search_products(conn, name_contains="ea")) == []


def test_max_price_inclusive(conn):
    res = search_products(conn, max_price=1.5)
    assert ids(res) == [1, 7, 9]
    assert all(r["price"] <= 1.5 for r in res)


def test_max_price_none_means_no_limit(conn):
    assert len(search_products(conn, max_price=None, limit=100)) == 8


def test_order_by_price_ascending_ties_by_id(conn):
    res = search_products(conn, order_by="price")
    assert ids(res) == [1, 7, 9, 2, 6, 8, 4, 5]


def test_order_by_price_descending_ties_still_by_id_ascending(conn):
    res = search_products(conn, order_by="price", descending=True)
    assert ids(res) == [5, 4, 8, 2, 6, 1, 7, 9]


def test_order_by_name_descending(conn):
    res = search_products(conn, order_by="name", descending=True)
    assert ids(res) == [9, 7, 4, 2, 8, 6, 5, 1]


def test_invalid_order_by_raises(conn):
    with pytest.raises(ValueError):
        search_products(conn, order_by="stock")
    with pytest.raises(ValueError):
        search_products(conn, order_by="NAME")


@pytest.mark.parametrize("limit", [0, -1, 101, 1.0, "5", None, True])
def test_invalid_limit_raises(conn, limit):
    with pytest.raises(ValueError):
        search_products(conn, limit=limit)


@pytest.mark.parametrize("limit", [1, 100])
def test_limit_bounds_accepted(conn, limit):
    assert len(search_products(conn, limit=limit)) == min(limit, 8)


@pytest.mark.parametrize("offset", [-1, 1.0, "0", None, False])
def test_invalid_offset_raises(conn, offset):
    with pytest.raises(ValueError):
        search_products(conn, offset=offset)


def test_pagination_applied_after_filter_and_order(conn):
    page1 = search_products(conn, order_by="price", limit=3, offset=0)
    page2 = search_products(conn, order_by="price", limit=3, offset=3)
    assert ids(page1) == [1, 7, 9]
    assert ids(page2) == [2, 6, 8]


def test_offset_beyond_results_is_empty(conn):
    assert search_products(conn, offset=100) == []


def test_filters_combine(conn):
    res = search_products(conn, name_contains="g", max_price=2.5, order_by="price")
    assert ids(res) == [7, 9, 8]


def test_does_not_modify_database(conn):
    before = conn.execute("SELECT * FROM products ORDER BY id").fetchall()
    search_products(conn, name_contains="a", max_price=5, order_by="price",
                    descending=True, limit=2, offset=1)
    after = conn.execute("SELECT * FROM products ORDER BY id").fetchall()
    assert before == after


def test_sql_injection_text_is_treated_as_data(conn):
    res = search_products(conn, name_contains="' OR 1=1 --")
    assert res == []
    assert len(conn.execute("SELECT * FROM products").fetchall()) == len(ROWS)
