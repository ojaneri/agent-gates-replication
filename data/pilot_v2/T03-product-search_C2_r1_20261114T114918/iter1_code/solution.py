import sqlite3


_ORDER_COLUMNS = {"name": "name", "price": "price"}


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
    if order_by not in _ORDER_COLUMNS:
        raise ValueError("order_by must be 'name' or 'price'")
    limit = _check_int(limit, "limit", 1, 100)
    offset = _check_int(offset, "offset", 0, None)

    conditions = ["stock > 0"]
    params: list = []

    if name_contains != "":
        # instr() with lower() performs a literal, ASCII case-insensitive
        # substring test, so '%' and '_' are not treated as wildcards.
        conditions.append("instr(lower(name), lower(?)) > 0")
        params.append(name_contains)

    if max_price is not None:
        conditions.append("price <= ?")
        params.append(max_price)

    direction = "DESC" if descending else "ASC"
    column = _ORDER_COLUMNS[order_by]
    # Column and direction come from fixed whitelists, never from user input.
    sql = (
        "SELECT id, name, price FROM products WHERE " + " AND ".join(conditions)
        + f" ORDER BY {column} {direction}, id ASC LIMIT ? OFFSET ?"
    )
    params.extend([limit, offset])

    cursor = conn.cursor()
    try:
        rows = cursor.execute(sql, params).fetchall()
    finally:
        cursor.close()
    return [{"id": row[0], "name": row[1], "price": row[2]} for row in rows]
