# Tapo Probe

Local-first probe for TP-Link Tapo P110 smart plug energy readings.

The first milestone is intentionally small: prove local access, print current readings, and append JSONL records. Grafana integration comes after real plug access is confirmed.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

Create `.env` for your Tapo cloud account credentials. These are used by the local Tapo protocol library to authenticate to plugs on your LAN. `.env` is ignored by git.

```dotenv
TAPO_USERNAME=you@example.com
TAPO_PASSWORD=your-password
```

Shell environment variables with the same names override `.env` values.

In the Tapo app, also enable local third-party access: `Me > Third-Party Services > Third-Party Compatibility`. Without this, the plugs can be discovered but reject local energy reads with a `FORBIDDEN` error.

Create a local config file. `tapo-config.json` is ignored by git.

```json
{
  "devices": [
    {"name": "desk", "ip": "192.168.1.50"}
  ]
}
```

Run a probe:

```bash
tapo-probe --config tapo-config.json --output tapo-readings.jsonl
```

If you do not know plug IP addresses, check your router DHCP leases, network scanner, or the Tapo app device details. Configure static DHCP reservations once found so dashboard labels remain stable.

## Output

Readings are appended to JSONL with one object per line. Each record includes timestamp, configured device name, IP, available power metrics, and raw fields useful for troubleshooting firmware differences.

## Grafana Next Steps

Run the Prometheus exporter:

```bash
tapo-probe serve --config tapo-config.json --port 9108 --interval 60
```

Metrics are exposed at `http://localhost:9108/metrics`. Each metric includes `name`, `ip`, and `hostname` labels. Add optional hostnames in `tapo-config.json`:

```json
{
  "devices": [
    {"name": "desk", "hostname": "desk-plug", "ip": "192.168.1.50"}
  ]
}
```

Example metrics:

- `tapo_plug_power_watts`
- `tapo_plug_today_energy_wh`
- `tapo_plug_month_energy_wh`
- `tapo_plug_today_runtime_seconds`
- `tapo_plug_month_runtime_seconds`
- `tapo_plug_rssi_dbm`
- `tapo_plug_up`

To send to Grafana Cloud, install Grafana Alloy and copy `grafana/alloy.config.example` to your Alloy config path. Set these environment variables from your Grafana Cloud Prometheus remote_write details:

```bash
export GRAFANA_CLOUD_PROM_URL='https://prometheus-prod-xx.grafana.net/api/prom/push'
export GRAFANA_CLOUD_PROM_USER='your-prometheus-user-id'
export GRAFANA_METRICS_WRITE='your-grafana-cloud-metrics-write-token'
export GRAFANA_METRICS_READ='your-grafana-cloud-metrics-read-token'
```

`GRAFANA_CLOUD_PROM_URL` must be the Prometheus remote_write endpoint from Grafana Cloud, not a dashboard URL. Dashboard URLs like https://getcass.grafana.net/d/ are for viewing dashboards and cannot receive metrics.

`GRAFANA_METRICS_WRITE` must be valid for Grafana Cloud Metrics remote_write. A Grafana service account token that can call the Grafana dashboard API may still fail remote_write with `401 Unauthorized: invalid token` unless it has the Grafana Cloud Metrics publish/write permission. `GRAFANA_METRICS_READ` is used only for verification queries.

In Grafana Cloud, add panels using PromQL such as `tapo_plug_power_watts` grouped by `hostname`.

## Development

```bash
pytest -v
```
