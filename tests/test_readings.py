from __future__ import annotations

from tapo_probe.readings import normalize_reading


def test_normalizes_common_energy_fields():
    reading = normalize_reading(
        "desk",
        "192.168.1.50",
        {"current_power": 12.5, "voltage": 240, "current": 0.052, "today_energy": 0.4},
    )

    assert reading.name == "desk"  # nosec B101
    assert reading.ip == "192.168.1.50"  # nosec B101
    assert reading.power_w == 12.5  # nosec B101
    assert reading.voltage_v == 240  # nosec B101
    assert reading.current_a == 0.052  # nosec B101
    assert reading.total_energy_kwh == 0.4  # nosec B101


def test_normalizes_milli_and_wh_fields():
    reading = normalize_reading(
        "desk",
        "192.168.1.50",
        {"power_mw": 12500, "voltage_mv": 240000, "current_ma": 52, "total_energy_wh": 400},
    )

    assert reading.power_w == 12.5  # nosec B101
    assert reading.voltage_v == 240  # nosec B101
    assert reading.current_a == 0.052  # nosec B101
    assert reading.total_energy_kwh == 0.4  # nosec B101
    assert reading.raw["power_mw"] == 12500  # nosec B101
