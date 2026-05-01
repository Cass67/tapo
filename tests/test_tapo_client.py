from __future__ import annotations

from tapo_probe.config import DeviceConfig
from tapo_probe.tapo_client import TapoLibraryBackend, collect_readings


class FakeBackend:
    async def get_reading(self, username, password, _device):  # nosec B101 B105
        assert username == "user@example.com"  # nosec B101
        assert password == "secret"  # nosec B101 B105
        return {"current_power": 12.5}


class FailingBackend:
    async def get_reading(self, _username, _password, _device):
        raise RuntimeError("offline")  # noqa: E501


def test_collect_readings_with_fake_backend():
    readings, errors = collect_readings(
        "user@example.com",
        "secret",
        (DeviceConfig(name="desk", ip="192.168.1.50"),),
        backend=FakeBackend(),
    )

    assert errors == []  # nosec B101
    assert readings[0].name == "desk"  # nosec B101
    assert readings[0].power_w == 12.5  # nosec B101


def test_collect_readings_reports_device_errors():
    readings, errors = collect_readings(
        "user@example.com",
        "secret",
        (DeviceConfig(name="desk", ip="192.168.1.50"),),
        backend=FailingBackend(),
    )

    assert readings == []  # nosec B101
    assert errors == ["desk (192.168.1.50): offline"]  # nosec B101


def test_collect_readings_retries_transient_device_errors():
    class FlakyBackend:
        def __init__(self):
            self.calls = 0

        async def get_reading(self, _username, _password, _device):
            self.calls += 1
            if self.calls == 1:
                raise ConnectionRefusedError("connection refused")
            return {"current_power": 12.5}

    backend = FlakyBackend()
    readings, errors = collect_readings(
        "user@example.com",
        "secret",
        (DeviceConfig(name="desk", ip="192.168.1.50"),),
        backend=backend,
        sleep=lambda _seconds: None,
    )

    assert errors == []  # nosec B101
    assert readings[0].power_w == 12.5  # nosec B101
    assert backend.calls == 2  # nosec B101


def test_tapo_backend_reports_third_party_compatibility_errors():
    class FakeClient:
        def __init__(self, username, password, **_kwargs):
            pass

        async def p110(self, _ip):
            raise Exception(
                'Tapo(Unauthorized { kind: "FORBIDDEN", description: "Make sure Third-Party Compatibility is turned on" })'
            )

    backend = TapoLibraryBackend(client_factory=FakeClient)
    readings, errors = collect_readings(
        "user@example.com",
        "secret",
        (DeviceConfig(name="desk", ip="192.168.1.50"),),
        backend=backend,
    )

    assert readings == []  # nosec B101
    assert errors == [  # nosec B101
        "desk (192.168.1.50): Tapo rejected local access. In the Tapo app, enable Me > Third-Party Services > Third-Party Compatibility, then try again."
    ]
