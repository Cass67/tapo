# Dashboard Preview Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a visual README preview of the sample Grafana dashboard.

**Architecture:** Create a hand-authored SVG asset under `docs/assets/` and embed it in the README Sample Dashboard section. Keep the preview illustrative and leave the importable Grafana dashboard JSON unchanged. Add docs tests that verify the README references the SVG and the SVG contains expected panel names.

**Tech Stack:** SVG, Markdown, pytest docs checks.

---

### Task 1: Dashboard Preview Tests

**Files:**
- Modify: `tests/test_grafana_docs.py`

**Step 1: Write failing tests**

Add a docs test that asserts:
- README references `docs/assets/tapo-p110-dashboard-preview.svg`
- SVG contains `Current Power`, `Energy Used`, `Runtime`, `Wi-Fi RSSI`, `Device On`, and `Safety Status`

**Step 2: Run test to verify failure**

Run: `.venv/bin/pytest tests/test_grafana_docs.py -v`
Expected: FAIL because the SVG and README reference do not exist.

### Task 2: SVG Preview Asset

**Files:**
- Create: `docs/assets/tapo-p110-dashboard-preview.svg`

**Step 1: Create SVG**

Add a dark Grafana-style dashboard mockup with six panels matching `grafana/tapo-p110-dashboard.sample.json`.

### Task 3: README Embed

**Files:**
- Modify: `README.md`

**Step 1: Embed preview**

Add the SVG image under `## Sample Dashboard` with a note that it is illustrative.

**Step 2: Run docs tests**

Run: `.venv/bin/pytest tests/test_grafana_docs.py -v`
Expected: PASS.

### Task 4: Verification

**Files:**
- All changed files

**Step 1: Run full tests**

Run: `.venv/bin/pytest -v`
Expected: PASS.
