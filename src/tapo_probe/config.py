from __future__ import annotations

import json
import os
from dataclasses import dataclass
from ipaddress import ip_address
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DeviceConfig:
    name: str
    ip: str
    hostname: str | None = None


@dataclass(frozen=True)
class ProbeConfig:
    username: str | None
    password: str | None
    devices: tuple[DeviceConfig, ...]
    missing: tuple[str, ...]


class ConfigError(ValueError):
    """Raised when the local config file cannot be parsed."""


def load_config(
    config_path: str | Path | None = None, env_path: str | Path = ".env"
) -> ProbeConfig:
    dotenv = _load_dotenv(env_path)
    username = os.environ.get("TAPO_USERNAME") or dotenv.get("TAPO_USERNAME")
    password = os.environ.get("TAPO_PASSWORD") or dotenv.get("TAPO_PASSWORD")
    devices: list[DeviceConfig] = []

    if config_path is not None:
        path = Path(config_path)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ConfigError(
                f"{path} is not valid JSON: {exc.msg} at line {exc.lineno}, column {exc.colno}"
            ) from exc
        if not isinstance(data, dict):
            raise ConfigError(f"{path} must contain a JSON object")
        devices = _load_devices(data.get("devices", []))

    missing = []
    if not username:
        missing.append("TAPO_USERNAME")
    if not password:
        missing.append("TAPO_PASSWORD")
    if not devices:
        missing.append("devices")

    return ProbeConfig(
        username=username,
        password=password,
        devices=tuple(devices),
        missing=tuple(missing),
    )


def _load_dotenv(env_path: str | Path) -> dict[str, str]:
    path = Path(env_path)
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = _clean_env_value(value.strip())
    return values


def _load_devices(value: Any) -> list[DeviceConfig]:
    if not isinstance(value, list):
        raise ConfigError("devices must be a list")

    devices = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ConfigError(f"devices[{index}] must be an object")
        name = _required_text(item, "name", index)
        ip = _required_text(item, "ip", index)
        try:
            ip_address(ip)
        except ValueError as exc:
            raise ConfigError(f"devices[{index}].ip must be a valid IP address") from exc
        hostname = item.get("hostname")
        devices.append(
            DeviceConfig(
                name=name,
                ip=ip,
                hostname=str(hostname).strip() if hostname else None,
            )
        )
    return devices


def _required_text(item: dict[str, Any], key: str, index: int) -> str:
    value = item.get(key)
    if value is None or not str(value).strip():
        raise ConfigError(f"devices[{index}] must include {key}")
    return str(value).strip()


def _clean_env_value(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value
