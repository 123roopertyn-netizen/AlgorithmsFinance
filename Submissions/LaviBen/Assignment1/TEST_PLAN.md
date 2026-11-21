# Tests-first plan and independent expectations

This plan and the executable tests were completed before creating an
`orderbook/` implementation package.

## Evidence categories

| Requirement or risk | Independent evidence |
|---|---|
| Empty book and required API | `test_empty_book_and_required_public_api` |
| One resting order and defensive inspection copy | `test_one_order_rests_and_inspection_is_canonical_copy` |
| FIFO independent of identifier spelling | Makers `z_first`, then `a_second`; expected fills remain arrival-ordered |
| Best-price priority | Older bid at 100 must lose to later bids at 102 and 101 |
| Market statuses | Separately calculated empty, exact-depth and oversized cases |
| Partial-maker priority | First maker is partially filled, then must execute before the next maker |
| Crossing limits and maker-price execution | Hand-calculated crossing buy and sell cases at multiple prices |
| Cancellation state changes | Before execution, after partial fill, after full fill, repeated and unknown targets |
| Long FIFO queue | 200 makers with reverse-lexical identifiers |
| Validation and atomic rejection | Stable reason/precedence table plus a lower-sequence valid follow-up |
| Quantity conservation | Incoming quantity equals fills plus reported residual after every submission |
| Maker conservation | Each maker's before/after residual differs by exactly its ordered fills |
| Cancellation conservation | Cancelled quantity equals the target's prior residual |
| Proceeds | Integer sum of resting price times executed quantity |
| Worked example | Exact supplied fills, remaining book and `359400.00` USD proceeds |
| Supplied data integrity | Byte count, SHA-256, event count, event-type count, sequence and metadata checks |
| Version agreement | Results and canonical books compared after every event in ten generated streams |

## Hand-calculated conservation stream

The conservation test deliberately crosses and rests both sides:

1. Bid `bid1`: 5 units at 105.
2. Bid `bid2`: 4 units at 103.
3. Ask `ask1`: 2 units at 110.
4. Sell limit: 7 units at 104; fills `bid1` for 5 at 105 and rests 2 at 104.
5. Buy limit: 3 units at 105; fills the resting sell for 2 at 104 and rests 1 at 105.
6. Market sell: 6 units; fills 1 at 105 and 4 at 103, then discards 1 unfilled.
7. Cancel `ask1`: removes its unchanged 2-unit residual.

Total tick-times-quantity proceeds are
`105*5 + 104*2 + 105*1 + 103*4 = 1250`.

## Failing baseline requirement

The first run must use:

```bash
python3 -m unittest discover -s tests -v
```

It is expected to fail because `orderbook.baseline.BaselineOrderBook` and
`orderbook.revised.RevisedOrderBook` do not yet exist. Fixture-only tests should
already pass. The observed command, exit status and failure summary are recorded
in `TESTS_FIRST_BASELINE.md` before implementation begins.

Passing tests will be evidence, not proof. Final documentation must also state
the invariants and complexity reasoning for the versions actually measured.
