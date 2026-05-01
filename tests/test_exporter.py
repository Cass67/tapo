from __future__ import annotations

import signal

from tapo_probe.config import DeviceConfig, ProbeConfig
from tapo_probe import exporter
from tapo_probe.exporter import ExporterState
from tapo_probe.readings import normalize_reading


def test_exporter_state_polls_and_formats_metrics():
    config = ProbeConfig(
        username="user@example.com",
        password="secret",  # nosec B106
        devices=(DeviceConfig(name="desk", ip="192.168.1.50", hostname="desk-host"),),
        missing=(),
    )

    def collect(username, password, devices):
        return [normalize_reading("desk", "192.168.1.50", {"current_power": 12.5})], []

    state = ExporterState(config, collect_readings=collect)

    state.poll_once()

    assert (  # nosec B101
        'tapo_plug_power_watts{hostname="desk-host",ip="192.168.1.50",name="desk",nickname="desk-host",alias="desk-host"} 12.5'
        in state.metrics_text()
    )


def test_exporter_state_formats_device_errors():
    config = ProbeConfig(
        username="user@example.com",
        password="secret",  # nosec B106
        devices=(DeviceConfig(name="desk", ip="192.168.1.50", hostname="desk-host"),),
        missing=(),
    )

    def collect(username, password, devices):
        return [], ["desk (192.168.1.50): offline"]

    state = ExporterState(config, collect_readings=collect)

    state.poll_once()

    assert (  # nosec B101
        'tapo_plug_up{hostname="desk-host",ip="192.168.1.50",name="desk",nickname="desk-host",alias="desk-host"} 0'
        in state.metrics_text()
    )


def test_serve_metrics_registers_signal_shutdown(monkeypatch):
    registered = {}

    class FakeServer:
        def __init__(self, address, handler):
            self.address = address
            self.handler = handler
            self.shutdown_called = False
            self.closed = False

        def serve_forever(self):
            for handler in registered.values():
                handler(signal.SIGTERM, None)

        def shutdown(self):
            self.shutdown_called = True

        def server_close(self):
            self.closed = True

    servers = []

    def fake_server(address, handler):
        server = FakeServer(address, handler)
        servers.append(server)
        return server

    def fake_signal(signum, handler):
        registered[signum] = handler

    config = ProbeConfig(username=None, password=None, devices=(), missing=())
    monkeypatch.setattr(exporter, "ThreadingHTTPServer", fake_server)
    monkeypatch.setattr(exporter.signal, "signal", fake_signal)

    exporter.serve_metrics(config, port=9109, interval=3600)

    assert servers[0].address == ("127.0.0.1", 9109)  # nosec B101
    assert signal.SIGINT in registered  # nosec B101
    assert signal.SIGTERM in registered  # nosec B101
    assert servers[0].shutdown_called  # nosec B101
    assert servers[0].closed  # nosec B101
