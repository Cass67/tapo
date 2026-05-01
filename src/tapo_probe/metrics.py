from __future__ import annotations

import base64
import binascii
from collections.abc import Mapping

from tapo_probe.readings import Reading


def format_metrics(
    readings: list[Reading],
    errors: Mapping[tuple[str, str], str],
    hostname_overrides: Mapping[str, str] | None = None,
) -> str:
    overrides = hostname_overrides or {}
    lines = [
        "# HELP tapo_plug_power_watts Current plug power draw in watts.",
        "# TYPE tapo_plug_power_watts gauge",
        "# HELP tapo_plug_today_energy_wh Energy used today in watt-hours.",
        "# TYPE tapo_plug_today_energy_wh gauge",
        "# HELP tapo_plug_month_energy_wh Energy used this month in watt-hours.",
        "# TYPE tapo_plug_month_energy_wh gauge",
        "# HELP tapo_plug_today_runtime_seconds Runtime today in seconds.",
        "# TYPE tapo_plug_today_runtime_seconds gauge",
        "# HELP tapo_plug_month_runtime_seconds Runtime this month in seconds.",
        "# TYPE tapo_plug_month_runtime_seconds gauge",
        "# HELP tapo_plug_rssi_dbm Wi-Fi RSSI in dBm.",
        "# TYPE tapo_plug_rssi_dbm gauge",
        "# HELP tapo_plug_up Whether the plug was read successfully.",
        "# TYPE tapo_plug_up gauge",
    ]

    seen = set()
    for reading in readings:
        labels = _labels(reading.name, reading.ip, _hostname(reading, overrides))
        seen.add((reading.name, reading.ip))
        _append_metric(lines, "tapo_plug_power_watts", labels, reading.power_w)
        _append_metric(lines, "tapo_plug_today_energy_wh", labels, _raw_number(reading, "today_energy"))
        _append_metric(lines, "tapo_plug_month_energy_wh", labels, _raw_number(reading, "month_energy"))
        _append_metric(lines, "tapo_plug_today_runtime_seconds", labels, _raw_number(reading, "today_runtime"))
        _append_metric(lines, "tapo_plug_month_runtime_seconds", labels, _raw_number(reading, "month_runtime"))
        _append_metric(lines, "tapo_plug_rssi_dbm", labels, _raw_number(reading, "rssi"))
        lines.append(f"tapo_plug_up{labels} 1")
        _append_compatibility_metrics(lines, labels, reading)

    for name, ip in errors:
        if (name, ip) in seen:
            continue
        hostname = overrides.get(ip, name)
        lines.append(f"tapo_plug_up{_labels(name, ip, hostname)} 0")

    return "\n".join(lines) + "\n"


def _hostname(reading: Reading, overrides: Mapping[str, str]) -> str:
    if reading.ip in overrides:
        return overrides[reading.ip]
    nickname = reading.raw.get("nickname")
    return _decode_tapo_text(str(nickname)) if nickname else reading.name


def _labels(name: str, ip: str, hostname: str) -> str:
    parts = {
        "hostname": hostname,
        "ip": ip,
        "name": name,
        "nickname": hostname,
        "alias": hostname,
    }
    return "{" + ",".join(f'{key}="{_escape_label(value)}"' for key, value in parts.items()) + "}"


def _append_metric(lines: list[str], metric: str, labels: str, value: float | int | None) -> None:
    if value is not None:
        lines.append(f"{metric}{labels} {value:g}")


def _append_compatibility_metrics(lines: list[str], labels: str, reading: Reading) -> None:
    power_mw = reading.power_w * 1000 if reading.power_w is not None else None
    _append_metric(lines, "tapo_energyUsage_currentPower", labels, power_mw)
    _append_metric(lines, "tapo_energyUsage_todayEnergy", labels, _raw_number(reading, "today_energy"))
    _append_metric(lines, "tapo_energyUsage_monthEnergy", labels, _raw_number(reading, "month_energy"))
    _append_metric(lines, "tapo_energyUsage_todayRuntime", labels, _raw_number(reading, "today_runtime"))
    _append_metric(lines, "tapo_energyUsage_monthRuntime", labels, _raw_number(reading, "month_runtime"))
    _append_metric(lines, "tapo_deviceInfo_rssi", labels, _raw_number(reading, "rssi"))
    lines.append(f"tapo_deviceInfo_device_on{labels} 1")


def _raw_number(reading: Reading, key: str) -> float | None:
    value = reading.raw.get(key)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _escape_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


def _decode_tapo_text(value: str) -> str:
    try:
        decoded = base64.b64decode(value, validate=True).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError):
        return value
    return decoded or value
