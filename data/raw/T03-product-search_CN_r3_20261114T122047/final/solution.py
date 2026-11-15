import sqlite3


def search_products(conn: sqlite3.Connection, name_contains: str = "", max_price: float | None = None,
                    order_by: str = "name", descending: bool = False, limit: int = 20,
                    offset: int = 0) -> list[dict]:
    """Search products. See spec.md."""
    if order_by == "name":
        order_column = "name"
    elif order_by == "price":
        order_column = "price"
    else:
        raise ValueError("order_by must be 'name' or 'price'")

    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError("limit must be an integer from 1 to 100")
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        raise ValueError("offset must be an integer of at least 0")

    direction = "DESC" if descending else "ASC"

    # instr() is a literal substring test, so '%' and '_' are not wildcards.
    # lower() only folds ASCII letters in SQLite (without ICU), matching the spec.
    conditions = ["stock > 0"]
    params: list = []
    if name_contains:
        conditions.append("instr(lower(name), lower(?)) > 0")
        params.append(name_contains)
    if max_price is not None:
        conditions.append("price <= ?")
        params.append(max_price)

    sql = (
        "SELECT id, name, price FROM products "
        "WHERE " + " AND ".join(conditions) + " "
        f"ORDER BY {order_column} {direction}, id ASC "
        "LIMIT ? OFFSET ?"
    )
    params.extend([limit, offset])

    cursor = conn.execute(sql, params)
    return [{"id": row[0], "name": row[1], "price": row[2]} for row in cursor.fetchall()]
