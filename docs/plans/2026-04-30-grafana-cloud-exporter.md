# Grafana Cloud Exporter Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a Prometheus metrics exporter for Tapo P110 readings that Grafana Alloy can scrape and remote-write to Grafana Cloud.

**Architecture:** Keep the existing one-shot CLI and add a long-running exporter mode. The exporter polls configured plugs, caches latest readings, and serves `/metrics`; Grafana Alloy handles Grafana Cloud authentication and remote_write. Metrics include a `hostname` label, using device config override when present and falling back to the Tapo nickname/name.

**Tech Stack:** Python 3, standard-library HTTP server, existing `tapo` package, pytest, Grafana Alloy config.

---

### Task 1: Device Hostname Config

**Files:**
- Modify: `src/tapo_probe/config.py`
- Modify: `tests/test_config.py`

**Step 1: Write failing test**

Add a test that loads a device with `hostname` from JSON:

```python
def test_loads_optional_device_hostname(monkeypatch, tmp_path):
    monkeypatch.setenv("TAPO_USERNAME", "user@example.com")
    monkeypatch.setenv("TAPO_PASSWORD", "secret")
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"devices": [{"name": "desk", "hostname": "desk-plug", "ip": "192.168.1.50"}]}), encoding="utf-8")

    config = load_config(config_path)

    assert config.devices[0].hostname == "desk-plug"
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_config.py::test_loads_optional_device_hostname -v`

Expected: FAIL because `DeviceConfig` has no hostname.

**Step 3: Implement minimal config support**

Add `hostname: str | None = None` to `DeviceConfig` and parse optional `hostname` in `load_config()`.

**Step 4: Run test**

Run: `.venv/bin/pytest tests/test_config.py::test_loads_optional_device_hostname -v`

Expected: PASS.

### Task 2: Metrics Formatting

**Files:**
- Create: `src/tapo_probe/metrics.py`
- Create: `tests/test_metrics.py`

**Step 1: Write failing tests**

Test that one normalized reading renders Prometheus text including labels `name`, `ip`, and `hostname`:

```python
def test_formats_prometheus_metrics_with_hostname():
    reading = normalize_reading("desk", "192.168.1.50", {"current_power": 12.5, "today_energy": 400, "month_energy": 1200, "rssi": -55, "nickname": "Desk Plug"})

    text = format_metrics([reading], {}, hostname_overrides={"192.168.1.50": "desk-host"})

    assert 'tapo_plug_power_watts{hostname="desk-host",ip="192.168.1.50",name="desk"} 12.5' in text
    assert 'tapo_plug_up{hostname="desk-host",ip="192.168.1.50",name="desk"} 1' in text
```

Also test failed devices render `tapo_plug_up 0`.

**Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_metrics.py -v`

Expected: FAIL because metrics module does not exist.

**Step 3: Implement metrics formatter**

Create `format_metrics(readings, errors, hostname_overrides=None)` with metrics:

- `tapo_plug_power_watts`
- `tapo_plug_today_energy_wh`
- `tapo_plug_month_energy_wh`
- `tapo_plug_today_runtime_seconds`
- `tapo_plug_month_runtime_seconds`
- `tapo_plug_rssi_dbm`
- `tapo_plug_up`

Escape Prometheus label values. Use config hostname override first, then raw `nickname`, then reading name.

**Step 4: Run tests**

Run: `.venv/bin/pytest tests/test_metrics.py -v`

Expected: PASS.

### Task 3: Exporter Loop and HTTP Server

**Files:**
- Create: `src/tapo_probe/exporter.py`
- Create: `tests/test_exporter.py`

**Step 1: Write failing tests**

Test that an exporter state object polls readings, records errors, and returns metrics text.

**Step 2: Run tests**

Run: `.venv/bin/pytest tests/test_exporter.py -v`

Expected: FAIL because exporter module does not exist.

**Step 3: Implement exporter state**

Create a small `ExporterState` class with:

- `poll_once()` calling `collect_readings()`
- cached readings/errors
- `metrics_text()` returning Prometheus format

Keep the HTTP server simple and standard-library based.

**Step 4: Run tests**

Run: `.venv/bin/pytest tests/test_exporter.py -v`

Expected: PASS.

### Task 4: CLI `serve` Mode

**Files:**
- Modify: `src/tapo_probe/cli.py`
- Modify: `tests/test_cli.py`

**Step 1: Write failing test**

Test parser behavior for `serve` mode by monkeypatching `serve_metrics()` and asserting it receives config, output port, and interval.

**Step 2: Run test**

Run: `.venv/bin/pytest tests/test_cli.py::test_cli_serve_starts_exporter -v`

Expected: FAIL because `serve` does not exist.

**Step 3: Implement CLI mode**

Add subcommand-like behavior without breaking existing one-shot usage:

```bash
tapo-probe serve --config tapo-config.json --port 9108 --interval 60
```

**Step 4: Run test**

Run: `.venv/bin/pytest tests/test_cli.py::test_cli_serve_starts_exporter -v`

Expected: PASS.

### Task 5: Grafana Alloy Example

**Files:**
- Create: `grafana/alloy.config.example`
- Modify: `README.md`

**Step 1: Write docs**

Add Alloy config that scrapes `localhost:9108` and remote-writes to Grafana Cloud using environment variables:

- `GRAFANA_CLOUD_PROM_URL`
- `GRAFANA_CLOUD_PROM_USER`
- `GRAFANA_CLOUD_API_KEY`

**Step 2: Document workflow**

README should show:

```bash
tapo-probe serve --config tapo-config.json --port 9108 --interval 60
```

and where to find Grafana Cloud Prometheus remote_write credentials.

**Step 3: Run final verification**

Run: `.venv/bin/pytest -v`

Expected: PASS.
