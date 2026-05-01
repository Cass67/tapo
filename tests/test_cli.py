from __future__ import annotations

import json

from tapo_probe import cli
from tapo_probe.readings import normalize_reading


def test_cli_prints_discovery_guidance_when_no_devices(monkeypatch, tmp_path, capsys):
    monkeypatch.delenv("TAPO_USERNAME", raising=False)
    monkeypatch.delenv("TAPO_PASSWORD", raising=False)
    monkeypatch.chdir(tmp_path)

    result = cli.main([])

    captured = capsys.readouterr()
    assert result == 2  # nosec B101
    assert "No Tapo devices are configured" in captured.err  # nosec B101
    assert "Router DHCP leases" in captured.err  # nosec B101


def test_cli_reports_missing_credentials(monkeypatch, tmp_path, capsys):
    monkeypatch.delenv("TAPO_USERNAME", raising=False)
    monkeypatch.delenv("TAPO_PASSWORD", raising=False)
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps({"devices": [{"name": "desk", "ip": "192.168.1.50"}]}), encoding="utf-8"
    )

    monkeypatch.chdir(tmp_path)

    result = cli.main(["--config", str(config_path)])

    captured = capsys.readouterr()
    assert result == 2  # nosec B101
    assert "TAPO_USERNAME" in captured.err  # nosec B101
    assert "TAPO_PASSWORD" in captured.err  # nosec B101


def test_cli_reports_invalid_config_without_traceback(tmp_path, capsys):
    config_path = tmp_path / "config.json"
    config_path.write_text("export TAPO_USERNAME='user@example.com'", encoding="utf-8")

    result = cli.main(["--config", str(config_path)])

    captured = capsys.readouterr()
    assert result == 2  # nosec B101
    assert "Config error:" in captured.err  # nosec B101
    assert "is not valid JSON" in captured.err  # nosec B101


def test_cli_prints_table_and_writes_jsonl(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("TAPO_USERNAME", "user@example.com")
    monkeypatch.setenv("TAPO_PASSWORD", "secret")
    config_path = tmp_path / "config.json"
    output_path = tmp_path / "readings.jsonl"
    config_path.write_text(
        json.dumps({"devices": [{"name": "desk", "ip": "192.168.1.50"}]}), encoding="utf-8"
    )

    def fake_collect(username, password, devices):
        assert username == "user@example.com"  # nosec B101
        assert password == "secret"  # nosec B101 B105
        assert devices[0].name == "desk"  # nosec B101
        return [normalize_reading("desk", "192.168.1.50", {"current_power": 12.5})], []

    monkeypatch.setattr(cli, "collect_readings", fake_collect)

    result = cli.main(["--config", str(config_path), "--output", str(output_path)])

    captured = capsys.readouterr()
    assert result == 0  # nosec B101
    assert "desk\t192.168.1.50\t12.5" in captured.out  # nosec B101
    assert json.loads(output_path.read_text(encoding="utf-8").splitlines()[0])["power_w"] == 12.5  # nosec B101


def test_cli_suggests_discovery_when_all_devices_fail(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("TAPO_USERNAME", "user@example.com")
    monkeypatch.setenv("TAPO_PASSWORD", "secret")
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps({"devices": [{"name": "desk", "ip": "192.168.1.50"}]}), encoding="utf-8"
    )

    def fake_collect(username, password, devices):
        return [], ["desk (192.168.1.50): Connection timeout to host http://192.168.1.50/app"]

    monkeypatch.setattr(cli, "collect_readings", fake_collect)

    result = cli.main(["--config", str(config_path)])

    captured = capsys.readouterr()
    assert result == 1  # nosec B101
    assert "ERROR desk" in captured.err  # nosec B101
    assert "Run: tapo-probe --discover" in captured.err  # nosec B101


def test_cli_reports_partial_success_summary(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("TAPO_USERNAME", "user@example.com")
    monkeypatch.setenv("TAPO_PASSWORD", "secret")
    config_path = tmp_path / "config.json"
    output_path = tmp_path / "readings.jsonl"
    config_path.write_text(
        json.dumps(
            {
                "devices": [
                    {"name": "ok", "ip": "192.168.2.93"},
                    {"name": "bad", "ip": "192.168.2.58"},
                ]
            }
        ),
        encoding="utf-8",
    )

    def fake_collect(username, password, devices):
        return [normalize_reading("ok", "192.168.2.93", {"current_power": 22})], [
            "bad (192.168.2.58): HASH_MISMATCH"
        ]

    monkeypatch.setattr(cli, "collect_readings", fake_collect)

    result = cli.main(["--config", str(config_path), "--output", str(output_path)])

    captured = capsys.readouterr()
    assert result == 0  # nosec B101
    assert "Summary: 1 succeeded, 1 failed" in captured.err  # nosec B101
    assert output_path.exists()  # nosec B101


def test_cli_discover_prints_found_devices(monkeypatch, capsys):
    monkeypatch.setattr(
        cli, "discover_devices", lambda timeout=5: [{"ip": "192.168.2.73", "model": "P110"}]
    )

    result = cli.main(["--discover"])

    captured = capsys.readouterr()
    assert result == 0  # nosec B101
    assert "192.168.2.73" in captured.out  # nosec B101
    assert "P110" in captured.out  # nosec B101


def test_cli_discover_passes_timeout(monkeypatch, capsys):
    called = {}

    def fake_discover(timeout=5):
        called["timeout"] = timeout
        return [{"ip": "192.168.2.73", "model": "P110"}]

    monkeypatch.setattr(cli, "discover_devices", fake_discover)

    result = cli.main(["--discover", "--timeout", "2"])

    assert result == 0  # nosec B101
    assert called["timeout"] == 2  # nosec B101


def test_cli_serve_starts_exporter(monkeypatch, tmp_path):
    monkeypatch.setenv("TAPO_USERNAME", "user@example.com")
    monkeypatch.setenv("TAPO_PASSWORD", "secret")
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps({"devices": [{"name": "desk", "hostname": "desk-host", "ip": "192.168.1.50"}]}),
        encoding="utf-8",
    )
    called = {}

    def fake_serve(config, port, interval):
        called["config"] = config
        called["port"] = port
        called["interval"] = interval

    monkeypatch.setattr(cli, "serve_metrics", fake_serve)

    result = cli.main(["serve", "--config", str(config_path), "--port", "9108", "--interval", "60"])

    assert result == 0  # nosec B101
    assert called["config"].devices[0].hostname == "desk-host"  # nosec B101
    assert called["port"] == 9108  # nosec B101
    assert called["interval"] == 60  # nosec B101


def test_cli_serve_uses_sys_argv_when_argv_is_none(monkeypatch, tmp_path):
    monkeypatch.setenv("TAPO_USERNAME", "user@example.com")
    monkeypatch.setenv("TAPO_PASSWORD", "secret")
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps({"devices": [{"name": "desk", "ip": "192.168.1.50"}]}), encoding="utf-8"
    )
    called = {}

    def fake_serve(config, port, interval):
        called["port"] = port

    monkeypatch.setattr(cli, "serve_metrics", fake_serve)
    monkeypatch.setattr(
        "sys.argv", ["tapo-probe", "serve", "--config", str(config_path), "--port", "9108"]
    )

    result = cli.main()

    assert result == 0  # nosec B101
    assert called["port"] == 9108  # nosec B101
