import sqlite3


_ORDER_COLUMNS = {
    "name": "name COLLATE BINARY",
    "price": "price",
}


def _check_int(value, label, minimum, maximum=None):
    """Return value if it is a plain int within range, else raise ValueError."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    if value < minimum or (maximum is not None and value > maximum):
        if maximum is None:
            raise ValueError(f"{label} must be at least {minimum}")
        raise ValueError(f"{label} must be between {minimum} and {maximum}")
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
        raise TypeError("name_contains must be a string")

    clauses = ["stock > 0"]
    params: list = []
    if name_contains:
        # instr() is a plain substring search, so % and _ are ordinary characters.
        # lower() folds ASCII letters only, giving ASCII case-insensitive matching.
        clauses.append("instr(lower(name), lower(?)) > 0")
        params.append(name_contains)
    if max_price is not None:
        clauses.append("price <= ?")
        params.append(max_price)

    direction = "DESC" if descending else "ASC"
    sql = (
        "SELECT id, name, price FROM products"
        f" WHERE {' AND '.join(clauses)}"
        f" ORDER BY {_ORDER_COLUMNS[order_by]} {direction}, id ASC"
        " LIMIT ? OFFSET ?"
    )
    params.extend([limit, offset])

    rows = conn.execute(sql, params).fetchall()
    return [{"id": row[0], "name": row[1], "price": row[2]} for row in rows]
