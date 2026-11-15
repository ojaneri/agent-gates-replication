import sqlite3


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def search_products(conn: sqlite3.Connection, name_contains: str = "", max_price: float | None = None,
                    order_by: str = "name", descending: bool = False, limit: int = 20,
                    offset: int = 0) -> list[dict]:
    """Search products. See spec.md."""
    if order_by not in ("name", "price"):
        raise ValueError("order_by must be 'name' or 'price'")
    if not _is_int(limit) or not 1 <= limit <= 100:
        raise ValueError("limit must be an integer from 1 to 100")
    if not _is_int(offset) or offset < 0:
        raise ValueError("offset must be an integer of at least 0")

    # instr() does a literal substring match, so '%' and '_' are not wildcards.
    # lower() only folds ASCII letters in SQLite's default build, as the spec requires.
    conditions = ["stock > 0"]
    params: list = []
    if name_contains:
        conditions.append("instr(lower(name), lower(?)) > 0")
        params.append(name_contains)
    if max_price is not None:
        conditions.append("price <= ?")
        params.append(max_price)

    direction = "DESC" if descending else "ASC"
    sql = (
        "SELECT id, name, price FROM products WHERE " + " AND ".join(conditions)
        + f" ORDER BY {order_by} {direction}, id ASC LIMIT ? OFFSET ?"
    )
    params.extend([limit, offset])

    rows = conn.execute(sql, params).fetchall()
    return [{"id": row[0], "name": row[1], "price": row[2]} for row in rows]
