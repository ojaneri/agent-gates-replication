import sqlite3

import pytest

from solution import search_products


ROWS = [
    # id, name, price, stock
    (1, "Apple", 1.50, 10),
    (2, "banana", 0.25, 5),
    (3, "Cherry", 3.00, 0),      # out of stock: never returned
    (4, "apricot", 2.00, 7),
    (5, "Discount 50% off", 4.00, 1),
    (6, "under_score", 2.00, 3),
    (7, "Mango", 2.00, 2),
    (8, "ALPHA", 9.99, 4),
    (9, "bake", 0.25, 1),
    (10, "Zucchini", 5.00, -1),  # negative stock: never returned
]


@pytest.fixture
def conn():
    connection = sqlite3.connect(":memory:")
    connection.execute(
        "CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, "
        "price REAL NOT NULL, stock INTEGER NOT NULL)"
    )
    connection.executemany("INSERT INTO products VALUES (?, ?, ?, ?)", ROWS)
    connection.commit()
    yield connection
    connection.close()


def ids(results):
    return [r["id"] for r in results]


# --- basic result shape and stock filter ---------------------------------

def test_default_call_returns_only_in_stock_products_sorted_by_name(conn):
    result = search_products(conn)
    assert ids(result) == [8, 1, 5, 7, 4, 9, 2, 6]


def test_results_are_dicts_with_exactly_id_name_price(conn):
    result = search_products(conn, name_contains="apple")
    assert result == [{"id": 1, "name": "Apple", "price": 1.5}]
    assert set(result[0].keys()) == {"id", "name", "price"}


def test_out_of_stock_and_negative_stock_excluded(conn):
    assert 3 not in ids(search_products(conn))
    assert 10 not in ids(search_products(conn))


def test_stock_of_one_is_included(conn):
    assert 9 in ids(search_products(conn))


def test_empty_database_returns_empty_list():
    connection = sqlite3.connect(":memory:")
    connection.execute(
        "CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, "
        "price REAL NOT NULL, stock INTEGER NOT NULL)"
    )
    assert search_products(connection) == []
    connection.close()


def test_no_matches_returns_empty_list(conn):
    assert search_products(conn, name_contains="zzz") == []


def test_only_out_of_stock_match_returns_empty_list(conn):
    assert search_products(conn, name_contains="cherry") == []


# --- name_contains ---------------------------------------------------------

def test_name_contains_empty_string_matches_everything_in_stock(conn):
    assert len(search_products(conn, name_contains="")) == 8


def test_name_contains_is_case_insensitive_for_ascii(conn):
    assert ids(search_products(conn, name_contains="APPLE")) == [1]
    assert ids(search_products(conn, name_contains="aPpLe")) == [1]


def test_name_contains_matches_substring_not_prefix(conn):
    assert ids(search_products(conn, name_contains="ana")) == [2]


def test_name_contains_matches_inside_word(conn):
    assert ids(search_products(conn, name_contains="pric")) == [4]


def test_percent_is_literal_not_wildcard(conn):
    assert ids(search_products(conn, name_contains="50%")) == [5]


def test_percent_alone_matches_only_names_containing_percent(conn):
    assert ids(search_products(conn, name_contains="%")) == [5]


def test_underscore_is_literal_not_wildcard(conn):
    assert ids(search_products(conn, name_contains="_")) == [6]


def test_underscore_does_not_match_any_character(conn):
    # If "_" were a wildcard, "under_score" would match "underXscore" style
    # patterns; searching for "undersc" must still match via substring only.
    assert ids(search_products(conn, name_contains="under_s")) == [6]
    assert search_products(conn, name_contains="underXs") == []


def test_backslash_is_ordinary_character(conn):
    assert search_products(conn, name_contains="\\") == []


def test_name_contains_with_quote_characters_is_safe(conn):
    assert search_products(conn, name_contains="' OR 1=1 --") == []


def test_non_ascii_letters_are_not_case_folded(conn):
    connection = sqlite3.connect(":memory:")
    connection.execute(
        "CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, "
        "price REAL NOT NULL, stock INTEGER NOT NULL)"
    )
    connection.executemany(
        "INSERT INTO products VALUES (?, ?, ?, ?)",
        [(1, "Émile", 1.0, 1), (2, "émile", 1.0, 1)],
    )
    assert ids(search_products(connection, name_contains="émile")) == [2]
    assert ids(search_products(connection, name_contains="ÉMILE")) == [1]
    connection.close()


# --- max_price -------------------------------------------------------------

def test_max_price_none_means_no_price_filter(conn):
    assert len(search_products(conn, max_price=None)) == 8


def test_max_price_is_inclusive(conn):
    result = search_products(conn, max_price=2.0)
    assert 4 in ids(result)  # price exactly 2.00 is kept
    assert 1 in ids(result)  # 1.50 kept
    assert 5 not in ids(result)  # 4.00 excluded
    assert 8 not in ids(result)  # 9.99 excluded


def test_max_price_just_below_a_price_excludes_it(conn):
    assert 4 not in ids(search_products(conn, max_price=1.99))


def test_max_price_zero_returns_nothing_when_no_free_items(conn):
    assert search_products(conn, max_price=0) == []


def test_max_price_combined_with_name_filter(conn):
    assert ids(search_products(conn, name_contains="a", max_price=2.0)) == [1, 7, 4, 9, 2]


# --- order_by and descending ----------------------------------------------

def test_order_by_price_ascending_ties_broken_by_id(conn):
    result = search_products(conn, order_by="price")
    assert ids(result) == [2, 9, 1, 4, 6, 7, 5, 8]


def test_order_by_price_descending_ties_still_broken_by_id_ascending(conn):
    result = search_products(conn, order_by="price", descending=True)
    assert ids(result) == [8, 5, 4, 6, 7, 1, 2, 9]


def test_order_by_name_descending(conn):
    result = search_products(conn, order_by="name", descending=True)
    assert ids(result) == [6, 2, 9, 4, 7, 5, 1, 8]


def test_order_by_name_uses_binary_ordering_uppercase_first(conn):
    names = [r["name"] for r in search_products(conn)]
    assert names == sorted(names)
    assert names[0] == "ALPHA"  # uppercase sorts before lowercase in binary order


def test_descending_false_is_same_as_default(conn):
    assert search_products(conn, descending=False) == search_products(conn)


def test_name_ties_broken_by_id_ascending_in_descending_order():
    connection = sqlite3.connect(":memory:")
    connection.execute(
        "CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, "
        "price REAL NOT NULL, stock INTEGER NOT NULL)"
    )
    connection.executemany(
        "INSERT INTO products VALUES (?, ?, ?, ?)",
        [(5, "same", 1.0, 1), (2, "same", 1.0, 1), (9, "same", 1.0, 1)],
    )
    result = search_products(connection, order_by="name", descending=True)
    assert ids(result) == [2, 5, 9]
    connection.close()


@pytest.mark.parametrize("bad", ["id", "Name", "", "price ", "name;", None, 1])
def test_invalid_order_by_raises_value_error(conn, bad):
    with pytest.raises(ValueError):
        search_products(conn, order_by=bad)


# --- limit and offset ------------------------------------------------------

def test_limit_applied_after_filtering_and_ordering(conn):
    assert ids(search_products(conn, order_by="price", limit=3)) == [2, 9, 1]


def test_offset_applied_after_ordering(conn):
    assert ids(search_products(conn, order_by="price", offset=2, limit=2)) == [1, 4]


def test_limit_and_offset_together_with_descending(conn):
    assert ids(search_products(conn, order_by="price", descending=True, offset=1, limit=2)) == [5, 4]


def test_offset_beyond_results_returns_empty(conn):
    assert search_products(conn, offset=100) == []


def test_offset_zero_is_allowed(conn):
    assert search_products(conn, offset=0, limit=1) == [{"id": 8, "name": "ALPHA", "price": 9.99}]


def test_limit_one_is_allowed(conn):
    assert len(search_products(conn, limit=1)) == 1


def test_limit_100_is_allowed(conn):
    assert len(search_products(conn, limit=100)) == 8


@pytest.mark.parametrize("bad", [0, -1, 101, 1000])
def test_limit_out_of_range_raises(conn, bad):
    with pytest.raises(ValueError):
        search_products(conn, limit=bad)


@pytest.mark.parametrize("bad", [1.0, "5", None, True])
def test_limit_wrong_type_raises(conn, bad):
    with pytest.raises(ValueError):
        search_products(conn, limit=bad)


def test_offset_negative_raises(conn):
    with pytest.raises(ValueError):
        search_products(conn, offset=-1)


@pytest.mark.parametrize("bad", [1.0, "0", None, False])
def test_offset_wrong_type_raises(conn, bad):
    with pytest.raises(ValueError):
        search_products(conn, offset=bad)


# --- read-only behaviour ---------------------------------------------------

def test_function_never_modifies_database(conn):
    before = conn.execute("SELECT * FROM products ORDER BY id").fetchall()
    changes_before = conn.total_changes
    search_products(conn, name_contains="a", max_price=5, order_by="price", descending=True)
    search_products(conn, name_contains="'; DROP TABLE products; --")
    after = conn.execute("SELECT * FROM products ORDER BY id").fetchall()
    assert before == after
    assert conn.total_changes == changes_before
