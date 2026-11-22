# Correctness and invariants

## State invariants

After every accepted event:

1. Every active order appears exactly once.
2. Every resting quantity is a positive integer.
3. Every resting order retains its original accepted `seq` as `arrival_seq`.
4. At a price, lower `arrival_seq` has FIFO priority.
5. The best bid is strictly below the best ask whenever both sides are nonempty.
6. An executed or cancelled order is absent from the active state.
7. The last accepted sequence changes only after a valid event completes.

Validation is performed before dispatch. A rejected event therefore cannot
partially match, cancel, rest, or advance the accepted sequence.

## Baseline matching pseudocode

For an incoming limit order:

```text
validate the complete event
collect eligible opposite-side resting orders
sort them by best price, then increasing arrival sequence
for each maker while incoming quantity remains:
    execute min(incoming remainder, maker remainder)
    record a fill at the maker's resting price
    subtract the same quantity from taker and maker
    remove an exhausted maker
if incoming limit quantity remains:
    append it with its original sequence
accept the event sequence and return only this event's fills
```

`FillMarketSell` uses the same loop over all bids ordered by decreasing price
then increasing arrival sequence. It discards rather than rests any residual.

## Why the invariants are preserved

- Validation admits only positive integer price/quantity fields and prevents a
  second active order with the same identifier.
- Sorting eligible makers by price and arrival implements price-time priority.
- A partial maker stays in the same object with the same arrival sequence.
- Exhausted makers are removed before another event is processed.
- A residual limit is appended only after all eligible opposite orders have
  been exhausted, so the resting book cannot remain crossed.
- Every fill subtracts the same integer quantity from incoming and maker
  remainders. Thus incoming quantity equals fills plus returned residual, and
  each maker loses exactly its fills.
- Cancellation returns and removes exactly the target's current residual.

These arguments and passing tests provide evidence; they are not a formal
proof for arbitrary Python objects outside the documented event contract.
