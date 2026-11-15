import sqlite3

_ORDERS = {"name": "name", "price": "price"}


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _validate(order_by, limit, offset) -> None:
    if order_by not in _ORDERS:
        raise ValueError("order_by must be 'name' or 'price'")
    if not _is_int(limit) or not 1 <= limit <= 100:
        raise ValueError("limit must be an integer from 1 to 100")
    if not _is_int(offset) or offset < 0:
        raise ValueError("offset must be an integer >= 0")


def _escape_like(text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def search_products(conn: sqlite3.Connection, name_contains: str = "", max_price: float | None = None,
                    order_by: str = "name", descending: bool = False, limit: int = 20,
                    offset: int = 0) -> list[dict]:
    """Search products. See spec.md."""
    _validate(order_by, limit, offset)
    column = _ORDERS[order_by]
    direction = "DESC" if descending else "ASC"
    sql = "SELECT id, name, price FROM products WHERE stock > 0 AND name LIKE ? ESCAPE '\\'"
    params: list = ["%" + _escape_like(name_contains) + "%"]
    if max_price is not None:
        sql += " AND price <= ?"
        params.append(max_price)
    sql += " ORDER BY " + column + " " + direction + ", id ASC LIMIT ? OFFSET ?"  # nosec B608
    params.extend([limit, offset])
    rows = conn.execute(sql, params).fetchall()
    return [{"id": r[0], "name": r[1], "price": r[2]} for r in rows]
