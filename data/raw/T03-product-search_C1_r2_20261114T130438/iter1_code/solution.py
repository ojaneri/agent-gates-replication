import sqlite3


_ORDER_COLUMNS = {"name": "name", "price": "price"}


def _check_int(value, name: str, minimum: int, maximum: int | None = None) -> int:
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
    if not isinstance(order_by, str) or order_by not in _ORDER_COLUMNS:
        raise ValueError("order_by must be 'name' or 'price'")
    limit = _check_int(limit, "limit", 1, 100)
    offset = _check_int(offset, "offset", 0)
    if not isinstance(name_contains, str):
        raise ValueError("name_contains must be a string")

    # instr() does a plain substring search, so '%' and '_' are ordinary characters.
    # lower() only folds ASCII letters in SQLite's default build, as the spec requires.
    conditions = ["stock > 0"]
    params: list = []
    if name_contains != "":
        conditions.append("instr(lower(name), lower(?)) > 0")
        params.append(name_contains)
    if max_price is not None:
        conditions.append("price <= ?")
        params.append(max_price)

    column = _ORDER_COLUMNS[order_by]
    direction = "DESC" if descending else "ASC"
    sql = (
        "SELECT id, name, price FROM products WHERE " + " AND ".join(conditions)
        + f" ORDER BY {column} {direction}, id ASC LIMIT ? OFFSET ?"
    )
    params.extend([limit, offset])

    cursor = conn.execute(sql, params)
    return [{"id": row[0], "name": row[1], "price": row[2]} for row in cursor.fetchall()]
