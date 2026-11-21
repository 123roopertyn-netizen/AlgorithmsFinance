"""Exercise the real launcher and JSON/gzip reader against independent expectations."""
import gzip
import json
import subprocess
import sys

import pytest

import contract


@pytest.mark.parametrize("compressed", [False, True], ids=["jsonl", "jsonl-gzip"])
def test_replay_command_a(tmp_path, compressed):
    events = (contract.SUPPLIED / "worked_example.jsonl").read_text(encoding="utf-8")
    path = tmp_path / ("worked.jsonl.gz" if compressed else "worked.jsonl")
    opener = gzip.open if compressed else open
    with opener(path, "wt", encoding="utf-8") as stream:
        stream.write(events)
    command = [sys.executable, "run.py", "lob.replay", str(path), "--version", "A"]
    result = subprocess.run(command, cwd=contract.ROOT, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    got = [json.loads(line) for line in result.stdout.splitlines()]
    source = [json.loads(line) for line in events.splitlines()]
    expected = json.loads((contract.SUPPLIED / "worked_expected.json").read_text(encoding="utf-8"))
    want = [{"event_id": e["event_id"], "order_id": e["order_id"], "status": "resting",
             "unfilled_qty_units": e["qty_units"], "fills": []} for e in source[:5]]
    want.append(expected["market_sell_result"])
    assert got == want


def test_replay_keeps_rejections_in_input_order():
    command = [sys.executable, "run.py", "lob.replay",
               str(contract.OWN / "invalid_fields.jsonl"), "--version", "A"]
    result = subprocess.run(command, cwd=contract.ROOT, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    got = [json.loads(line) for line in result.stdout.splitlines()]
    expected = json.loads((contract.OWN / "invalid_fields.expected.json").read_text(encoding="utf-8"))
    assert got == expected["results"]
