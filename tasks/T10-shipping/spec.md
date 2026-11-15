# Parcel shipping cost

Implement `shipping_cost(length_cm, width_cm, height_cm, weight_kg, zone, subtotal)` in `solution.py`. It returns the shipping charge as a `decimal.Decimal` with exactly two decimal places.

## Inputs

- `length_cm`, `width_cm`, `height_cm`, `weight_kg`, `subtotal`: numbers (`int`, `float` or `Decimal`; `bool` is not a number here). A float is converted through its `str()` form, so `0.1` means exactly `0.1`. Anything else raises `TypeError`.
- The three dimensions and the weight must be greater than zero, and `subtotal` must be zero or more. Otherwise raise `ValueError`.
- `zone` must be the `int` 1, 2 or 3. Anything else (including `True`, `1.0` or `"1"`) raises `ValueError`.

## Rules

1. **Volumetric weight** = length × width × height / 5000 (kg).
2. **Billable weight** = the larger of the actual weight and the volumetric weight, **rounded up** to the next multiple of 0.5 kg (a value that already is a multiple stays as it is).
3. **Base charge** = 8.00 for the first kilogram, plus 1.50 for each further 0.5 kg of billable weight. A billable weight of 0.5 kg or 1 kg costs 8.00; 1.5 kg costs 9.50; 2 kg costs 11.00.
4. The base charge is multiplied by the **zone factor**: zone 1 → 1, zone 2 → 1.25, zone 3 → 1.6.
5. **Free shipping:** if `subtotal` is 150 or more **and** the zone is 1 or 2, the base charge (after the zone factor) is 0.
6. **Oversize surcharge:** if the longest side is **greater than** 120 cm, add 12.00. The surcharge is not multiplied by the zone factor and is not waived by free shipping.
7. Round the total to 2 decimal places with `ROUND_HALF_UP`, only at the end.
