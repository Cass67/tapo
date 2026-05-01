from __future__ import annotations

import json
from pathlib import Path


def test_alloy_example_uses_grafana_token_env():
    text = Path("grafana/alloy.config.example").read_text(encoding="utf-8")

    assert 'password = sys.env("GRAFANA_METRICS_WRITE")' in text  # nosec B101
    assert "GRAFANA_CLOUD_API_KEY" not in text  # nosec B101


def test_readme_documents_remote_write_not_dashboard_url():
    text = Path("README.md").read_text(encoding="utf-8")

    assert "GRAFANA_METRICS_WRITE" in text  # nosec B101
    assert "GRAFANA_METRICS_READ" in text  # nosec B101
    assert "remote_write endpoint" in text  # nosec B101
    assert "Dashboard URLs like https://getcass.grafana.net/d/" in text  # nosec B101
    assert "Grafana Cloud Metrics publish/write permission" in text  # nosec B101


def test_readme_documents_user_service_installer():
    text = Path("README.md").read_text(encoding="utf-8")

    assert "scripts/install-service.sh" in text  # nosec B101
    assert "systemctl --user" in text  # nosec B101
    assert "launchctl" in text  # nosec B101
    assert "~/Library/LaunchAgents/com.tapo-probe.exporter.plist" in text  # nosec B101
    assert "~/.config/systemd/user/tapo-probe.service" in text  # nosec B101


def test_sample_dashboard_uses_exported_metrics():
    dashboard = json.loads(
        Path("grafana/tapo-p110-dashboard.sample.json").read_text(encoding="utf-8")
    )
    text = json.dumps(dashboard)

    assert dashboard["title"] == "Tapo P110 Energy"  # nosec B101
    assert "tapo_energyUsage_currentPower" in text  # nosec B101
    assert "tapo_energyUsage_todayEnergy" in text  # nosec B101
    assert "tapo_deviceInfo_rssi" in text  # nosec B101
    assert "tapo_plug_overheat" in text  # nosec B101


def test_readme_documents_container_usage():
    text = Path("README.md").read_text(encoding="utf-8")

    assert "Containerfile" in text  # nosec B101
    assert "docker build" in text  # nosec B101
    assert "podman build" in text  # nosec B101
    assert "/config/tapo-config.json" in text  # nosec B101
    assert "TAPO_USERNAME" in text  # nosec B101
    assert "-p 9108:9108" in text  # nosec B101


def test_containerfile_runs_exporter_by_default():
    text = Path("Containerfile").read_text(encoding="utf-8")

    assert "python:3.12-slim" in text  # nosec B101
    assert "EXPOSE 9108" in text  # nosec B101
    assert "tapo-probe" in text  # nosec B101
    assert "/config/tapo-config.json" in text  # nosec B101
