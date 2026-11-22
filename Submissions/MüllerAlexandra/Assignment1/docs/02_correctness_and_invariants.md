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

## Baseline dispatcher pseudocode

For every event:

```text
build the set of active order identifiers
validate the complete event before changing the book
if validation fails:
    return rejected without changing the book or accepted sequence
dispatch LIMIT, MARKET_SELL, or CANCEL to its operation
record the event sequence as the last accepted sequence
return only this event's result
```

## Baseline limit insertion pseudocode

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
return only this event's fills and residual
```

## Baseline market-selling pseudocode

For an incoming market sell:

```text
validate the complete event
collect every resting bid
sort bids by decreasing price, then increasing arrival sequence
for each maker while incoming quantity remains:
    execute min(incoming remainder, maker remainder)
    record a fill at the maker's resting price
    subtract the same quantity from seller and maker
    remove an exhausted maker
return any unmatched market quantity as unfilled; never rest it
return only this event's fills and unfilled quantity
```

## Baseline cancellation pseudocode

For a cancellation:

```text
validate the complete event
scan active orders in the list for target_order_id
if the target is active:
    remember its current residual quantity
    remove the order
    return cancelled with exactly that residual quantity
otherwise:
    return not_found with cancelled quantity zero
```

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
