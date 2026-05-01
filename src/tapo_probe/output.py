from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from tapo_probe.readings import Reading


def append_jsonl(path: str | Path, readings: Iterable[Reading]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("a", encoding="utf-8") as file:
        for reading in readings:
            file.write(json.dumps(reading.to_dict(), separators=(",", ":")))
            file.write("\n")
