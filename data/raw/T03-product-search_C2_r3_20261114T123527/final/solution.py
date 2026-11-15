import sqlite3


# Each (order_by, descending) pair maps to a fixed SQL text, so no part of the
# query is ever built from caller-supplied strings.
_QUERIES = {
    ("name", False): (
        "SELECT id, name, price FROM products "
        "WHERE stock > 0 "
        "AND (? = '' OR instr(lower(name), lower(?)) > 0) "
        "AND (? IS NULL OR price <= ?) "
        "ORDER BY name ASC, id ASC LIMIT ? OFFSET ?"
    ),
    ("name", True): (
        "SELECT id, name, price FROM products "
        "WHERE stock > 0 "
        "AND (? = '' OR instr(lower(name), lower(?)) > 0) "
        "AND (? IS NULL OR price <= ?) "
        "ORDER BY name DESC, id ASC LIMIT ? OFFSET ?"
    ),
    ("price", False): (
        "SELECT id, name, price FROM products "
        "WHERE stock > 0 "
        "AND (? = '' OR instr(lower(name), lower(?)) > 0) "
        "AND (? IS NULL OR price <= ?) "
        "ORDER BY price ASC, id ASC LIMIT ? OFFSET ?"
    ),
    ("price", True): (
        "SELECT id, name, price FROM products "
        "WHERE stock > 0 "
        "AND (? = '' OR instr(lower(name), lower(?)) > 0) "
        "AND (? IS NULL OR price <= ?) "
        "ORDER BY price DESC, id ASC LIMIT ? OFFSET ?"
    ),
}


def _is_plain_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def search_products(conn: sqlite3.Connection, name_contains: str = "", max_price: float | None = None,
                    order_by: str = "name", descending: bool = False, limit: int = 20,
                    offset: int = 0) -> list[dict]:
    """Search products. See spec.md."""
    if order_by not in ("name", "price"):
        raise ValueError("order_by must be 'name' or 'price'")
    if not _is_plain_int(limit) or not 1 <= limit <= 100:
        raise ValueError("limit must be an integer from 1 to 100")
    if not _is_plain_int(offset) or offset < 0:
        raise ValueError("offset must be an integer of at least 0")

    query = _QUERIES[(order_by, bool(descending))]
    rows = conn.execute(
        query,
        (name_contains, name_contains, max_price, max_price, limit, offset),
    ).fetchall()
    return [{"id": row[0], "name": row[1], "price": row[2]} for row in rows]
