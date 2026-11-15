import sqlite3


# Every SQL statement is a fixed literal. Optional filters are switched on or
# off by parameters (a flag of 1 enables the clause), so no SQL text is ever
# built from user input.
_QUERIES = {
    ("name", False): (
        "SELECT id, name, price FROM products "
        "WHERE stock > 0 "
        "AND (? = 0 OR instr(lower(name), lower(?)) > 0) "
        "AND (? = 0 OR price <= ?) "
        "ORDER BY name ASC, id ASC LIMIT ? OFFSET ?"
    ),
    ("name", True): (
        "SELECT id, name, price FROM products "
        "WHERE stock > 0 "
        "AND (? = 0 OR instr(lower(name), lower(?)) > 0) "
        "AND (? = 0 OR price <= ?) "
        "ORDER BY name DESC, id ASC LIMIT ? OFFSET ?"
    ),
    ("price", False): (
        "SELECT id, name, price FROM products "
        "WHERE stock > 0 "
        "AND (? = 0 OR instr(lower(name), lower(?)) > 0) "
        "AND (? = 0 OR price <= ?) "
        "ORDER BY price ASC, id ASC LIMIT ? OFFSET ?"
    ),
    ("price", True): (
        "SELECT id, name, price FROM products "
        "WHERE stock > 0 "
        "AND (? = 0 OR instr(lower(name), lower(?)) > 0) "
        "AND (? = 0 OR price <= ?) "
        "ORDER BY price DESC, id ASC LIMIT ? OFFSET ?"
    ),
}


def _check_int(value, name: str, minimum: int, maximum: int | None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    if value < minimum or (maximum is not None and value > maximum):
        if maximum is None:
            raise ValueError(f"{name} must be at least {minimum}")
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return value


def search_products(conn: sqlite3.Connection, name_contains: str = "", max_price: float | None = None,
                    order_by: str = "name", descending: bool = False, limit: int = 20,
                    offset: int = 0) -> list[dict]:
    """Search products. See spec.md."""
    if not isinstance(name_contains, str):
        raise ValueError("name_contains must be a string")
    if order_by not in ("name", "price"):
        raise ValueError("order_by must be 'name' or 'price'")
    limit = _check_int(limit, "limit", 1, 100)
    offset = _check_int(offset, "offset", 0, None)

    # instr() with lower() gives a literal, ASCII case-insensitive substring
    # test, so '%' and '_' are not treated as wildcards.
    use_name = 0 if name_contains == "" else 1
    use_price = 0 if max_price is None else 1
    price_value = 0 if max_price is None else max_price

    sql = _QUERIES[(order_by, bool(descending))]
    params = (use_name, name_contains, use_price, price_value, limit, offset)

    cursor = conn.cursor()
    try:
        rows = cursor.execute(sql, params).fetchall()
    finally:
        cursor.close()
    return [{"id": row[0], "name": row[1], "price": row[2]} for row in rows]
