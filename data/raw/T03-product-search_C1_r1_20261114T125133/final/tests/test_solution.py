import sqlite3

import pytest

from solution import search_products


ROWS = [
    (1, "apple", 1.50, 10),
    (2, "Banana", 0.25, 5),
    (3, "cherry", 3.00, 0),      # out of stock, must never appear
    (4, "Apricot", 2.00, 7),
    (5, "50% off jam", 4.00, 3),
    (6, "5x0 mix", 4.00, 2),
    (7, "under_score", 1.00, 1),
    (8, "underXscore", 1.00, 1),
    (9, "Zucchini", 1.50, 4),
    (10, "apple", 1.50, 9),      # duplicate name and price, tests id tie-break
    (11, "ÉCLAIR", 2.50, 6),     # non-ASCII, not case folded
]


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, price REAL NOT NULL, stock INTEGER NOT NULL)")
    c.executemany("INSERT INTO products VALUES (?, ?, ?, ?)", ROWS)
    c.commit()
    yield c
    c.close()


def ids(results):
    return [r["id"] for r in results]


def test_result_shape(conn):
    res = search_products(conn, name_contains="banana")
    assert res == [{"id": 2, "name": "Banana", "price": 0.25}]
    assert set(res[0].keys()) == {"id", "name", "price"}


def test_out_of_stock_excluded(conn):
    assert 3 not in ids(search_products(conn, limit=100))


def test_empty_name_matches_all_in_stock(conn):
    res = search_products(conn, limit=100)
    assert sorted(ids(res)) == sorted(i for i, _, _, s in ROWS if s > 0)


def test_default_order_is_name_then_id(conn):
    res = search_products(conn, limit=100)
    names = [r["name"] for r in res]
    assert names == sorted(names)  # binary order: uppercase before lowercase
    # binary order: digits, then uppercase, then lowercase, then non-ASCII
    assert names[:4] == ["50% off jam", "5x0 mix", "Apricot", "Banana"]
    # duplicate "apple" rows ordered by id
    apples = [r["id"] for r in res if r["name"] == "apple"]
    assert apples == [1, 10]


def test_binary_name_ordering_uppercase_first(conn):
    names = [r["name"] for r in search_products(conn, limit=100)]
    # 'Z' (0x5A) sorts before 'a' (0x61), and 'É' sorts after ASCII letters
    assert names.index("Zucchini") < names.index("apple")
    assert names[-1] == "ÉCLAIR"


def test_name_descending_keeps_id_ascending_on_ties(conn):
    res = search_products(conn, name_contains="apple", descending=True)
    assert ids(res) == [1, 10]
    res = search_products(conn, name_contains="a", descending=True, limit=100)
    names = [r["name"] for r in res]
    assert names == sorted(names, reverse=True)


def test_price_ascending_ties_by_id(conn):
    res = search_products(conn, order_by="price", limit=100)
    prices = [r["price"] for r in res]
    assert prices == sorted(prices)
    # price 1.50 rows: ids 1, 9, 10 in id order
    tied = [r["id"] for r in res if r["price"] == 1.50]
    assert tied == [1, 9, 10]


def test_price_descending_ties_still_by_id(conn):
    res = search_products(conn, order_by="price", descending=True, limit=100)
    prices = [r["price"] for r in res]
    assert prices == sorted(prices, reverse=True)
    tied = [r["id"] for r in res if r["price"] == 4.00]
    assert tied == [5, 6]
    tied = [r["id"] for r in res if r["price"] == 1.50]
    assert tied == [1, 9, 10]


def test_name_filter_case_insensitive_ascii(conn):
    assert ids(search_products(conn, name_contains="APPLE")) == [1, 10]
    assert ids(search_products(conn, name_contains="ApRiCoT")) == [4]


def test_name_filter_non_ascii_not_folded(conn):
    assert ids(search_products(conn, name_contains="éclair")) == []
    assert ids(search_products(conn, name_contains="ÉCLAIR")) == [11]


def test_percent_is_literal(conn):
    assert ids(search_products(conn, name_contains="50%")) == [5]
    # '%' as wildcard would match "5x0 mix" or everything; it must not
    assert ids(search_products(conn, name_contains="%")) == [5]


def test_underscore_is_literal(conn):
    assert ids(search_products(conn, name_contains="under_score")) == [7]
    assert ids(search_products(conn, name_contains="_")) == [7]


def test_no_match_returns_empty(conn):
    assert search_products(conn, name_contains="nomatch") == []


def test_max_price_inclusive(conn):
    res = search_products(conn, max_price=1.50, limit=100)
    assert all(r["price"] <= 1.50 for r in res)
    assert 1 in ids(res) and 9 in ids(res)
    assert 4 not in ids(res)  # price 2.00


def test_max_price_zero_and_none(conn):
    assert search_products(conn, max_price=0, limit=100) == []
    assert len(search_products(conn, max_price=None, limit=100)) == 10


def test_limit_and_offset_applied_after_ordering(conn):
    full = ids(search_products(conn, order_by="price", limit=100))
    page = ids(search_products(conn, order_by="price", limit=3, offset=2))
    assert page == full[2:5]


def test_offset_past_end_returns_empty(conn):
    assert search_products(conn, offset=1000) == []


def test_limit_boundaries(conn):
    assert len(search_products(conn, limit=1)) == 1
    assert len(search_products(conn, limit=100)) == 10


@pytest.mark.parametrize("limit", [0, -1, 101, 1.5, "5", None, True])
def test_invalid_limit_raises(conn, limit):
    with pytest.raises(ValueError):
        search_products(conn, limit=limit)


@pytest.mark.parametrize("offset", [-1, 0.5, "0", None, False])
def test_invalid_offset_raises(conn, offset):
    with pytest.raises(ValueError):
        search_products(conn, offset=offset)


def test_offset_zero_valid(conn):
    assert len(search_products(conn, offset=0, limit=100)) == 10


@pytest.mark.parametrize("order_by", ["id", "stock", "NAME", "", "price; DROP TABLE products"])
def test_invalid_order_by_raises(conn, order_by):
    with pytest.raises(ValueError):
        search_products(conn, order_by=order_by)


def test_never_modifies_database(conn):
    before = conn.execute("SELECT * FROM products ORDER BY id").fetchall()
    search_products(conn, name_contains="a", max_price=5, order_by="price", descending=True, limit=5, offset=1)
    after = conn.execute("SELECT * FROM products ORDER BY id").fetchall()
    assert before == after
    count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    assert count == len(ROWS)


def test_percent_in_name_with_other_filters(conn):
    res = search_products(conn, name_contains="%", max_price=5, order_by="price")
    assert ids(res) == [5]
