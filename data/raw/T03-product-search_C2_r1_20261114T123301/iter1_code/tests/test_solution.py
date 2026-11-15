import sqlite3

import pytest

from solution import search_products


ROWS = [
    # id, name, price, stock
    (1, "apple", 1.50, 10),
    (2, "Banana", 0.25, 5),
    (3, "Cherry", 3.00, 0),      # out of stock: never returned
    (4, "apricot", 1.50, 2),     # ties with apple on price
    (5, "50% off juice", 2.00, 1),
    (6, "5x0 widget", 2.00, 4),  # '_'/'%' wildcard check target
    (7, "Zebra", 9.99, 3),
    (8, "CAFÉ", 4.00, 1),
    (9, "café", 4.00, 1),
    (10, "Date", 0.10, 7),
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


def ids(result):
    return [r["id"] for r in result]


def test_default_call_returns_in_stock_sorted_by_name(conn):
    result = search_products(conn, limit=100)
    # Binary order: digits < uppercase < lowercase. Out-of-stock Cherry excluded.
    assert [r["name"] for r in result] == [
        "50% off juice", "5x0 widget", "Banana", "CAFÉ", "Date", "Zebra",
        "apple", "apricot", "café",
    ]
    assert ids(result) == [5, 6, 2, 8, 10, 7, 1, 4, 9]


def test_result_has_exactly_id_name_price(conn):
    result = search_products(conn, limit=1)
    assert result == [{"id": 5, "name": "50% off juice", "price": 2.0}]
    assert set(result[0].keys()) == {"id", "name", "price"}


def test_out_of_stock_excluded(conn):
    assert 3 not in ids(search_products(conn, name_contains="cherry"))


def test_name_filter_is_case_insensitive_for_ascii(conn):
    assert ids(search_products(conn, name_contains="APPLE")) == [1]
    assert ids(search_products(conn, name_contains="banana")) == [2]


def test_name_filter_is_substring(conn):
    assert ids(search_products(conn, name_contains="pric")) == [4]
    assert ids(search_products(conn, name_contains="ana")) == [2]


def test_name_filter_no_match_returns_empty(conn):
    assert search_products(conn, name_contains="kiwi") == []


def test_empty_name_matches_everything(conn):
    assert len(search_products(conn, name_contains="", limit=100)) == 9


def test_percent_is_literal(conn):
    assert ids(search_products(conn, name_contains="50%")) == [5]


def test_percent_does_not_act_as_wildcard(conn):
    # If '%' were a wildcard, "%" would match every name.
    assert ids(search_products(conn, name_contains="%")) == [5]


def test_underscore_is_literal(conn):
    # If '_' were a wildcard, "5_0" would match "5x0 widget".
    assert search_products(conn, name_contains="5_0") == []
    assert ids(search_products(conn, name_contains="5x0")) == [6]


def test_non_ascii_case_is_not_folded(conn):
    # Only ASCII letters are case-insensitive.
    assert ids(search_products(conn, name_contains="café")) == [9]
    assert ids(search_products(conn, name_contains="CAFÉ")) == [8]
    assert ids(search_products(conn, name_contains="café".upper())) == [8]


def test_max_price_is_inclusive(conn):
    result = search_products(conn, max_price=1.50, order_by="price")
    assert ids(result) == [10, 2, 1, 4]


def test_max_price_excludes_above(conn):
    result = search_products(conn, max_price=1.49)
    assert ids(result) == [2, 10]


def test_max_price_none_means_no_limit(conn):
    assert len(search_products(conn, max_price=None, limit=100)) == 9


def test_max_price_zero_matches_nothing(conn):
    assert search_products(conn, max_price=0) == []


def test_order_by_name_ascending(conn):
    names = [r["name"] for r in search_products(conn, order_by="name")]
    assert names == sorted(names)
    assert names[0] == "50% off juice"


def test_order_by_name_descending(conn):
    result = search_products(conn, order_by="name", descending=True, limit=100)
    assert ids(result) == [9, 4, 1, 7, 10, 8, 2, 6, 5]


def test_order_by_name_is_binary_uppercase_first(conn):
    names = [r["name"] for r in search_products(conn, order_by="name", limit=100)]
    assert names.index("Zebra") < names.index("apple")


def test_order_by_price_ascending_ties_by_id(conn):
    result = search_products(conn, order_by="price")
    assert ids(result) == [10, 2, 1, 4, 5, 6, 8, 9, 7]


def test_order_by_price_descending_ties_still_by_id_ascending(conn):
    result = search_products(conn, order_by="price", descending=True)
    # Price 4.00 tie: 8 before 9; price 2.00 tie: 5 before 6; price 1.50 tie: 1 before 4.
    assert ids(result) == [7, 8, 9, 5, 6, 1, 4, 2, 10]


def test_descending_false_explicit_is_ascending(conn):
    assert ids(search_products(conn, order_by="price", descending=False)) == \
        ids(search_products(conn, order_by="price"))


def test_name_ties_broken_by_id(conn):
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, "
              "price REAL NOT NULL, stock INTEGER NOT NULL)")
    c.executemany("INSERT INTO products VALUES (?, ?, ?, ?)",
                  [(5, "same", 1.0, 1), (2, "same", 1.0, 1), (9, "same", 1.0, 1)])
    assert ids(search_products(c, order_by="name")) == [2, 5, 9]
    assert ids(search_products(c, order_by="name", descending=True)) == [2, 5, 9]
    assert ids(search_products(c, order_by="price", descending=True)) == [2, 5, 9]
    c.close()


def test_invalid_order_by_raises(conn):
    with pytest.raises(ValueError):
        search_products(conn, order_by="stock")


def test_order_by_is_case_sensitive(conn):
    with pytest.raises(ValueError):
        search_products(conn, order_by="Name")


def test_order_by_injection_attempt_rejected(conn):
    with pytest.raises(ValueError):
        search_products(conn, order_by="name; DROP TABLE products")


def test_limit_default_is_20(conn):
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, "
              "price REAL NOT NULL, stock INTEGER NOT NULL)")
    c.executemany("INSERT INTO products VALUES (?, ?, ?, ?)",
                  [(i, f"p{i:03d}", 1.0, 1) for i in range(1, 31)])
    assert len(search_products(c)) == 20
    assert len(search_products(c, limit=25)) == 25
    assert len(search_products(c, limit=100)) == 30
    c.close()


@pytest.mark.parametrize("bad", [0, -1, 101, 1000])
def test_limit_out_of_range_raises(conn, bad):
    with pytest.raises(ValueError):
        search_products(conn, limit=bad)


@pytest.mark.parametrize("bad", [1.0, "5", None, True])
def test_limit_wrong_type_raises(conn, bad):
    with pytest.raises(ValueError):
        search_products(conn, limit=bad)


@pytest.mark.parametrize("good", [1, 50, 100])
def test_limit_boundaries_accepted(conn, good):
    assert len(search_products(conn, limit=good, order_by="price")) <= good


def test_limit_one_returns_single_row(conn):
    assert ids(search_products(conn, limit=1)) == [5]


def test_offset_pagination(conn):
    all_ids = ids(search_products(conn, order_by="price", limit=100))
    page1 = ids(search_products(conn, order_by="price", limit=3, offset=0))
    page2 = ids(search_products(conn, order_by="price", limit=3, offset=3))
    assert page1 == all_ids[0:3]
    assert page2 == all_ids[3:6]


def test_offset_past_end_returns_empty(conn):
    assert search_products(conn, offset=100) == []


def test_offset_zero_is_accepted(conn):
    assert ids(search_products(conn, offset=0, limit=1)) == [5]


@pytest.mark.parametrize("bad", [-1, -100])
def test_negative_offset_raises(conn, bad):
    with pytest.raises(ValueError):
        search_products(conn, offset=bad)


@pytest.mark.parametrize("bad", [1.0, "0", None, False])
def test_offset_wrong_type_raises(conn, bad):
    with pytest.raises(ValueError):
        search_products(conn, offset=bad)


def test_limit_and_offset_applied_after_filter_and_order(conn):
    # Filter to cheap items first, then take offset 1, limit 2 in price order.
    result = search_products(conn, max_price=2.0, order_by="price", limit=2, offset=1)
    assert ids(result) == [2, 1]


def test_filters_combine(conn):
    result = search_products(conn, name_contains="a", max_price=1.5, order_by="price")
    assert ids(result) == [10, 2, 1, 4]


def test_function_does_not_modify_database(conn):
    before = conn.execute("SELECT * FROM products ORDER BY id").fetchall()
    search_products(conn, name_contains="a", max_price=5, order_by="price",
                    descending=True, limit=50, offset=1)
    search_products(conn)
    after = conn.execute("SELECT * FROM products ORDER BY id").fetchall()
    assert before == after


def test_empty_table_returns_empty():
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, "
              "price REAL NOT NULL, stock INTEGER NOT NULL)")
    assert search_products(c) == []
    c.close()
