# Installer Managed Alloy Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extend the installer so macOS installs and manages both the Tapo exporter and Grafana Alloy remote_write service.

**Architecture:** Keep Tapo exporter and Alloy as separate user LaunchAgents. The installer writes managed files under `~/.config/tapo-probe`: `alloy.config` from the repo example and an `alloy-run.sh` wrapper that sources repo `.env` without printing secrets, then executes `alloy run`. If Alloy is missing, the installer leaves the exporter installed and prints a clear install command.

**Tech Stack:** Bash, macOS launchd LaunchAgents, Grafana Alloy, pytest docs/script checks.

---

### Task 1: Installer Contract Tests

**Files:**
- Modify: `tests/test_grafana_docs.py`

**Step 1: Write failing tests**

Add tests asserting `scripts/install-service.sh` contains:
- `com.tapo-probe.alloy`
- `alloy-run.sh`
- `alloy.config`
- `alloy run`
- `brew install grafana/grafana/alloy`
- README text stating the installer manages Alloy.

**Step 2: Run tests to verify failure**

Run: `.venv/bin/pytest tests/test_grafana_docs.py -v`
Expected: FAIL because Alloy management is not implemented yet.

### Task 2: Installer Alloy Management

**Files:**
- Modify: `scripts/install-service.sh`

**Step 1: Implement minimal macOS Alloy management**

Add functions to:
- copy `grafana/alloy.config.example` to `~/.config/tapo-probe/alloy.config`
- write `~/.config/tapo-probe/alloy-run.sh`
- install `~/Library/LaunchAgents/com.tapo-probe.alloy.plist`
- start, status, and uninstall the Alloy LaunchAgent

**Step 2: Run syntax check**

Run: `bash -n scripts/install-service.sh`
Expected: PASS.

### Task 3: Documentation

**Files:**
- Modify: `README.md`

**Step 1: Update installer docs**

Document that the installer starts both exporter and Alloy when Alloy is installed, and how to check both services.

**Step 2: Run docs tests**

Run: `.venv/bin/pytest tests/test_grafana_docs.py -v`
Expected: PASS.

### Task 4: Verification

**Files:**
- All changed files

**Step 1: Run verification**

Run: `bash -n scripts/install-service.sh`
Run: `shellcheck scripts/install-service.sh` if available
Run: `alloy validate grafana/alloy.config.example` if available
Run: `.venv/bin/pytest -v`
Expected: PASS.
