import sqlite3


def _is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def search_products(conn: sqlite3.Connection, name_contains: str = "", max_price: float | None = None,
                    order_by: str = "name", descending: bool = False, limit: int = 20,
                    offset: int = 0) -> list[dict]:
    """Search products. See spec.md."""
    if order_by not in ("name", "price"):
        raise ValueError("order_by must be 'name' or 'price'")
    if not _is_int(limit) or not 1 <= limit <= 100:
        raise ValueError("limit must be an integer from 1 to 100")
    if not _is_int(offset) or offset < 0:
        raise ValueError("offset must be an integer >= 0")

    sql = "SELECT id, name, price FROM products WHERE stock > 0"
    params: list = []
    if name_contains:
        sql += " AND instr(lower(name), lower(?)) > 0"
        params.append(name_contains)
    if max_price is not None:
        sql += " AND price <= ?"
        params.append(max_price)
    direction = "DESC" if descending else "ASC"
    sql += f" ORDER BY {order_by} {direction}, id ASC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    rows = conn.execute(sql, params).fetchall()
    return [{"id": r[0], "name": r[1], "price": r[2]} for r in rows]
