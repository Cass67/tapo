from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class Reading:
    timestamp: str
    name: str
    ip: str
    power_w: float | None
    voltage_v: float | None
    current_a: float | None
    total_energy_kwh: float | None
    raw: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_reading(name: str, ip: str, raw: dict[str, Any]) -> Reading:
    return Reading(
        timestamp=datetime.now(UTC).isoformat(),
        name=name,
        ip=ip,
        power_w=_metric(
            raw, "current_power", "current_power_w", "power", "power_mw", scale_for_milli=True
        ),
        voltage_v=_metric(raw, "voltage", "voltage_mv", scale_for_milli=True),
        current_a=_metric(raw, "current", "current_ma", scale_for_milli=True),
        total_energy_kwh=_metric(
            raw, "today_energy", "energy", "total_energy", "total_energy_wh", scale_for_wh=True
        ),
        raw=raw,
    )


def _metric(
    raw: dict[str, Any],
    *names: str,
    scale_for_milli: bool = False,
    scale_for_wh: bool = False,
) -> float | None:
    for name in names:
        value = raw.get(name)
        if value is None:
            continue
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if scale_for_milli and name.endswith(("_mw", "_mv", "_ma")):
            return number / 1000
        if scale_for_wh and name.endswith("_wh"):
            return number / 1000
        return number
    return None
