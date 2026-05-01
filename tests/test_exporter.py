from __future__ import annotations

from tapo_probe.config import DeviceConfig, ProbeConfig
from tapo_probe.exporter import ExporterState
from tapo_probe.readings import normalize_reading


def test_exporter_state_polls_and_formats_metrics():
    config = ProbeConfig(
        username="user@example.com",
        password="secret",
        devices=(DeviceConfig(name="desk", ip="192.168.1.50", hostname="desk-host"),),
        missing=(),
    )

    def collect(username, password, devices):
        return [normalize_reading("desk", "192.168.1.50", {"current_power": 12.5})], []

    state = ExporterState(config, collect_readings=collect)

    state.poll_once()

    assert 'tapo_plug_power_watts{hostname="desk-host",ip="192.168.1.50",name="desk",nickname="desk-host",alias="desk-host"} 12.5' in state.metrics_text()


def test_exporter_state_formats_device_errors():
    config = ProbeConfig(
        username="user@example.com",
        password="secret",
        devices=(DeviceConfig(name="desk", ip="192.168.1.50", hostname="desk-host"),),
        missing=(),
    )

    def collect(username, password, devices):
        return [], ["desk (192.168.1.50): offline"]

    state = ExporterState(config, collect_readings=collect)

    state.poll_once()

    assert 'tapo_plug_up{hostname="desk-host",ip="192.168.1.50",name="desk",nickname="desk-host",alias="desk-host"} 0' in state.metrics_text()
