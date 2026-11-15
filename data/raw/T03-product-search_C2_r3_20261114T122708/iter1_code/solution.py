import sqlite3

_BASE = ("SELECT id, name, price FROM products WHERE stock > 0 "
         "AND name LIKE ? ESCAPE '\\' AND (? IS NULL OR price <= ?) ")
_QUERIES = {
    ("name", False): _BASE + "ORDER BY name ASC, id ASC LIMIT ? OFFSET ?",
    ("name", True): _BASE + "ORDER BY name DESC, id ASC LIMIT ? OFFSET ?",
    ("price", False): _BASE + "ORDER BY price ASC, id ASC LIMIT ? OFFSET ?",
    ("price", True): _BASE + "ORDER BY price DESC, id ASC LIMIT ? OFFSET ?",
}


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
        raise ValueError("offset must be an integer >= 0")
    escaped = (name_contains.replace("\\", "\\\\")
               .replace("%", "\\%").replace("_", "\\_"))
    sql = _QUERIES[(order_by, bool(descending))]
    rows = conn.execute(sql, (f"%{escaped}%", max_price, max_price, limit, offset)).fetchall()
    return [{"id": r[0], "name": r[1], "price": r[2]} for r in rows]
