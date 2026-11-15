import sqlite3


def _is_int(value) -> bool:
    # bool is a subclass of int, but True/False are not meaningful counts here.
    return isinstance(value, int) and not isinstance(value, bool)


def search_products(conn: sqlite3.Connection, name_contains: str = "", max_price: float | None = None,
                    order_by: str = "name", descending: bool = False, limit: int = 20,
                    offset: int = 0) -> list[dict]:
    """Search products. See spec.md."""
    # --- Validate arguments before touching the database. ---
    if not isinstance(order_by, str) or order_by not in ("name", "price"):
        raise ValueError("order_by must be 'name' or 'price'")
    if not _is_int(limit) or not (1 <= limit <= 100):
        raise ValueError("limit must be an integer from 1 to 100")
    if not _is_int(offset) or offset < 0:
        raise ValueError("offset must be an integer of at least 0")

    # --- Build a parameterised, read-only query. ---
    # Substring matching uses INSTR (not LIKE), so '%' and '_' are plain characters.
    # LOWER() gives case-insensitive matching for ASCII letters.
    conditions = ["stock > 0"]
    params: list = []

    if name_contains:
        conditions.append("INSTR(LOWER(name), LOWER(?)) > 0")
        params.append(name_contains)

    if max_price is not None:
        conditions.append("price <= ?")
        params.append(max_price)

    direction = "DESC" if descending else "ASC"
    # Ties in the chosen order are always broken by id ascending.
    sort_column = "name" if order_by == "name" else "price"
    order_clause = f"{sort_column} {direction}, id ASC"

    sql = (
        "SELECT id, name, price FROM products "
        f"WHERE {' AND '.join(conditions)} "
        f"ORDER BY {order_clause} "
        "LIMIT ? OFFSET ?"
    )
    params.extend([limit, offset])

    cursor = conn.cursor()
    # Ignore any row_factory set on the connection so results are plain tuples.
    cursor.row_factory = None
    try:
        rows = cursor.execute(sql, params).fetchall()
    finally:
        cursor.close()

    return [{"id": row[0], "name": row[1], "price": row[2]} for row in rows]
