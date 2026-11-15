import sqlite3

import pytest

from solution import search_products


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, price REAL NOT NULL, stock INTEGER NOT NULL)")
    rows = [
        (1, "apple", 1.0, 5),
        (2, "Banana", 0.5, 3),
        (3, "cherry", 1.0, 0),      # out of stock: never returned
        (4, "Apricot", 2.0, 10),
        (5, "50% off pear", 3.0, 1),
        (6, "5000 widget", 3.0, 1),
        (7, "under_score", 4.0, 2),
        (8, "underXscore", 4.0, 2),
        (9, "Zucchini", 1.0, 7),
    ]
    c.executemany("INSERT INTO products VALUES (?, ?, ?, ?)", rows)
    c.commit()
    yield c
    c.close()


def ids(results):
    return [r["id"] for r in results]


def test_result_keys_exact(conn):
    result = search_products(conn)
    assert result
    for r in result:
        assert set(r.keys()) == {"id", "name", "price"}


def test_out_of_stock_excluded(conn):
    assert 3 not in ids(search_products(conn, limit=100))


def test_default_order_is_name_binary(conn):
    # Binary ordering: uppercase letters sort before lowercase.
    names = [r["name"] for r in search_products(conn, limit=100)]
    assert names == sorted(names)
    assert names[0] == "50% off pear"
    assert names.index("Apricot") < names.index("apple")
    assert names.index("Banana") < names.index("apple")


def test_order_by_name_descending(conn):
    names = [r["name"] for r in search_products(conn, descending=True, limit=100)]
    assert names == sorted(names, reverse=True)


def test_order_by_price_ties_broken_by_id_ascending(conn):
    result = search_products(conn, order_by="price", limit=100)
    assert ids(result) == [2, 1, 9, 4, 5, 6, 7, 8]


def test_order_by_price_descending_ties_still_id_ascending(conn):
    result = search_products(conn, order_by="price", descending=True, limit=100)
    assert ids(result) == [7, 8, 5, 6, 4, 1, 9, 2]


def test_invalid_order_by_raises(conn):
    with pytest.raises(ValueError):
        search_products(conn, order_by="stock")
    with pytest.raises(ValueError):
        search_products(conn, order_by="NAME")


def test_name_filter_case_insensitive(conn):
    result = search_products(conn, name_contains="APPLE")
    assert ids(result) == [1]


def test_name_filter_substring(conn):
    assert ids(search_products(conn, name_contains="ana")) == [2]


def test_empty_name_matches_all_in_stock(conn):
    assert len(search_products(conn, limit=100)) == 8


def test_percent_is_literal(conn):
    assert ids(search_products(conn, name_contains="50%")) == [5]
    assert ids(search_products(conn, name_contains="%")) == [5]
    assert 6 not in ids(search_products(conn, name_contains="50%"))


def test_underscore_is_literal(conn):
    assert ids(search_products(conn, name_contains="under_score")) == [7]
    assert ids(search_products(conn, name_contains="_")) == [7]


def test_quotes_are_safe(conn):
    assert search_products(conn, name_contains="' OR 1=1 --") == []


def test_max_price_inclusive(conn):
    result = search_products(conn, max_price=1.0, limit=100)
    assert all(r["price"] <= 1.0 for r in result)
    assert set(ids(result)) == {1, 2, 9}


def test_max_price_none_no_filter(conn):
    assert len(search_products(conn, max_price=None, limit=100)) == 8


def test_limit_and_offset_applied_after_ordering(conn):
    all_ids = ids(search_products(conn, order_by="price", limit=100))
    page = ids(search_products(conn, order_by="price", limit=3, offset=2))
    assert page == all_ids[2:5]


def test_offset_past_end_returns_empty(conn):
    assert search_products(conn, offset=50) == []


@pytest.mark.parametrize("limit", [0, -1, 101, 1.5, "10", None, True])
def test_invalid_limit_raises(conn, limit):
    with pytest.raises(ValueError):
        search_products(conn, limit=limit)


@pytest.mark.parametrize("offset", [-1, 0.0, "0", None, False])
def test_invalid_offset_raises(conn, offset):
    with pytest.raises(ValueError):
        search_products(conn, offset=offset)


def test_limit_boundaries_valid(conn):
    assert len(search_products(conn, limit=1)) == 1
    assert len(search_products(conn, limit=100)) == 8


def test_does_not_modify_database(conn):
    before = conn.execute("SELECT * FROM products ORDER BY id").fetchall()
    search_products(conn, name_contains="a", max_price=5, order_by="price", descending=True, limit=2, offset=1)
    after = conn.execute("SELECT * FROM products ORDER BY id").fetchall()
    assert before == after
