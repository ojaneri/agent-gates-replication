import sqlite3


def search_products(conn: sqlite3.Connection, name_contains: str = "", max_price: float | None = None,
                    order_by: str = "name", descending: bool = False, limit: int = 20,
                    offset: int = 0) -> list[dict]:
    """Search products. See spec.md."""
    # --- Validation -------------------------------------------------------
    if not isinstance(name_contains, str):
        raise ValueError("name_contains must be a string")
    if isinstance(limit, bool) or not isinstance(limit, int) or not (1 <= limit <= 100):
        raise ValueError("limit must be an integer from 1 to 100")
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        raise ValueError("offset must be an integer of at least 0")
    if not isinstance(order_by, str) or order_by not in ("name", "price"):
        raise ValueError("order_by must be 'name' or 'price'")

    # Column names come only from this fixed mapping, never from user input.
    order_column = "name" if order_by == "name" else "price"
    direction = "DESC" if descending else "ASC"

    # --- Query building ---------------------------------------------------
    # Only the stock rule is always present; the rest are optional clauses.
    conditions = ["stock > 0"]
    params: list = []

    # Substring match done with instr() so that '%' and '_' are literal
    # characters. lower() is applied to both sides so matching is
    # case-insensitive for ASCII letters (SQLite's lower() is ASCII-only by
    # default, which matches the spec).
    if name_contains != "":
        conditions.append("instr(lower(name), lower(?)) > 0")
        params.append(name_contains)

    if max_price is not None:
        conditions.append("price <= ?")
        params.append(max_price)

    sql = (
        "SELECT id, name, price FROM products "
        f"WHERE {' AND '.join(conditions)} "
        f"ORDER BY {order_column} {direction}, id ASC "
        "LIMIT ? OFFSET ?"
    )
    params.extend([limit, offset])

    # --- Execution (read-only) --------------------------------------------
    cursor = conn.execute(sql, params)
    rows = cursor.fetchall()
    return [{"id": row[0], "name": row[1], "price": row[2]} for row in rows]
