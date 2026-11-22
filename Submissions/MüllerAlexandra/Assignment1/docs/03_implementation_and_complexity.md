# Implementation and complexity

Let `B` be active individual orders, `P` occupied price levels, and `F` maker
fills produced by an incoming event. Version A stores a single Python list of
`B` mutable `RestingOrder` values.

## Baseline operations

### Validation

The baseline constructs the set of active identifiers before every event.
That costs `O(B)` time and `O(B)` temporary space. Field checks are constant
after that construction.

### Resting insertion

Appending a noncrossing residual is amortized `O(1)`, but the dispatcher has
already paid the `O(B)` validation cost. Finding eligible makers scans all
active orders. If `K <= B` makers are eligible, sorting them costs
`O(K log K)` time and `O(K)` temporary space.

### Matching and market selling

Each fill update is constant work, but removing an exhausted maker from the
middle of the list costs `O(B)` because later references shift. Consequently,
the directly implemented worst-case matching cost is

```text
O(B + K log K + F B)
```

including validation, candidate construction, sorting, state updates, and
fill-list construction. The returned `F` fill records are required output,
not auxiliary space. Candidate storage and active-identifier validation use
`O(B)` temporary space.

### Cancellation

Cancellation scans for the target and removes it from the list, so it is
`O(B)` time and `O(B)` temporary space including the shared validation set.

### Inspection

Canonical inspection sorts bids and asks, requiring `O(B log B)` time and
`O(B)` returned output plus sorting workspace.

## Revision target

Version B must preserve identical results while avoiding repeated whole-book
identifier construction, whole-book scans, and repeated list shifts. Its data
organization and complexity will be documented only after the design is
implemented and measured against this preserved baseline.
