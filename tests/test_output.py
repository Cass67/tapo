from __future__ import annotations

import json

from tapo_probe.output import append_jsonl
from tapo_probe.readings import normalize_reading


def test_appends_readings_as_jsonl(tmp_path):
    output = tmp_path / "readings.jsonl"
    reading = normalize_reading("desk", "192.168.1.50", {"current_power": 12.5})

    append_jsonl(output, [reading])
    append_jsonl(output, [reading])

    lines = output.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2  # nosec B101
    assert json.loads(lines[0])["name"] == "desk"  # nosec B101
    assert json.loads(lines[0])["power_w"] == 12.5  # nosec B101
