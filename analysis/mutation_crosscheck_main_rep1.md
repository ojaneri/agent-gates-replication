# Mutation engine cross-check (gates/mutate.py vs cosmic-ray 8.4.1)

Source: <project>\study\data\raw

Runs compared: 36. Spearman rho = 0.640 (p = 2.61e-05).
Mean score: ours 0.946, cosmic-ray 0.945. Mean mutants per run: ours 32.9, cosmic-ray 146.3.

| run_id                                   | task               | condition   | model             |   ours_total |   ours_score |   cr_killed |   cr_survived |   cr_incompetent |   cr_score |
|:-----------------------------------------|:-------------------|:------------|:------------------|-------------:|-------------:|------------:|--------------:|-----------------:|-----------:|
| T01-coupons_C0_r1_20261114T122546        | T01-coupons        | C0          | claude-sonnet-5-5 |           32 |       0.875  |         150 |            14 |                0 |     0.9146 |
| T01-coupons_C0_r1_20261114T122914        | T01-coupons        | C0          | claude-haiku-5-5  |           28 |       0.9643 |         146 |             4 |                0 |     0.9733 |
| T01-coupons_C1_r1_20261114T123022        | T01-coupons        | C1          | claude-sonnet-5-5 |           34 |       0.9118 |         156 |            10 |                0 |     0.9398 |
| T01-coupons_C1_r1_20261114T130807        | T01-coupons        | C1          | claude-haiku-5-5  |           29 |       1      |         158 |             2 |                0 |     0.9875 |
| T01-coupons_C2_r1_20261114T122105        | T01-coupons        | C2          | claude-haiku-5-5  |           38 |       0.9474 |         156 |             4 |                0 |     0.975  |
| T01-coupons_C2_r1_20261114T122210        | T01-coupons        | C2          | claude-sonnet-5-5 |           35 |       0.9429 |         150 |             7 |                0 |     0.9554 |
| T02-booking_C0_r1_20261114T124439        | T02-booking        | C0          | claude-sonnet-5-5 |           39 |       0.8718 |         164 |            13 |                0 |     0.9266 |
| T02-booking_C0_r1_20261114T124958        | T02-booking        | C0          | claude-haiku-5-5  |           35 |       1      |         147 |            10 |                0 |     0.9363 |
| T02-booking_C1_r1_20261114T121849        | T02-booking        | C1          | claude-haiku-5-5  |           35 |       1      |         147 |            10 |                0 |     0.9363 |
| T02-booking_C1_r1_20261114T121929        | T02-booking        | C1          | claude-sonnet-5-5 |           39 |       0.8718 |         165 |            10 |                0 |     0.9429 |
| T02-booking_C2_r1_20261114T122001        | T02-booking        | C2          | claude-sonnet-5-5 |           41 |       0.878  |         163 |            13 |                0 |     0.9261 |
| T02-booking_C2_r1_20261114T130132        | T02-booking        | C2          | claude-haiku-5-5  |           42 |       0.9524 |         170 |             6 |                0 |     0.9659 |
| T03-product-search_C0_r1_20261114T123715 | T03-product-search | C0          | claude-sonnet-5-5 |           25 |       0.84   |          71 |             9 |                0 |     0.8875 |
| T03-product-search_C0_r1_20261114T130638 | T03-product-search | C0          | claude-haiku-5-5  |           20 |       1      |          69 |             7 |                0 |     0.9079 |
| T03-product-search_C1_r1_20261114T123832 | T03-product-search | C1          | claude-sonnet-5-5 |           24 |       0.875  |          73 |             7 |                0 |     0.9125 |
| T03-product-search_C1_r1_20261114T125133 | T03-product-search | C1          | claude-haiku-5-5  |           22 |       1      |          79 |             2 |                0 |     0.9753 |
| T03-product-search_C2_r1_20261114T123301 | T03-product-search | C2          | claude-haiku-5-5  |           16 |       1      |          70 |             3 |                0 |     0.9589 |
| T03-product-search_C2_r1_20261114T124557 | T03-product-search | C2          | claude-sonnet-5-5 |           22 |       1      |         167 |             2 |                0 |     0.9882 |
| T04-invoice_C0_r1_20261114T122218        | T04-invoice        | C0          | claude-haiku-5-5  |           34 |       0.9706 |         193 |             4 |                0 |     0.9797 |
| T04-invoice_C0_r1_20261114T124246        | T04-invoice        | C0          | claude-sonnet-5-5 |           48 |       0.9375 |         202 |            13 |                0 |     0.9395 |
| T04-invoice_C1_r1_20261114T121615        | T04-invoice        | C1          | claude-sonnet-5-5 |           37 |       0.973  |         195 |             6 |                0 |     0.9701 |
| T04-invoice_C1_r1_20261114T123854        | T04-invoice        | C1          | claude-haiku-5-5  |           34 |       1      |         185 |             4 |                0 |     0.9788 |
| T04-invoice_C2_r1_20261114T123306        | T04-invoice        | C2          | claude-sonnet-5-5 |           36 |       1      |         203 |             5 |                0 |     0.976  |
| T04-invoice_C2_r1_20261114T131016        | T04-invoice        | C2          | claude-haiku-5-5  |           34 |       1      |         195 |             2 |                0 |     0.9898 |
| T05-rate-limiter_C0_r1_20261114T121643   | T05-rate-limiter   | C0          | claude-haiku-5-5  |           52 |       0.9808 |         191 |            11 |                0 |     0.9455 |
| T05-rate-limiter_C0_r1_20261114T122923   | T05-rate-limiter   | C0          | claude-sonnet-5-5 |           54 |       0.8333 |         174 |            16 |                0 |     0.9158 |
| T05-rate-limiter_C1_r1_20261114T125001   | T05-rate-limiter   | C1          | claude-sonnet-5-5 |           35 |       0.8857 |         140 |            12 |                0 |     0.9211 |
| T05-rate-limiter_C1_r1_20261114T125229   | T05-rate-limiter   | C1          | claude-haiku-5-5  |           54 |       0.963  |         179 |             5 |                0 |     0.9728 |
| T05-rate-limiter_C2_r1_20261114T124704   | T05-rate-limiter   | C2          | claude-sonnet-5-5 |           34 |       0.9706 |         139 |             6 |                0 |     0.9586 |
| T05-rate-limiter_C2_r1_20261114T125612   | T05-rate-limiter   | C2          | claude-haiku-5-5  |           40 |       0.975  |         164 |             8 |                0 |     0.9535 |
| T06-safe-extract_C0_r1_20261114T121545   | T06-safe-extract   | C0          | claude-haiku-5-5  |           21 |       0.9524 |          53 |             6 |                0 |     0.8983 |
| T06-safe-extract_C0_r1_20261114T124026   | T06-safe-extract   | C0          | claude-sonnet-5-5 |           25 |       0.88   |          88 |            11 |                0 |     0.8889 |
| T06-safe-extract_C1_r1_20261114T123144   | T06-safe-extract   | C1          | claude-sonnet-5-5 |           27 |       0.8889 |          95 |            10 |                0 |     0.9048 |
| T06-safe-extract_C1_r1_20261114T130043   | T06-safe-extract   | C1          | claude-haiku-5-5  |           20 |       0.95   |          51 |             6 |                0 |     0.8947 |
| T06-safe-extract_C2_r1_20261114T121733   | T06-safe-extract   | C2          | claude-sonnet-5-5 |           22 |       1      |          80 |             2 |                0 |     0.9756 |
| T06-safe-extract_C2_r1_20261114T131156   | T06-safe-extract   | C2          | claude-haiku-5-5  |           22 |       0.9545 |          74 |             5 |                0 |     0.9367 |
