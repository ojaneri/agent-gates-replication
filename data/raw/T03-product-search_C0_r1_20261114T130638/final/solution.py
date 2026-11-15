import sqlite3


def search_products(conn: sqlite3.Connection, name_contains: str = "", max_price: float | None = None,
                    order_by: str = "name", descending: bool = False, limit: int = 20,
                    offset: int = 0) -> list[dict]:
    """Search products. See spec.md."""
    # Validate arguments before touching the database.
    if order_by not in ("name", "price"):
        raise ValueError("order_by must be 'name' or 'price'")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError("limit must be an integer from 1 to 100")
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        raise ValueError("offset must be an integer of at least 0")
    if not isinstance(name_contains, str):
        raise ValueError("name_contains must be a string")

    # Only fixed, whitelisted fragments are placed into the SQL text;
    # every user-supplied value is passed as a bound parameter.
    direction = "DESC" if descending else "ASC"
    if order_by == "name":
        order_clause = f"name {direction}, id ASC"
    else:
        order_clause = f"price {direction}, id ASC"

    conditions = ["stock > 0"]
    params: list = []

    if name_contains != "":
        # instr() is a plain substring test, so '%' and '_' carry no special meaning.
        # lower() folds ASCII letters only (SQLite default), as the spec requires.
        conditions.append("instr(lower(name), lower(?)) > 0")
        params.append(name_contains)

    if max_price is not None:
        conditions.append("price <= ?")
        params.append(max_price)

    sql = (
        "SELECT id, name, price FROM products "
        f"WHERE {' AND '.join(conditions)} "
        f"ORDER BY {order_clause} "
        "LIMIT ? OFFSET ?"
    )
    params.extend([limit, offset])

    cursor = conn.execute(sql, params)
    rows = cursor.fetchall()
    return [{"id": row[0], "name": row[1], "price": row[2]} for row in rows]
