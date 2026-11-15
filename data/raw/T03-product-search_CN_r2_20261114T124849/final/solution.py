import sqlite3


def search_products(conn: sqlite3.Connection, name_contains: str = "", max_price: float | None = None,
                    order_by: str = "name", descending: bool = False, limit: int = 20,
                    offset: int = 0) -> list[dict]:
    """Search products. See spec.md."""
    if order_by not in ("name", "price"):
        raise ValueError("order_by must be 'name' or 'price'")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError("limit must be an integer from 1 to 100")
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        raise ValueError("offset must be an integer of at least 0")

    conditions = ["stock > 0"]
    params: list = []

    if name_contains:
        # Escape LIKE wildcards (and the escape character itself) so that
        # '%' and '_' are matched literally. LIKE is case-insensitive for
        # ASCII letters, which matches the required semantics.
        escaped = (name_contains.replace("\\", "\\\\")
                                .replace("%", "\\%")
                                .replace("_", "\\_"))
        conditions.append("name LIKE ? ESCAPE '\\'")
        params.append("%" + escaped + "%")

    if max_price is not None:
        conditions.append("price <= ?")
        params.append(max_price)

    direction = "DESC" if descending else "ASC"
    sort_column = "name" if order_by == "name" else "price"
    query = (
        "SELECT id, name, price FROM products "
        "WHERE " + " AND ".join(conditions) + " "
        f"ORDER BY {sort_column} {direction}, id ASC "
        "LIMIT ? OFFSET ?"
    )
    params.extend([limit, offset])

    cursor = conn.cursor()
    try:
        cursor.row_factory = None
        rows = cursor.execute(query, params).fetchall()
    finally:
        cursor.close()

    return [{"id": row[0], "name": row[1], "price": row[2]} for row in rows]
