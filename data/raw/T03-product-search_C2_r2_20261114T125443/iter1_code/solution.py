import sqlite3

# One fixed statement per (order column, descending) pair, so no SQL text is
# ever assembled from caller input. Ties are always broken by id ascending.
_QUERIES = {
    ("name", False): """SELECT id, name, price FROM products
        WHERE stock > 0
          AND (? = '' OR instr(lower(name), lower(?)) > 0)
          AND (? IS NULL OR price <= ?)
        ORDER BY name ASC, id ASC LIMIT ? OFFSET ?""",
    ("name", True): """SELECT id, name, price FROM products
        WHERE stock > 0
          AND (? = '' OR instr(lower(name), lower(?)) > 0)
          AND (? IS NULL OR price <= ?)
        ORDER BY name DESC, id ASC LIMIT ? OFFSET ?""",
    ("price", False): """SELECT id, name, price FROM products
        WHERE stock > 0
          AND (? = '' OR instr(lower(name), lower(?)) > 0)
          AND (? IS NULL OR price <= ?)
        ORDER BY price ASC, id ASC LIMIT ? OFFSET ?""",
    ("price", True): """SELECT id, name, price FROM products
        WHERE stock > 0
          AND (? = '' OR instr(lower(name), lower(?)) > 0)
          AND (? IS NULL OR price <= ?)
        ORDER BY price DESC, id ASC LIMIT ? OFFSET ?""",
}


def _is_plain_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _check_limit(limit) -> None:
    if not _is_plain_int(limit) or not 1 <= limit <= 100:
        raise ValueError("limit must be an integer from 1 to 100")


def _check_offset(offset) -> None:
    if not _is_plain_int(offset) or offset < 0:
        raise ValueError("offset must be an integer of at least 0")


def search_products(conn: sqlite3.Connection, name_contains: str = "", max_price: float | None = None,
                    order_by: str = "name", descending: bool = False, limit: int = 20,
                    offset: int = 0) -> list[dict]:
    """Search products. See spec.md."""
    if order_by not in ("name", "price"):
        raise ValueError("order_by must be 'name' or 'price'")
    _check_limit(limit)
    _check_offset(offset)
    # lower() only folds ASCII letters in SQLite's default build, matching the spec.
    # instr() does a literal substring test, so % and _ are not wildcards.
    query = _QUERIES[(order_by, bool(descending))]
    rows = conn.execute(query, (name_contains, name_contains,
                                max_price, max_price,
                                limit, offset)).fetchall()
    return [{"id": row[0], "name": row[1], "price": row[2]} for row in rows]
