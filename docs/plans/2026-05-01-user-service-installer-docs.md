# User Service Installer And Dashboard Documentation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add user-level macOS/Linux autostart installation, current README documentation, and a sample Grafana dashboard.

**Architecture:** Keep service installation in one Bash script that detects macOS `launchd` or Linux `systemd --user`. Keep documentation in `README.md` and dashboard code in `grafana/tapo-p110-dashboard.sample.json`. Add lightweight tests that verify the docs and dashboard reference current metrics and install commands.

**Tech Stack:** Bash, launchd user LaunchAgents, systemd user services, Grafana dashboard JSON, pytest.

---

### Task 1: Installer Documentation Tests

**Files:**
- Modify: `tests/test_grafana_docs.py`

**Step 1: Write failing tests**

Add tests that assert:
- `README.md` references `scripts/install-service.sh`
- `README.md` documents `systemctl --user` and `launchctl`
- `grafana/tapo-p110-dashboard.sample.json` exists and contains dashboard-compatible metric names

**Step 2: Run tests to verify failure**

Run: `.venv/bin/pytest tests/test_grafana_docs.py -v`

Expected: FAIL because installer docs and dashboard JSON do not exist yet.

### Task 2: User-Level Service Installer

**Files:**
- Create: `scripts/install-service.sh`

**Step 1: Implement installer**

Create a Bash script with strict mode that:
- installs the project into `.venv`
- creates `~/.config/tapo-probe/tapo-config.json` from a sample if missing
- on macOS writes `~/Library/LaunchAgents/com.tapo-probe.exporter.plist`
- on Linux writes `~/.config/systemd/user/tapo-probe.service`
- starts/restarts the user service

**Step 2: Syntax check**

Run: `bash -n scripts/install-service.sh`

Expected: PASS.

### Task 3: Dashboard Sample

**Files:**
- Create: `grafana/tapo-p110-dashboard.sample.json`

**Step 1: Add dashboard JSON**

Add a Grafana dashboard with power, energy, runtime, RSSI, uptime, and safety panels using metrics emitted by `src/tapo_probe/metrics.py`.

**Step 2: Validate JSON through tests**

Run: `.venv/bin/pytest tests/test_grafana_docs.py -v`

Expected: tests that parse dashboard JSON pass once README is updated.

### Task 4: README Update

**Files:**
- Modify: `README.md`

**Step 1: Update docs**

Document setup, config, one-shot probe, exporter, installer/autostart, Alloy, dashboard import, metrics, and development checks.

**Step 2: Run docs tests**

Run: `.venv/bin/pytest tests/test_grafana_docs.py -v`

Expected: PASS.

### Task 5: Final Verification

**Files:**
- All changed files

**Step 1: Run relevant checks**

Run: `bash -n scripts/install-service.sh`
Run: `.venv/bin/pytest -v`

Expected: PASS.
