# Invoice totals with tax, bulk discount and credit

Implement `invoice_totals` in `solution.py`. All money values are `decimal.Decimal`.

```python
invoice_totals(lines, region, credit=Decimal("0")) -> dict
```

## Inputs

- `lines`: list of dicts with keys `sku` (str), `category` (str), `unit_price` (`Decimal`), `qty` (`int`) and, optionally, `discount_pct` (`Decimal`, default 0).
- `region`: `"A"` or `"B"`.
- `credit`: store credit available to the customer, a `Decimal`.

## Tax rates (percent)

| Region | food | books | standard |
|---|---|---|---|
| A | 0 | 5 | 20 |
| B | 7 | 7 | 15 |

## Rules

1. Raise `ValueError` if: the region is unknown; a category is not one of the three above; `qty` is not an integer of at least 1 (a `bool` is not accepted); `unit_price` is negative; `discount_pct` is outside 0 to 100 (both ends allowed); `credit` is negative.
2. **Line net.** `unit_price * qty`, reduced by the line's `discount_pct`. If the category is `standard` **and** `qty` is 10 or more, an extra 5% bulk discount applies to that line, **on top of** its own discount (the two are multiplied: 10% and then 5% leaves 85.5%, not 85%). The line net is then rounded to cents.
3. **Line tax.** The rounded line net times the line's tax rate, rounded to cents.
4. All rounding is to 2 decimal places with halves rounded up (`ROUND_HALF_UP`), and it happens **per line**, never on the totals.
5. **Totals.** `net` and `tax` are the sums of the line values. `gross = net + tax`.
6. **Credit.** The credit pays part or all of `gross`. `credit_used` is the smaller of `credit` and `gross`. `total_due = gross - credit_used`. `credit_left = credit - credit_used`.
7. **Tax by rate.** `tax_by_rate` maps each tax rate (an `int`, e.g. `20`) that appears on at least one line to the sum of tax for those lines. A rate of 0 that appears on a line is included, with value 0.00. Rates that appear on no line are not included.
8. Return a dict with keys `net`, `tax`, `gross`, `credit_used`, `total_due`, `credit_left` and `tax_by_rate`. Every money value has exactly 2 decimal places. An empty `lines` list gives all zeros and an empty `tax_by_rate`.

Do not change the function signature.
