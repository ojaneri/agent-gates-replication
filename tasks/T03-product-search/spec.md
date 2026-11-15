# Product search (SQLite)

Implement `search_products` in `solution.py`. It queries a SQLite database through the `sqlite3.Connection` it receives. The table already exists:

```sql
CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, price REAL NOT NULL, stock INTEGER NOT NULL);
```

```python
search_products(conn, name_contains="", max_price=None, order_by="name", descending=False, limit=20, offset=0)
    -> list[dict]
```

## Rules

1. Return only products with `stock` greater than 0.
2. `name_contains` filters by substring of `name`, case-insensitive for ASCII letters. An empty string matches every name. The characters `%` and `_` in `name_contains` are ordinary characters, not wildcards: searching for `"50%"` matches only names that contain the text `50%`.
3. `max_price`, when not `None`, keeps only products with `price <= max_price`.
4. `order_by` must be `"name"` or `"price"`. Any other value raises `ValueError`. `descending=True` reverses that order. Ordering by name uses SQLite's default text ordering (binary, so uppercase letters sort before lowercase).
5. Ties in the chosen order are always broken by `id`, ascending, whatever `descending` is.
6. `limit` must be an integer from 1 to 100 and `offset` an integer of at least 0. Otherwise raise `ValueError`. Apply them after filtering and ordering.
7. Each result is a dict with exactly the keys `id`, `name` and `price`.
8. The function must never modify the database.

Do not change the function signature.
