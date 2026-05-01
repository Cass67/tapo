from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tapo_probe.config import ConfigError, load_config
from tapo_probe.exporter import serve_metrics
from tapo_probe.output import append_jsonl
from tapo_probe.tapo_client import collect_readings, discover_devices

DISCOVERY_GUIDANCE = """No Tapo devices are configured.

Find each plug IP address from one of:
- Router DHCP leases or attached-device list
- A LAN scanner such as arp-scan or nmap
- Tapo app device details, if shown by your app version

Then create a config file like:
{
  "devices": [
    {"name": "desk", "ip": "192.168.1.50"}
  ]
}
"""


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "serve":
        return _serve(argv[1:])

    parser = argparse.ArgumentParser(description="Probe Tapo P110 smart plug energy readings")
    parser.add_argument("--config", type=Path, help="Path to JSON config file")
    parser.add_argument(
        "--output", type=Path, default=Path("tapo-readings.jsonl"), help="JSONL output path"
    )
    parser.add_argument(
        "--discover", action="store_true", help="Scan the LAN for Tapo devices and print their IPs"
    )
    parser.add_argument("--timeout", type=int, default=5, help="Discovery timeout in seconds")
    args = parser.parse_args(argv)

    if args.discover:
        return _discover(args.timeout)

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 2
    missing = _check_missing(config)
    if missing is not None:
        return missing
    return _probe(config, args.output)


def _discover(timeout: int = 5) -> int:
    devices = discover_devices(timeout=timeout)
    if not devices:
        print(
            "No Tapo devices discovered. Check that the plug is powered on and on this LAN.",
            file=sys.stderr,
        )
        return 1
    print("ip\tmodel\ttype\tmac")
    for device in devices:
        print(
            f"{device.get('ip', '-')}\t{device.get('model', '-')}\t"
            f"{device.get('type', '-')}\t{device.get('mac', '-')}"
        )
    return 0


def _check_missing(config: object) -> int | None:
    if "devices" in config.missing:
        print(DISCOVERY_GUIDANCE, file=sys.stderr)
        return 2
    credential_gaps = [item for item in config.missing if item != "devices"]
    if credential_gaps:
        print(
            f"Missing required environment variables: {', '.join(credential_gaps)}", file=sys.stderr
        )
        return 2
    if config.username is None or config.password is None:
        print("Missing credentials", file=sys.stderr)
        return 2
    return None


def _probe(config: object, output_path: Path) -> int:
    readings, errors = collect_readings(config.username, config.password, config.devices)
    for error in errors:
        print(f"ERROR {error}", file=sys.stderr)
    if readings or errors:
        print(f"Summary: {len(readings)} succeeded, {len(errors)} failed", file=sys.stderr)
    if errors and not readings:
        print("Run: tapo-probe --discover", file=sys.stderr)
        print(
            "Also verify the configured IP is on your LAN subnet and the plug is powered on.",
            file=sys.stderr,
        )
    if readings:
        append_jsonl(output_path, readings)
        _print_table(readings)
    return 1 if errors and not readings else 0


def _serve(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Serve Tapo P110 metrics for Prometheus/Grafana Alloy"
    )
    parser.add_argument("--config", type=Path, required=True, help="Path to JSON config file")
    parser.add_argument("--port", type=int, default=9108, help="Metrics listen port")
    parser.add_argument("--interval", type=int, default=60, help="Polling interval in seconds")
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 2
    if config.missing:
        print(f"Missing required configuration: {', '.join(config.missing)}", file=sys.stderr)
        return 2
    serve_metrics(config, port=args.port, interval=args.interval)
    return 0


def _print_table(readings: list[object]) -> None:
    print("name\tip\tpower_w\tvoltage_v\tcurrent_a\ttotal_energy_kwh")
    for reading in readings:
        print(
            f"{reading.name}\t{reading.ip}\t{_fmt(reading.power_w)}\t{_fmt(reading.voltage_v)}\t"
            f"{_fmt(reading.current_a)}\t{_fmt(reading.total_energy_kwh)}"
        )


def _fmt(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:g}"


if __name__ == "__main__":
    raise SystemExit(main())
