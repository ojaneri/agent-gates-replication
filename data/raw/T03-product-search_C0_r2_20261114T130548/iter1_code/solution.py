import sqlite3


def _check_int(value, name, minimum, maximum=None):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    if value < minimum or (maximum is not None and value > maximum):
        if maximum is None:
            raise ValueError(f"{name} must be at least {minimum}")
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return value


def search_products(conn: sqlite3.Connection, name_contains: str = "", max_price: float | None = None,
                    order_by: str = "name", descending: bool = False, limit: int = 20,
                    offset: int = 0) -> list[dict]:
    """Search products. See spec.md."""
    if order_by not in ("name", "price"):
        raise ValueError("order_by must be 'name' or 'price'")
    limit = _check_int(limit, "limit", 1, 100)
    offset = _check_int(offset, "offset", 0)

    clauses = ["stock > 0"]
    params: list = []

    if name_contains:
        # Escape LIKE wildcards so '%' and '_' are literal characters.
        # instr() on lower-cased text is a literal substring test, so no
        # escaping is needed and LIKE's case_sensitive_like setting is irrelevant.
        clauses.append("instr(lower(name), lower(?)) > 0")
        params.append(name_contains)

    if max_price is not None:
        clauses.append("price <= ?")
        params.append(max_price)

    direction = "DESC" if descending else "ASC"
    # Ties are always broken by id ascending.
    sql = (
        "SELECT id, name, price FROM products "
        "WHERE " + " AND ".join(clauses) + " "
        f"ORDER BY {order_by} {direction}, id ASC "
        "LIMIT ? OFFSET ?"
    )
    params.extend([limit, offset])

    cur = conn.execute(sql, params)
    try:
        rows = cur.fetchall()
    finally:
        cur.close()
    return [{"id": r[0], "name": r[1], "price": r[2]} for r in rows]
