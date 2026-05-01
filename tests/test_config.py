from __future__ import annotations

import json

import pytest
from tapo_probe.config import ConfigError, load_config


def test_missing_config_records_missing_values(monkeypatch, tmp_path):
    monkeypatch.delenv("TAPO_USERNAME", raising=False)
    monkeypatch.delenv("TAPO_PASSWORD", raising=False)

    config = load_config(env_path=tmp_path / ".env")

    assert config.devices == ()  # nosec B101
    assert config.missing == ("TAPO_USERNAME", "TAPO_PASSWORD", "devices")  # nosec B101


def test_loads_credentials_from_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("TAPO_USERNAME", "user@example.com")
    monkeypatch.setenv("TAPO_PASSWORD", "secret")
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"devices": []}), encoding="utf-8")

    config = load_config(config_path)

    assert config.username == "user@example.com"  # nosec B101
    assert config.password == "secret"  # nosec B101 B105
    assert config.missing == ("devices",)  # nosec B101


def test_loads_credentials_from_dotenv(monkeypatch, tmp_path):
    monkeypatch.delenv("TAPO_USERNAME", raising=False)
    monkeypatch.delenv("TAPO_PASSWORD", raising=False)
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text(
        "TAPO_USERNAME=user@example.com\nTAPO_PASSWORD=secret\n", encoding="utf-8"
    )

    config = load_config(env_path=dotenv_path)

    assert config.username == "user@example.com"  # nosec B101
    assert config.password == "secret"  # nosec B101 B105
    assert config.missing == ("devices",)  # nosec B101


def test_environment_overrides_dotenv(monkeypatch, tmp_path):
    monkeypatch.setenv("TAPO_USERNAME", "env-user@example.com")
    monkeypatch.setenv("TAPO_PASSWORD", "env-secret")
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text(
        "TAPO_USERNAME=file-user@example.com\nTAPO_PASSWORD=file-secret\n", encoding="utf-8"
    )

    config = load_config(env_path=dotenv_path)

    assert config.username == "env-user@example.com"  # nosec B101
    assert config.password == "env-secret"  # nosec B101 B105


def test_loads_devices_from_json(monkeypatch, tmp_path):
    monkeypatch.setenv("TAPO_USERNAME", "user@example.com")
    monkeypatch.setenv("TAPO_PASSWORD", "secret")
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps({"devices": [{"name": "desk", "ip": "192.168.1.50"}]}), encoding="utf-8"
    )

    config = load_config(config_path)

    assert config.devices[0].name == "desk"  # nosec B101
    assert config.devices[0].ip == "192.168.1.50"  # nosec B101
    assert config.missing == ()  # nosec B101


def test_loads_optional_device_hostname(monkeypatch, tmp_path):
    monkeypatch.setenv("TAPO_USERNAME", "user@example.com")
    monkeypatch.setenv("TAPO_PASSWORD", "secret")
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps({"devices": [{"name": "desk", "hostname": "desk-plug", "ip": "192.168.1.50"}]}),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.devices[0].hostname == "desk-plug"  # nosec B101


def test_invalid_json_raises_clear_config_error(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text("export TAPO_USERNAME='user@example.com'", encoding="utf-8")

    with pytest.raises(ConfigError, match="is not valid JSON"):
        load_config(config_path)
