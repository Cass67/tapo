# Containerfile Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add an exporter-only container image path for Docker and Podman users.

**Architecture:** Add a root `Containerfile` that installs the Python package and runs `tapo-probe serve` against a mounted config. Add `.dockerignore` to prevent secrets and local artifacts entering the build context. Update README and docs tests to keep usage discoverable.

**Tech Stack:** Docker/Podman Containerfile, Python slim image, pytest docs checks.

---

### Task 1: Docs Tests

**Files:**
- Modify: `tests/test_grafana_docs.py`

**Step 1: Write failing tests**

Add tests that assert `Containerfile`, `docker build`, `podman build`, `/config/tapo-config.json`, `TAPO_USERNAME`, and `-p 9108:9108` are documented.

**Step 2: Run tests to verify failure**

Run: `.venv/bin/pytest tests/test_grafana_docs.py -v`
Expected: FAIL because container docs and files are missing.

### Task 2: Container Files

**Files:**
- Create: `Containerfile`
- Create: `.dockerignore`

**Step 1: Add container image definition**

Use `python:3.12-slim`, copy package metadata and `src/`, install package without dev extras, expose `9108`, and default to `tapo-probe serve --config /config/tapo-config.json --port 9108 --interval 60`.

**Step 2: Add build context ignores**

Ignore `.env*`, `.venv`, `.git`, caches, local readings, and local Tapo configs.

### Task 3: README Update

**Files:**
- Modify: `README.md`

**Step 1: Document Docker and Podman usage**

Add build and run examples using mounted config and environment variables.

**Step 2: Run docs tests**

Run: `.venv/bin/pytest tests/test_grafana_docs.py -v`
Expected: PASS.

### Task 4: Verification

**Files:**
- All changed files

**Step 1: Run relevant checks**

Run: `.venv/bin/pytest -v`
Run: `docker build -f Containerfile -t tapo-probe:test .` if Docker is available.

Expected: Tests pass; container build passes when Docker is available.
