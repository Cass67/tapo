from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

from tapo_probe.config import DeviceConfig
from tapo_probe.readings import Reading, normalize_reading


class TapoBackend(Protocol):
    async def get_reading(
        self, username: str, password: str, device: DeviceConfig
    ) -> dict[str, Any]: ...


class TapoAuthError(RuntimeError):
    pass


class TapoLibraryBackend:
    def __init__(self, client_factory: Callable[..., Any] | None = None) -> None:
        self._client_factory = client_factory

    async def get_reading(
        self, username: str, password: str, device: DeviceConfig
    ) -> dict[str, Any]:
        try:
            from tapo import ApiClient

            client_factory = self._client_factory or ApiClient
            client = client_factory(username, password, timeout_s=10)
            plug = await client.p110(device.ip)
            info = await plug.get_device_info_json()
            usage = await plug.get_energy_usage()
            power = await plug.get_current_power()
        except Exception as exc:
            message = str(exc)
            if "Third-Party Compatibility" in message or "FORBIDDEN" in message:
                raise TapoAuthError(
                    "Tapo rejected local access. In the Tapo app, enable Me > Third-Party Services > "
                    "Third-Party Compatibility, then try again."
                ) from exc
            raise

        return _to_mapping(info) | _to_mapping(usage) | _to_mapping(power)


PlugP100Backend = TapoLibraryBackend


async def collect_readings_async(
    username: str,
    password: str,
    devices: tuple[DeviceConfig, ...],
    backend: TapoBackend | None = None,
    attempts: int = 3,
    sleep: Callable[[float], None] = time.sleep,
) -> tuple[list[Reading], list[str]]:
    client = backend or TapoLibraryBackend()
    readings: list[Reading] = []
    errors: list[str] = []
    for device in devices:
        last_error: Exception | None = None
        for attempt in range(1, attempts + 1):
            try:
                raw = await client.get_reading(username, password, device)
                break
            except Exception as exc:  # noqa: BLE001 - report per-device failures in CLI output.
                last_error = exc
                if attempt < attempts:
                    sleep(attempt)
        else:
            msg = str(last_error) if last_error else "unknown error"
            errors.append(f"{device.name} ({device.ip}): {msg}")
            continue
        readings.append(normalize_reading(device.name, device.ip, raw))
    return readings, errors


def collect_readings(
    username: str,
    password: str,
    devices: tuple[DeviceConfig, ...],
    backend: TapoBackend | None = None,
    attempts: int = 3,
    sleep: Callable[[float], None] = time.sleep,
    runner: Callable[
        [Awaitable[tuple[list[Reading], list[str]]]], tuple[list[Reading], list[str]]
    ] = asyncio.run,
) -> tuple[list[Reading], list[str]]:
    return runner(
        collect_readings_async(username, password, devices, backend, attempts=attempts, sleep=sleep)
    )


async def discover_devices_async(timeout: int = 5) -> list[dict[str, str]]:
    from plugp100.discovery.tapo_discovery import TapoDiscovery

    devices = await TapoDiscovery.scan(timeout=timeout)
    return [
        {
            "ip": str(device.ip),
            "model": str(device.device_model),
            "type": str(device.device_type),
            "mac": str(device.mac),
        }
        for device in devices
    ]


def discover_devices(timeout: int = 5) -> list[dict[str, str]]:
    return asyncio.run(discover_devices_async(timeout=timeout))


def _to_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "to_dict"):
        mapped = value.to_dict()
        if isinstance(mapped, dict):
            return mapped
    if hasattr(value, "model_dump"):
        mapped = value.model_dump()
        if isinstance(mapped, dict):
            return mapped
    if hasattr(value, "__dict__"):
        return dict(value.__dict__)
    return {}
