from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path


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


def load_config(config_path: str | Path | None = None, env_path: str | Path = ".env") -> ProbeConfig:
    dotenv = _load_dotenv(env_path)
    username = os.environ.get("TAPO_USERNAME") or dotenv.get("TAPO_USERNAME")
    password = os.environ.get("TAPO_PASSWORD") or dotenv.get("TAPO_PASSWORD")
    devices: list[DeviceConfig] = []

    if config_path is not None:
        path = Path(config_path)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ConfigError(f"{path} is not valid JSON: {exc.msg} at line {exc.lineno}, column {exc.colno}") from exc
        if not isinstance(data, dict):
            raise ConfigError(f"{path} must contain a JSON object")
        for item in data.get("devices", []):
            devices.append(
                DeviceConfig(
                    name=str(item["name"]),
                    ip=str(item["ip"]),
                    hostname=str(item["hostname"]) if item.get("hostname") else None,
                )
            )

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


def _clean_env_value(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value
