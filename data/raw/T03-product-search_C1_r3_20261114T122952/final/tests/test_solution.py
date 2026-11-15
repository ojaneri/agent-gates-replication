import sqlite3
import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from solution import search_products  # noqa: E402


ROWS = [
    # id, name, price, stock
    (1, "Apple", 1.5, 10),
    (2, "apricot", 2.0, 5),
    (3, "Banana", 0.5, 0),       # out of stock -> never returned
    (4, "Cherry", 3.0, 7),
    (5, "50% Off Juice", 4.0, 2),
    (6, "Under_score", 1.0, 3),
    (7, "UNDERSCORE plain", 1.0, 3),
    (8, "Date", 2.0, 1),
    (9, "apple", 1.5, 4),        # same name as id 1 (different case) and price
    (10, "Zeta", 9.99, 1),
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


# --- basic behaviour and stock filter -------------------------------------

def test_default_returns_in_stock_sorted_by_name_binary(conn):
    result = search_products(conn, limit=100)
    # Binary ordering: uppercase before lowercase. Names:
    # "50% Off Juice", "Apple", "Cherry", "Date", "UNDERSCORE plain",
    # "Under_score", "Zeta", "apple", "apricot"
    assert [r["name"] for r in result] == [
        "50% Off Juice", "Apple", "Cherry", "Date", "UNDERSCORE plain",
        "Under_score", "Zeta", "apple", "apricot",
    ]


def test_out_of_stock_excluded(conn):
    assert 3 not in ids(search_products(conn, limit=100))


def test_result_dict_has_exactly_id_name_price(conn):
    result = search_products(conn, limit=1)
    assert len(result) == 1
    assert set(result[0].keys()) == {"id", "name", "price"}
    assert result[0] == {"id": 5, "name": "50% Off Juice", "price": 4.0}


def test_result_values_are_correct(conn):
    result = search_products(conn, name_contains="cherry")
    assert result == [{"id": 4, "name": "Cherry", "price": 3.0}]


def test_empty_database_returns_empty_list():
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, "
              "price REAL NOT NULL, stock INTEGER NOT NULL)")
    assert search_products(c) == []
    c.close()


def test_all_out_of_stock_returns_empty():
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, "
              "price REAL NOT NULL, stock INTEGER NOT NULL)")
    c.execute("INSERT INTO products VALUES (1, 'x', 1.0, 0)")
    assert search_products(c) == []
    c.close()


# --- name_contains ---------------------------------------------------------

def test_empty_name_matches_everything(conn):
    assert search_products(conn, name_contains="", limit=100) == \
        search_products(conn, limit=100)


def test_name_contains_case_insensitive_ascii(conn):
    result = search_products(conn, name_contains="APPLE", limit=100)
    assert ids(result) == [1, 9]  # "Apple" and "apple"


def test_name_contains_substring_match(conn):
    assert ids(search_products(conn, name_contains="ric", limit=100)) == [2]
    assert ids(search_products(conn, name_contains="err", limit=100)) == [4]


def test_name_contains_no_match(conn):
    assert search_products(conn, name_contains="nonexistent") == []


def test_percent_is_not_a_wildcard(conn):
    assert ids(search_products(conn, name_contains="50%")) == [5]
    # A bare % is literal too: only "50% Off Juice" contains it.
    assert ids(search_products(conn, name_contains="%")) == [5]


def test_underscore_is_not_a_wildcard(conn):
    result = search_products(conn, name_contains="_", limit=100)
    assert ids(result) == [6]  # only "Under_score"; "UNDERSCORE" has no underscore
    assert search_products(conn, name_contains="r_s") == [
        {"id": 6, "name": "Under_score", "price": 1.0}
    ]


def test_name_contains_must_be_string(conn):
    with pytest.raises(TypeError):
        search_products(conn, name_contains=None)
    with pytest.raises(TypeError):
        search_products(conn, name_contains=5)


def test_name_contains_with_quotes_is_safe(conn):
    assert search_products(conn, name_contains="' OR 1=1 --") == []


# --- max_price -------------------------------------------------------------

def test_max_price_inclusive(conn):
    result = search_products(conn, max_price=1.5, limit=100)
    # Binary name order: Apple, UNDERSCORE plain, Under_score, apple
    assert ids(result) == [1, 7, 6, 9]
    assert all(r["price"] <= 1.5 for r in result)


def test_max_price_none_means_no_limit(conn):
    assert search_products(conn, max_price=None, limit=100) == \
        search_products(conn, limit=100)


def test_max_price_below_all_returns_empty(conn):
    assert search_products(conn, max_price=0.1) == []


def test_max_price_zero_keeps_nothing_priced_positive(conn):
    assert search_products(conn, max_price=0) == []


# --- order_by and descending ----------------------------------------------

def test_order_by_price_ascending_ties_by_id(conn):
    result = search_products(conn, order_by="price", limit=100)
    # prices: 1.0(6), 1.0(7), 1.5(1), 1.5(9), 2.0(2), 2.0(8), 3.0(4), 4.0(5), 9.99(10)
    assert ids(result) == [6, 7, 1, 9, 2, 8, 4, 5, 10]


def test_order_by_price_descending_ties_still_id_ascending(conn):
    result = search_products(conn, order_by="price", descending=True, limit=100)
    assert ids(result) == [10, 5, 4, 2, 8, 1, 9, 6, 7]


def test_order_by_name_descending(conn):
    result = search_products(conn, order_by="name", descending=True, limit=100)
    assert [r["name"] for r in result] == [
        "apricot", "apple", "Zeta", "Under_score", "UNDERSCORE plain",
        "Date", "Cherry", "Apple", "50% Off Juice",
    ]
    # Reverse of the ascending binary order.


def test_order_by_name_ties_broken_by_id_descending_flag(conn):
    # Names are distinct in case-sensitive order, so build an explicit tie.
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, "
              "price REAL NOT NULL, stock INTEGER NOT NULL)")
    c.executemany("INSERT INTO products VALUES (?, ?, ?, ?)",
                  [(3, "same", 1.0, 1), (1, "same", 1.0, 1), (2, "same", 1.0, 1)])
    assert ids(search_products(c, order_by="name")) == [1, 2, 3]
    assert ids(search_products(c, order_by="name", descending=True)) == [1, 2, 3]
    c.close()


def test_order_by_invalid_value_raises(conn):
    with pytest.raises(ValueError):
        search_products(conn, order_by="stock")
    with pytest.raises(ValueError):
        search_products(conn, order_by="NAME")
    with pytest.raises(ValueError):
        search_products(conn, order_by=None)
    with pytest.raises(ValueError):
        search_products(conn, order_by=["name"])


# --- limit and offset ------------------------------------------------------

def test_default_limit_is_20(conn):
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, "
              "price REAL NOT NULL, stock INTEGER NOT NULL)")
    c.executemany("INSERT INTO products VALUES (?, ?, ?, ?)",
                  [(i, f"p{i:03d}", 1.0, 1) for i in range(1, 31)])
    assert len(search_products(c)) == 20
    c.close()


def test_limit_and_offset_apply_after_filter_and_order(conn):
    full = search_products(conn, order_by="price", limit=100)
    page = search_products(conn, order_by="price", limit=3, offset=2)
    assert page == full[2:5]


def test_offset_beyond_end_returns_empty(conn):
    assert search_products(conn, offset=1000) == []


def test_limit_one(conn):
    assert len(search_products(conn, limit=1)) == 1


def test_limit_bounds_accepted(conn):
    assert len(search_products(conn, limit=1)) == 1
    assert len(search_products(conn, limit=100)) == 9


@pytest.mark.parametrize("bad", [0, -1, 101, 1000])
def test_limit_out_of_range_raises(conn, bad):
    with pytest.raises(ValueError):
        search_products(conn, limit=bad)


@pytest.mark.parametrize("bad", [1.0, 5.5, "5", None, True, False])
def test_limit_non_integer_raises(conn, bad):
    with pytest.raises(ValueError):
        search_products(conn, limit=bad)


def test_offset_zero_allowed(conn):
    assert search_products(conn, offset=0, limit=100) == search_products(conn, limit=100)


@pytest.mark.parametrize("bad", [-1, -100, 1.0, "0", None, True])
def test_offset_invalid_raises(conn, bad):
    with pytest.raises(ValueError):
        search_products(conn, offset=bad)


# --- combined and immutability ---------------------------------------------

def test_combined_filters(conn):
    result = search_products(conn, name_contains="a", max_price=2.0,
                             order_by="price", descending=True, limit=2, offset=1)
    # In stock, contains 'a' (case-insensitive), price <= 2.0:
    # ids 1, 2, 7, 8, 9. Descending price, ties by id asc:
    # 2.0: 2, 8; 1.5: 1, 9; 1.0: 7. Offset 1, limit 2 -> 8, 1.
    assert ids(result) == [8, 1]


def test_does_not_modify_database(conn):
    before = conn.execute("SELECT * FROM products ORDER BY id").fetchall()
    changes_before = conn.total_changes
    search_products(conn, name_contains="a", max_price=5, order_by="price",
                    descending=True, limit=5, offset=1)
    assert conn.total_changes == changes_before
    assert conn.execute("SELECT * FROM products ORDER BY id").fetchall() == before


def test_works_with_row_factory_connection(conn):
    conn.row_factory = sqlite3.Row
    result = search_products(conn, name_contains="cherry")
    assert result == [{"id": 4, "name": "Cherry", "price": 3.0}]
    assert type(result[0]) is dict
