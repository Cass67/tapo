# Tapo P110 Local Probe Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a local Python CLI that validates Tapo P110 access, reads energy data, and writes timestamped readings to JSONL.

**Architecture:** Keep the first version small: one CLI entrypoint, one config loader, one Tapo client adapter, and one JSONL writer. The real Tapo dependency is isolated behind an adapter so config and output behavior can be tested without a physical plug.

**Tech Stack:** Python 3, pytest, `pyproject.toml`, Tapo-compatible Python library selected during implementation after confirming package support.

---

### Task 1: Project Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `.gitignore`
- Create: `src/tapo_probe/__init__.py`
- Create: `tests/test_config.py`

**Step 1: Write the failing test**

Create `tests/test_config.py` with a test that imports `tapo_probe.config.load_config` and verifies missing config returns no devices and records missing credentials.

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py -v`

Expected: FAIL because `tapo_probe.config` does not exist.

**Step 3: Write minimal implementation**

Create package structure, `pyproject.toml`, `.gitignore`, and a minimal `src/tapo_probe/config.py` with dataclasses for config and a `load_config()` function.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py -v`

Expected: PASS.

### Task 2: Config Loading

**Files:**
- Modify: `src/tapo_probe/config.py`
- Modify: `tests/test_config.py`

**Step 1: Write failing tests**

Add tests for reading credentials from environment variables and device definitions from a JSON config file.

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_config.py -v`

Expected: FAIL for unsupported env/config parsing.

**Step 3: Implement config parsing**

Support `TAPO_USERNAME`, `TAPO_PASSWORD`, and a JSON file containing `devices` with `name` and `ip` fields.

**Step 4: Run tests**

Run: `pytest tests/test_config.py -v`

Expected: PASS.

### Task 3: Setup Guidance CLI

**Files:**
- Create: `src/tapo_probe/cli.py`
- Create: `tests/test_cli.py`
- Modify: `pyproject.toml`

**Step 1: Write failing tests**

Test that the CLI exits with a useful message when no devices are configured, including guidance to find plug IPs from the router, DHCP leases, or Tapo app details.

**Step 2: Run tests**

Run: `pytest tests/test_cli.py -v`

Expected: FAIL because CLI does not exist.

**Step 3: Implement CLI**

Add an argparse-based CLI and console script entrypoint. Do not contact real devices yet.

**Step 4: Run tests**

Run: `pytest tests/test_cli.py -v`

Expected: PASS.

### Task 4: Reading Normalization

**Files:**
- Create: `src/tapo_probe/readings.py`
- Create: `tests/test_readings.py`

**Step 1: Write failing tests**

Test normalization of plausible P110 energy responses into fields: timestamp, device name, IP, power watts, voltage, current, total energy, and raw fields.

**Step 2: Run tests**

Run: `pytest tests/test_readings.py -v`

Expected: FAIL because normalization does not exist.

**Step 3: Implement normalization**

Handle common field variants defensively and preserve unknown raw data for troubleshooting.

**Step 4: Run tests**

Run: `pytest tests/test_readings.py -v`

Expected: PASS.

### Task 5: JSONL Output

**Files:**
- Create: `src/tapo_probe/output.py`
- Create: `tests/test_output.py`

**Step 1: Write failing tests**

Test appending one or more normalized readings to a JSONL file.

**Step 2: Run tests**

Run: `pytest tests/test_output.py -v`

Expected: FAIL because output module does not exist.

**Step 3: Implement JSONL writer**

Append each reading as compact JSON with one record per line.

**Step 4: Run tests**

Run: `pytest tests/test_output.py -v`

Expected: PASS.

### Task 6: Tapo Client Adapter

**Files:**
- Create: `src/tapo_probe/tapo_client.py`
- Create: `tests/test_tapo_client.py`
- Modify: `pyproject.toml`

**Step 1: Investigate package choice**

Confirm the best maintained Python package for Tapo P110 local energy readings.

**Step 2: Write adapter tests with a fake backend**

Test that the adapter returns normalized metadata and energy data without requiring a physical plug.

**Step 3: Implement adapter**

Wrap the selected library behind a small interface so the CLI does not depend on library-specific response shapes.

**Step 4: Run tests**

Run: `pytest tests/test_tapo_client.py -v`

Expected: PASS.

### Task 7: End-to-End CLI Wiring

**Files:**
- Modify: `src/tapo_probe/cli.py`
- Modify: `tests/test_cli.py`
- Modify: `README.md`

**Step 1: Write failing CLI tests**

Test a configured fake device run prints a concise table and writes JSONL output.

**Step 2: Run tests**

Run: `pytest tests/test_cli.py -v`

Expected: FAIL until wiring is complete.

**Step 3: Implement wiring**

Load config, poll configured devices, report per-device errors, print readings, and write JSONL output.

**Step 4: Run tests**

Run: `pytest -v`

Expected: PASS.

### Task 8: Manual Verification Notes

**Files:**
- Modify: `README.md`

**Step 1: Document setup**

Add instructions for creating a virtualenv, installing the package, setting `TAPO_USERNAME` and `TAPO_PASSWORD`, creating a local config file, and running the probe.

**Step 2: Document Grafana next steps**

Briefly describe the future Prometheus exporter and InfluxDB writer options.

**Step 3: Run final verification**

Run: `pytest -v`

Expected: PASS.
