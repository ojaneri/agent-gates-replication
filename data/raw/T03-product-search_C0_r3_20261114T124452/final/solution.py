import sqlite3


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
    if order_by == "name":
        order_expr = "name COLLATE BINARY"
    elif order_by == "price":
        order_expr = "price"
    else:
        raise ValueError("order_by must be 'name' or 'price'")
    limit = _check_int(limit, "limit", 1, 100)
    offset = _check_int(offset, "offset", 0, None)

    direction = "DESC" if descending else "ASC"
    conditions = ["stock > 0"]
    params: list = []

    if name_contains:
        # instr() is a plain substring match (no LIKE wildcards), and lower()
        # folds ASCII letters only in SQLite's default configuration.
        conditions.append("instr(lower(name), lower(?)) > 0")
        params.append(name_contains)

    if max_price is not None:
        conditions.append("price <= ?")
        params.append(max_price)

    sql = (
        "SELECT id, name, price FROM products "
        "WHERE " + " AND ".join(conditions) + " "
        f"ORDER BY {order_expr} {direction}, id ASC "
        "LIMIT ? OFFSET ?"
    )
    params.extend([limit, offset])

    cursor = conn.execute(sql, params)
    return [{"id": row[0], "name": row[1], "price": row[2]} for row in cursor.fetchall()]
