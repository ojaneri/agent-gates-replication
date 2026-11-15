import sqlite3

ORDER_COLUMNS = {"name": "name", "price": "price"}


def _escape_like(text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _validate(order_by, limit, offset):
    if order_by not in ORDER_COLUMNS:
        raise ValueError("order_by must be 'name' or 'price'")
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 100:
        raise ValueError("limit must be an integer from 1 to 100")
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise ValueError("offset must be an integer >= 0")


def search_products(conn: sqlite3.Connection, name_contains: str = "", max_price: float | None = None,
                    order_by: str = "name", descending: bool = False, limit: int = 20,
                    offset: int = 0) -> list[dict]:
    _validate(order_by, limit, offset)
    where = ["stock > 0", "name LIKE ? ESCAPE '\\'"]
    params: list = ["%" + _escape_like(name_contains) + "%"]
    if max_price is not None:
        where.append("price <= ?")
        params.append(max_price)
    direction = "DESC" if descending else "ASC"
    parts = ["SELECT id, name, price FROM products WHERE", " AND ".join(where),
             "ORDER BY", ORDER_COLUMNS[order_by], direction, ", id ASC LIMIT ? OFFSET ?"]
    params += [limit, offset]
    rows = conn.execute(" ".join(parts), params).fetchall()
    return [{"id": r[0], "name": r[1], "price": r[2]} for r in rows]
