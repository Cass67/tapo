from __future__ import annotations

from tapo_probe.metrics import format_metrics
from tapo_probe.readings import normalize_reading


def test_formats_prometheus_metrics_with_hostname():
    reading = normalize_reading(
        "desk",
        "192.168.1.50",
        {
            "current_power": 12.5,
            "today_energy": 400,
            "month_energy": 1200,
            "rssi": -55,
            "nickname": "Desk Plug",
            "on_time": 3600,
            "signal_level": 2,
            "overheat_status": "Normal",
            "overcurrent_status": "OvercurrentStatus.Normal",
            "power_protection_status": "PowerProtectionStatus.Normal",
            "fw_ver": "1.4.6 Build 260309",
        },
    )

    text = format_metrics([reading], {}, hostname_overrides={"192.168.1.50": "desk-host"})

    assert (  # nosec B101
        'tapo_plug_power_watts{hostname="desk-host",ip="192.168.1.50",name="desk",nickname="desk-host",alias="desk-host"} 12.5'
        in text
    )
    assert (  # nosec B101
        'tapo_plug_today_energy_wh{hostname="desk-host",ip="192.168.1.50",name="desk",nickname="desk-host",alias="desk-host"} 400'
        in text
    )
    assert (  # nosec B101
        'tapo_plug_month_energy_wh{hostname="desk-host",ip="192.168.1.50",name="desk",nickname="desk-host",alias="desk-host"} 1200'
        in text
    )
    assert (  # nosec B101
        'tapo_plug_rssi_dbm{hostname="desk-host",ip="192.168.1.50",name="desk",nickname="desk-host",alias="desk-host"} -55'
        in text
    )
    assert (  # nosec B101
        'tapo_plug_up{hostname="desk-host",ip="192.168.1.50",name="desk",nickname="desk-host",alias="desk-host"} 1'
        in text
    )
    assert (  # nosec B101
        'tapo_plug_on_time_seconds{hostname="desk-host",ip="192.168.1.50",name="desk",nickname="desk-host",alias="desk-host"} 3600'
        in text
    )
    assert (  # nosec B101
        'tapo_plug_signal_level{hostname="desk-host",ip="192.168.1.50",name="desk",nickname="desk-host",alias="desk-host"} 2'
        in text
    )
    assert (  # nosec B101
        'tapo_plug_overheat{hostname="desk-host",ip="192.168.1.50",name="desk",nickname="desk-host",alias="desk-host"} 0'
        in text
    )
    assert (  # nosec B101
        'tapo_plug_overcurrent{hostname="desk-host",ip="192.168.1.50",name="desk",nickname="desk-host",alias="desk-host"} 0'
        in text
    )
    assert (  # nosec B101
        'tapo_plug_power_protection_triggered{hostname="desk-host",ip="192.168.1.50",name="desk",nickname="desk-host",alias="desk-host"} 0'
        in text
    )
    assert (  # nosec B101
        'tapo_plug_info{hostname="desk-host",ip="192.168.1.50",name="desk",nickname="desk-host",alias="desk-host",fw_ver="1.4.6 Build 260309"} 1'
        in text
    )


def test_formats_failed_device_up_metric():
    text = format_metrics(
        [], {("desk", "192.168.1.50"): "offline"}, hostname_overrides={"192.168.1.50": "desk-host"}
    )

    assert (  # nosec B101
        'tapo_plug_up{hostname="desk-host",ip="192.168.1.50",name="desk",nickname="desk-host",alias="desk-host"} 0'
        in text
    )


def test_escapes_prometheus_labels():
    reading = normalize_reading('desk"plug', "192.168.1.50", {"current_power": 12.5})

    text = format_metrics([reading], {})

    assert 'name="desk\\"plug"' in text  # nosec B101


def test_decodes_base64_tapo_nickname_for_hostname():
    reading = normalize_reading(
        "desk", "192.168.1.50", {"current_power": 12.5, "nickname": "SG90VHVi"}
    )

    text = format_metrics([reading], {})

    assert 'hostname="HotTub"' in text  # nosec B101


def test_formats_dashboard_compatibility_metrics():
    reading = normalize_reading(
        "desk",
        "192.168.1.50",
        {
            "current_power": 12.5,
            "today_energy": 400,
            "month_energy": 1200,
            "today_runtime": 60,
            "month_runtime": 3600,
            "rssi": -55,
        },
    )

    text = format_metrics([reading], {})

    assert (  # nosec B101
        'tapo_energyUsage_currentPower{hostname="desk",ip="192.168.1.50",name="desk",nickname="desk",alias="desk"} 12500'
        in text
    )
    assert (  # nosec B101
        'tapo_energyUsage_todayEnergy{hostname="desk",ip="192.168.1.50",name="desk",nickname="desk",alias="desk"} 400'
        in text
    )
    assert (  # nosec B101
        'tapo_energyUsage_monthEnergy{hostname="desk",ip="192.168.1.50",name="desk",nickname="desk",alias="desk"} 1200'
        in text
    )
    assert (  # nosec B101
        'tapo_energyUsage_todayRuntime{hostname="desk",ip="192.168.1.50",name="desk",nickname="desk",alias="desk"} 60'
        in text
    )
    assert (  # nosec B101
        'tapo_energyUsage_monthRuntime{hostname="desk",ip="192.168.1.50",name="desk",nickname="desk",alias="desk"} 3600'
        in text
    )
    assert (  # nosec B101
        'tapo_deviceInfo_rssi{hostname="desk",ip="192.168.1.50",name="desk",nickname="desk",alias="desk"} -55'
        in text
    )
    assert (  # nosec B101
        'tapo_deviceInfo_device_on{hostname="desk",ip="192.168.1.50",name="desk",nickname="desk",alias="desk"} 1'
        in text
    )


def test_status_flag_does_not_treat_abnormal_as_normal():
    reading = normalize_reading(
        "desk", "192.168.1.50", {"current_power": 12.5, "overcurrent_status": "abnormal"}
    )

    text = format_metrics([reading], {})

    assert (  # nosec B101
        'tapo_plug_overcurrent{hostname="desk",ip="192.168.1.50",name="desk",nickname="desk",alias="desk"} 1'
        in text
    )
