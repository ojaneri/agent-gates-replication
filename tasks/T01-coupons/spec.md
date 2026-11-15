# Order total with coupons

Implement `order_total` in `solution.py`.

```python
order_total(items, coupon, today, used_codes) -> Decimal
```

## Inputs

- `items`: list of `(sku, unit_price, quantity)` tuples. `unit_price` is a `Decimal`, `quantity` an `int`.
- `coupon`: `None` or a dict with keys:
  - `code` (str)
  - `kind`: `"percent"` or `"fixed"`
  - `value` (`Decimal`): percentage for `"percent"`, amount for `"fixed"`
  - `min_subtotal` (`Decimal`)
  - `expires` (`datetime.date`)
- `today`: `datetime.date`
- `used_codes`: set of coupon codes this customer already used.

## Rules

1. Every `quantity` must be an integer of at least 1, and every `unit_price` must be at least 0. Otherwise raise `ValueError`.
2. The subtotal is the sum of `unit_price * quantity`. An empty list has subtotal 0.
3. Coupon validity. If any of these hold, raise `CouponError` (already defined in the stub):
   - the coupon expired: it is valid up to and including its `expires` date;
   - its code is in `used_codes`;
   - the subtotal is below `min_subtotal` (a subtotal equal to `min_subtotal` is accepted);
   - `kind` is neither `"percent"` nor `"fixed"`.
4. A `"percent"` coupon must have `0 < value <= 100`, otherwise raise `ValueError`. The discount is `subtotal * value / 100`.
5. A `"fixed"` coupon must have `value > 0`, otherwise raise `ValueError`. The discount is `value`, but never more than the subtotal.
6. Shipping is computed on the subtotal **after** the discount: below 100.00 it costs 10.00; at 100.00 or more it is free. An empty order (subtotal 0, no items) has no shipping.
7. The result is `subtotal - discount + shipping`, rounded to 2 decimal places, with halves rounded up (`ROUND_HALF_UP`).

Do not change the function signature or the `CouponError` class.
