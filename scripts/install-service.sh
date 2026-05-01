#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="tapo-probe"
MACOS_LABEL="com.tapo-probe.exporter"
MACOS_ALLOY_LABEL="com.tapo-probe.alloy"
PORT="${TAPO_PROBE_PORT:-9108}"
INTERVAL="${TAPO_PROBE_INTERVAL:-60}"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
venv_dir="$repo_root/.venv"
config_dir="${XDG_CONFIG_HOME:-$HOME/.config}/tapo-probe"
config_file="$config_dir/tapo-config.json"
alloy_config_file="$config_dir/alloy.config"
alloy_runner="$config_dir/alloy-run.sh"

usage() {
  printf 'Usage: %s [install|uninstall|status]\n' "${0##*/}"
}

create_config_sample() {
  mkdir -p "$config_dir"
  if [[ ! -f "$config_file" ]]; then
    cat >"$config_file" <<'JSON'
{
  "devices": [
    {"name": "desk", "hostname": "desk-plug", "ip": "192.168.1.50"}
  ]
}
JSON
    printf 'Created sample config at %s\n' "$config_file"
    printf 'Edit it before relying on the service.\n'
  fi
}

install_package() {
  if [[ ! -x "$venv_dir/bin/python" ]]; then
    python3 -m venv "$venv_dir"
  fi
  "$venv_dir/bin/python" -m pip install --upgrade pip
  "$venv_dir/bin/python" -m pip install -e "$repo_root"
}

install_macos() {
  local launch_agents_dir="$HOME/Library/LaunchAgents"
  local logs_dir="$HOME/Library/Logs"
  local plist_file="$launch_agents_dir/$MACOS_LABEL.plist"

  mkdir -p "$launch_agents_dir" "$logs_dir"
  cat >"$plist_file" <<XML
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$MACOS_LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>$venv_dir/bin/tapo-probe</string>
    <string>serve</string>
    <string>--config</string>
    <string>$config_file</string>
    <string>--port</string>
    <string>$PORT</string>
    <string>--interval</string>
    <string>$INTERVAL</string>
  </array>
  <key>WorkingDirectory</key>
  <string>$repo_root</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>$logs_dir/tapo-probe.out.log</string>
  <key>StandardErrorPath</key>
  <string>$logs_dir/tapo-probe.err.log</string>
</dict>
</plist>
XML

  launchctl bootout "gui/$(id -u)" "$plist_file" >/dev/null 2>&1 || true
  launchctl bootstrap "gui/$(id -u)" "$plist_file"
  launchctl enable "gui/$(id -u)/$MACOS_LABEL"
  launchctl kickstart -k "gui/$(id -u)/$MACOS_LABEL"
  printf 'Installed macOS LaunchAgent: %s\n' "$plist_file"
  install_macos_alloy "$launch_agents_dir" "$logs_dir"
}

install_macos_alloy() {
  local launch_agents_dir="$1"
  local logs_dir="$2"
  local alloy_bin
  local plist_file="$launch_agents_dir/$MACOS_ALLOY_LABEL.plist"

  if ! alloy_bin="$(command -v alloy)"; then
    printf 'Grafana Alloy is not installed. Install it with: brew install grafana/grafana/alloy\n' >&2
    printf 'Tapo exporter is installed, but Grafana Cloud remote_write will not run until Alloy is installed and this installer is rerun.\n' >&2
    return 0
  fi

  cp "$repo_root/grafana/alloy.config.example" "$alloy_config_file"
  cat >"$alloy_runner" <<SH
#!/usr/bin/env bash
set -euo pipefail
if [[ -f "$repo_root/.env" ]]; then
  set -a
  source "$repo_root/.env"
  set +a
fi
# Run the equivalent of: alloy run "$alloy_config_file"
exec "$alloy_bin" run "$alloy_config_file"
SH
  chmod 700 "$alloy_runner"

  cat >"$plist_file" <<XML
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$MACOS_ALLOY_LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>$alloy_runner</string>
  </array>
  <key>WorkingDirectory</key>
  <string>$repo_root</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>$logs_dir/tapo-probe-alloy.out.log</string>
  <key>StandardErrorPath</key>
  <string>$logs_dir/tapo-probe-alloy.err.log</string>
</dict>
</plist>
XML

  launchctl bootout "gui/$(id -u)" "$plist_file" >/dev/null 2>&1 || true
  launchctl bootstrap "gui/$(id -u)" "$plist_file"
  launchctl enable "gui/$(id -u)/$MACOS_ALLOY_LABEL"
  launchctl kickstart -k "gui/$(id -u)/$MACOS_ALLOY_LABEL"
  printf 'Installed macOS Alloy LaunchAgent: %s\n' "$plist_file"
}

install_linux() {
  local systemd_user_dir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
  local service_file="$systemd_user_dir/$SERVICE_NAME.service"

  mkdir -p "$systemd_user_dir"
  cat >"$service_file" <<SYSTEMD
[Unit]
Description=Tapo P110 Prometheus exporter
After=network-online.target

[Service]
Type=simple
WorkingDirectory=$repo_root
ExecStart=$venv_dir/bin/tapo-probe serve --config $config_file --port $PORT --interval $INTERVAL
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
SYSTEMD

  systemctl --user daemon-reload
  systemctl --user enable --now "$SERVICE_NAME.service"
  printf 'Installed Linux user service: %s\n' "$service_file"
}

install_service() {
  create_config_sample
  install_package
  case "$(uname -s)" in
    Darwin) install_macos ;;
    Linux) install_linux ;;
    *)
      printf 'Unsupported OS: %s\n' "$(uname -s)" >&2
      return 1
      ;;
  esac
}

uninstall_service() {
  case "$(uname -s)" in
    Darwin)
      local plist_file="$HOME/Library/LaunchAgents/$MACOS_LABEL.plist"
      local alloy_plist_file="$HOME/Library/LaunchAgents/$MACOS_ALLOY_LABEL.plist"
      launchctl bootout "gui/$(id -u)" "$alloy_plist_file" >/dev/null 2>&1 || true
      launchctl bootout "gui/$(id -u)" "$plist_file" >/dev/null 2>&1 || true
      rm -f "$alloy_plist_file"
      rm -f "$plist_file"
      rm -f "$alloy_runner" "$alloy_config_file"
      ;;
    Linux)
      systemctl --user disable --now "$SERVICE_NAME.service" >/dev/null 2>&1 || true
      rm -f "${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user/$SERVICE_NAME.service"
      systemctl --user daemon-reload
      ;;
    *)
      printf 'Unsupported OS: %s\n' "$(uname -s)" >&2
      return 1
      ;;
  esac
}

service_status() {
  case "$(uname -s)" in
    Darwin)
      launchctl print "gui/$(id -u)/$MACOS_LABEL"
      launchctl print "gui/$(id -u)/$MACOS_ALLOY_LABEL"
      ;;
    Linux) systemctl --user status "$SERVICE_NAME.service" ;;
    *)
      printf 'Unsupported OS: %s\n' "$(uname -s)" >&2
      return 1
      ;;
  esac
}

command="${1:-install}"
case "$command" in
  install) install_service ;;
  uninstall) uninstall_service ;;
  status) service_status ;;
  -h | --help | help) usage ;;
  *)
    usage >&2
    exit 2
    ;;
esac
