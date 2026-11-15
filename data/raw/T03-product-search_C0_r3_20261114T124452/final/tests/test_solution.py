import sqlite3

import pytest

from solution import search_products


ROWS = [
    (1, "apple", 1.50, 10),
    (2, "Banana", 0.75, 5),
    (3, "cherry", 3.00, 0),      # out of stock: never returned
    (4, "Apricot", 2.25, 7),
    (5, "50% off soap", 4.00, 3),
    (6, "a_b", 1.00, 2),
    (7, "axb", 1.00, 2),
    (8, "Zucchini", 1.50, 1),
    (9, "apple pie", 1.50, 4),
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


def ids(rows):
    return [r["id"] for r in rows]


def test_default_returns_in_stock_sorted_by_name_binary(conn):
    # Binary order: uppercase before lowercase. Out-of-stock cherry excluded.
    result = search_products(conn)
    names = [r["name"] for r in result]
    assert "cherry" not in names
    assert names == sorted(names)  # Python str sort is also code-point (binary) order


def test_result_has_exactly_id_name_price(conn):
    result = search_products(conn, name_contains="apple")
    assert result and all(set(r.keys()) == {"id", "name", "price"} for r in result)


def test_name_contains_is_case_insensitive_for_ascii(conn):
    assert ids(search_products(conn, name_contains="BANANA")) == [2]
    assert ids(search_products(conn, name_contains="apr")) == [4]


def test_empty_name_contains_matches_all_in_stock(conn):
    assert len(search_products(conn, name_contains="")) == 8


def test_percent_is_literal(conn):
    assert ids(search_products(conn, name_contains="50%")) == [5]
    assert search_products(conn, name_contains="%") == [
        r for r in search_products(conn) if "%" in r["name"]
    ]


def test_underscore_is_literal(conn):
    assert ids(search_products(conn, name_contains="a_b")) == [6]


def test_max_price_inclusive(conn):
    result = search_products(conn, max_price=1.50, order_by="price")
    assert all(r["price"] <= 1.50 for r in result)
    assert 1 in ids(result) and 9 in ids(result) and 8 in ids(result)


def test_order_by_price_with_id_tiebreak(conn):
    result = search_products(conn, order_by="price")
    assert ids(result) == [2, 6, 7, 1, 8, 9, 4, 5]


def test_order_by_price_descending_ties_still_ascending_id(conn):
    result = search_products(conn, order_by="price", descending=True)
    assert ids(result) == [5, 4, 1, 8, 9, 6, 7, 2]


def test_order_by_name_descending(conn):
    asc = [r["name"] for r in search_products(conn, limit=100)]
    desc = [r["name"] for r in search_products(conn, descending=True, limit=100)]
    assert desc == list(reversed(asc))


def test_invalid_order_by_raises(conn):
    with pytest.raises(ValueError):
        search_products(conn, order_by="id")
    with pytest.raises(ValueError):
        search_products(conn, order_by="NAME")


@pytest.mark.parametrize("limit", [0, -1, 101])
def test_invalid_limit_raises(conn, limit):
    with pytest.raises(ValueError):
        search_products(conn, limit=limit)


@pytest.mark.parametrize("limit", [1, 100])
def test_limit_bounds_accepted(conn, limit):
    assert len(search_products(conn, limit=limit)) <= limit


def test_invalid_offset_raises(conn):
    with pytest.raises(ValueError):
        search_products(conn, offset=-1)


def test_limit_and_offset_apply_after_filter_and_order(conn):
    all_ids = ids(search_products(conn, order_by="price", limit=100))
    page = ids(search_products(conn, order_by="price", limit=3, offset=2))
    assert page == all_ids[2:5]


def test_offset_past_end_is_empty(conn):
    assert search_products(conn, offset=100) == []


def test_never_modifies_database(conn):
    before = conn.execute("SELECT * FROM products ORDER BY id").fetchall()
    search_products(conn, name_contains="a", max_price=5, order_by="price", descending=True)
    after = conn.execute("SELECT * FROM products ORDER BY id").fetchall()
    assert before == after
