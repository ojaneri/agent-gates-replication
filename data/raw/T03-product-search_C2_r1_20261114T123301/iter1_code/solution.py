import sqlite3


# One fixed statement per (order_by, descending) combination. No SQL text is
# ever built from caller input; all user values are bound as parameters.
_QUERIES = {
    ("name", False): (
        "SELECT id, name, price FROM products "
        "WHERE stock > 0 "
        "AND (? IS NULL OR instr(lower(name), lower(?)) > 0) "
        "AND (? IS NULL OR price <= ?) "
        "ORDER BY name ASC, id ASC LIMIT ? OFFSET ?"
    ),
    ("name", True): (
        "SELECT id, name, price FROM products "
        "WHERE stock > 0 "
        "AND (? IS NULL OR instr(lower(name), lower(?)) > 0) "
        "AND (? IS NULL OR price <= ?) "
        "ORDER BY name DESC, id ASC LIMIT ? OFFSET ?"
    ),
    ("price", False): (
        "SELECT id, name, price FROM products "
        "WHERE stock > 0 "
        "AND (? IS NULL OR instr(lower(name), lower(?)) > 0) "
        "AND (? IS NULL OR price <= ?) "
        "ORDER BY price ASC, id ASC LIMIT ? OFFSET ?"
    ),
    ("price", True): (
        "SELECT id, name, price FROM products "
        "WHERE stock > 0 "
        "AND (? IS NULL OR instr(lower(name), lower(?)) > 0) "
        "AND (? IS NULL OR price <= ?) "
        "ORDER BY price DESC, id ASC LIMIT ? OFFSET ?"
    ),
}


def _check_int(value: object, low: int, high: int | None, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    if value < low or (high is not None and value > high):
        raise ValueError(f"{label} is out of range")


def search_products(conn: sqlite3.Connection, name_contains: str = "", max_price: float | None = None,
                    order_by: str = "name", descending: bool = False, limit: int = 20,
                    offset: int = 0) -> list[dict]:
    """Search products. See spec.md."""
    if order_by not in ("name", "price"):
        raise ValueError("order_by must be 'name' or 'price'")
    _check_int(limit, 1, 100, "limit")
    _check_int(offset, 0, None, "offset")

    # An empty name filter is passed as NULL, which the SQL treats as "no filter".
    name_param = None if name_contains == "" else name_contains
    query = _QUERIES[(order_by, bool(descending))]
    rows = conn.execute(
        query,
        (name_param, name_param, max_price, max_price, limit, offset),
    ).fetchall()
    return [{"id": row[0], "name": row[1], "price": row[2]} for row in rows]
