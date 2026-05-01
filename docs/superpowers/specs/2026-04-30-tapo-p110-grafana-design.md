# Tapo P110 Data Collection and Grafana Design

## Goal

Build a small local-first tool to confirm that TP-Link Tapo P110 smart plugs can be queried from the LAN, capture their energy readings, and create a path to Grafana dashboards once access is proven.

## Context

No existing Grafana, Prometheus, InfluxDB, Home Assistant, or Tapo-related project was found in `/Users/cass/git`. The first milestone should therefore avoid a full monitoring stack and focus on proving local device access.

The user prefers a local script first and is not yet sure whether plug IP addresses or Tapo credentials are available.

## Recommended Approach

Use a local Python probe/collector as the first step.

The tool should:

- Read Tapo account credentials from environment variables or a local config file.
- Accept optional plug IP addresses from config.
- Provide clear setup/discovery instructions when IPs are not known.
- Query each P110 over the local network using an existing Tapo-compatible Python library.
- Print current readings in a concise terminal table.
- Append timestamped readings to a local JSONL or CSV file.

## Data Model

Each reading should include:

- Timestamp in UTC.
- Plug name or configured label.
- Plug IP address.
- Current power in watts, when available.
- Voltage, when available.
- Current, when available.
- Total energy, when available.
- Raw response fields only if useful for troubleshooting.

## Phases

### Phase 1: Access Probe

Create a script that verifies credentials, connects to configured plug IPs, fetches device metadata, and prints available energy metrics. If no IPs are configured, the script should stop with actionable discovery guidance rather than silently failing.

### Phase 2: Local Logging

Extend the script to append successful readings to a local file. JSONL is preferred initially because it preserves variable fields from different firmware/library versions without schema churn.

### Phase 3: Grafana Integration

After local readings are confirmed, choose one Grafana path:

- Prometheus exporter: expose `/metrics` for scraping and Grafana dashboarding through Prometheus.
- InfluxDB writer: write readings to InfluxDB and query them directly from Grafana.

Prometheus is recommended if the user already wants a metrics-style stack. InfluxDB is recommended if the main goal is long-term energy analytics.

## Error Handling

The collector should report per-device failures without aborting the whole run. Authentication failures, unreachable hosts, unsupported firmware responses, and missing energy fields should produce clear messages.

Secrets should never be printed in logs or written to output files.

## Verification

Verification for Phase 1 should include:

- Running the script with no config and confirming it gives setup guidance.
- Running the script with invalid credentials or IPs and confirming useful errors.
- Running against at least one real P110 and confirming device metadata plus energy readings are returned.

Verification for later Grafana work should include:

- Confirming metrics or Influx points are emitted.
- Confirming Grafana can render current power and historical energy usage.
