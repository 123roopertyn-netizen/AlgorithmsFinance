# AI log

Tool: Claude (Claude Opus 5.5), used as a tutor and coding assistant. Bastian sets the
specification decisions, the order of the phases and reviews every step. This log records
what was accepted, corrected or rejected, with evidence (commit hashes, test output).

## Phase 0: setup and specification

| Suggestion | Decision | Reason / evidence |
|---|---|---|
| Folder `Submissions/BundschuhBastian/Assignment1/`, same conventions as the lab (venv, pytest.ini, AI log) | accepted | course README; lab submission |
| `SPEC.md` with decision IDs D1-D19 and fixed reason codes, so A and B return identical results | accepted (pending review) | needed for exact A-vs-B comparison |
| D1: `bool` and float are not integers (`type(x) is int`) | pending review | `isinstance(True, int)` is True in Python |
| D5: duplicate live ID check also for MARKET_SELL | pending review | spec says "duplicate live submission identifiers" |
| Record decompressed sha256 in addition to the .gz sha256 | accepted | regenerating `mixed` seed 42 with Python 3.13 / zlib-ng gave a different .gz hash but identical decompressed content |

## Accepted

## Corrected

## Rejected
