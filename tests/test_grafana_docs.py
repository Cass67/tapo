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
    assert "Dashboard URLs like https://example.grafana.net/d/" in text  # nosec B101
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

    assert dashboard["title"] == "Tapo smart plug monitoring"  # nosec B101
    assert len(dashboard["panels"]) >= 12  # nosec B101
    assert "tapo_energyUsage_currentPower" in text  # nosec B101
    assert "tapo_energyUsage_todayEnergy" in text  # nosec B101
    assert "tapo_deviceInfo_rssi" in text  # nosec B101
    assert "tapo_plug_overheat" in text  # nosec B101
    assert "Estimated Cost" in text  # nosec B101
    assert "Plug Firmware" in text  # nosec B101


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


def test_readme_embeds_dashboard_preview_svg():
    readme = Path("README.md").read_text(encoding="utf-8")
    svg = Path("docs/assets/tapo-p110-dashboard-preview.svg").read_text(encoding="utf-8")

    assert "docs/assets/tapo-p110-dashboard-preview.svg" in readme  # nosec B101
    assert "Tapo smart plug monitoring" in svg  # nosec B101
    assert "Power Consumption" in svg  # nosec B101
    assert "Energy Usage" in svg  # nosec B101
    assert "Estimated Cost" in svg  # nosec B101
    assert "Plug Firmware" in svg  # nosec B101


def test_installer_manages_alloy_remote_write_service():
    readme = Path("README.md").read_text(encoding="utf-8")
    installer = Path("scripts/install-service.sh").read_text(encoding="utf-8")

    assert "com.tapo-probe.alloy" in installer  # nosec B101
    assert "alloy-run.sh" in installer  # nosec B101
    assert "alloy.config" in installer  # nosec B101
    assert "alloy run" in installer  # nosec B101
    assert "brew install grafana/grafana/alloy" in installer  # nosec B101
    assert "installer manages both the exporter and Grafana Alloy" in readme  # nosec B101


def test_linux_installer_manages_alloy_user_service():
    readme = Path("README.md").read_text(encoding="utf-8")
    installer = Path("scripts/install-service.sh").read_text(encoding="utf-8")

    assert "tapo-probe-alloy.service" in installer  # nosec B101
    assert 'systemctl --user enable --now "tapo-probe-alloy.service"' in installer  # nosec B101
    assert "systemctl --user status tapo-probe-alloy.service" in readme  # nosec B101
    assert "journalctl --user -u tapo-probe-alloy.service -f" in readme  # nosec B101


def test_installer_bootstraps_pip_in_virtualenv():
    installer = Path("scripts/install-service.sh").read_text(encoding="utf-8")

    assert "ensure_venv_pip" in installer  # nosec B101
    assert "-m ensurepip --upgrade" in installer  # nosec B101
    assert "python3-venv" in installer  # nosec B101


def test_local_compose_stack_documents_long_retention():
    readme = Path("README.md").read_text(encoding="utf-8")
    compose = Path("compose.yaml").read_text(encoding="utf-8")
    prometheus = Path("grafana/prometheus.local.yml").read_text(encoding="utf-8")
    datasource = Path("grafana/provisioning/datasources/prometheus.yml").read_text(encoding="utf-8")

    assert "docker compose up -d" in readme  # nosec B101
    assert "http://cb1.lan:3000" in readme  # nosec B101
    assert "--storage.tsdb.retention.time=2y" in compose  # nosec B101
    assert "--web.listen-address=127.0.0.1:9090" in compose  # nosec B101
    assert "network_mode: host" in compose  # nosec B101
    assert "127.0.0.1:9108" in prometheus  # nosec B101
    assert "http://127.0.0.1:9090" in datasource  # nosec B101


def test_local_dashboard_uses_provisioned_datasource_uid():
    dashboard = Path("grafana/tapo-p110-dashboard.sample.json").read_text(encoding="utf-8")
    datasource = Path("grafana/provisioning/datasources/prometheus.yml").read_text(encoding="utf-8")

    assert "deleteDatasources:" in datasource  # nosec B101
    assert "uid: prometheus" in datasource  # nosec B101
    assert '"uid": "prometheus"' in dashboard  # nosec B101
    assert "${DS_PROMETHEUS}" not in dashboard  # nosec B101
