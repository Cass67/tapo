from __future__ import annotations

import threading
import time
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from tapo_probe.config import ProbeConfig
from tapo_probe.metrics import format_metrics
from tapo_probe.readings import Reading
from tapo_probe.tapo_client import collect_readings as default_collect_readings


class ExporterState:
    def __init__(
        self,
        config: ProbeConfig,
        collect_readings: Callable[..., tuple[list[Reading], list[str]]] = default_collect_readings,
    ) -> None:
        self._config = config
        self._collect_readings = collect_readings
        self._readings: list[Reading] = []
        self._errors: dict[tuple[str, str], str] = {}
        self._lock = threading.Lock()

    def poll_once(self) -> None:
        if self._config.username is None or self._config.password is None:
            return
        readings, errors = self._collect_readings(
            self._config.username, self._config.password, self._config.devices
        )
        parsed_errors = _parse_errors(errors)
        with self._lock:
            self._readings = readings
            self._errors = parsed_errors

    def metrics_text(self) -> str:
        with self._lock:
            readings = list(self._readings)
            errors = dict(self._errors)
        return format_metrics(
            readings, errors, hostname_overrides=_hostname_overrides(self._config)
        )


def serve_metrics(config: ProbeConfig, port: int = 9108, interval: int = 60) -> None:
    state = ExporterState(config)
    state.poll_once()

    def poll_loop() -> None:
        while True:
            time.sleep(interval)
            state.poll_once()

    thread = threading.Thread(target=poll_loop, daemon=True)
    thread.start()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - stdlib handler API.
            if self.path != "/metrics":
                self.send_response(404)
                self.end_headers()
                return
            body = state.metrics_text().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, _format: str, *_args: object) -> None:
            return

    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()


def _hostname_overrides(config: ProbeConfig) -> dict[str, str]:
    return {device.ip: device.hostname for device in config.devices if device.hostname}


def _parse_errors(errors: list[str]) -> dict[tuple[str, str], str]:
    parsed = {}
    for error in errors:
        prefix, _, message = error.partition(": ")
        name, _, ip_part = prefix.partition(" (")
        ip = ip_part.rstrip(")")
        if name and ip:
            parsed[(name, ip)] = message
    return parsed
