# Report: <exercise>

## 1. Specification and modelling boundaries
What is modelled, what is explicitly out of scope.

## 2. Correctness reasoning
- Invariants and why each operation preserves them
- Conservation checks
- Test evidence: command + result line (tests are evidence, not proof)

## 3. Algorithms and complexity
Pseudocode for each measured version. Table: operation × version × cost, with
bound type (worst-case / expected / amortized) and the symbols defined.

## 4. Runtime
Throughput, scaling plots, latency percentiles (convention stated), prediction vs measurement.

## 5. Memory
tracemalloc peak/current, what is included, growth and post-cleanup behaviour.

## 6. Profiling and one explained bottleneck
Code location + operation counts + complexity argument.

## 7. Revision
What changed between versions, why, the measured effect, workloads where it did *not* win.

## 8. Limitations
Machine, Python version, synthetic data, closed-loop latency, anything stopped or missing.

## 9. AI usage
Summary; details in 00_docs/AI_LOG.md.
