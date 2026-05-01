from __future__ import annotations

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
