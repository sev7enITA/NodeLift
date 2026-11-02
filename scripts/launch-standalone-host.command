#!/bin/zsh
# Start only this host instance. The session link stays in a private temporary file.
set -eu
bundle_dir=${0:A:h}
dashboard_port=${NODELIFT_DASHBOARD_PORT:-9868}
pairing_port=${NODELIFT_PAIRING_PORT:-9867}
host_address=${NODELIFT_HOST_ADDRESS:-auto}
state_dir=${NODELIFT_STATE_DIR:-"$HOME/.local/share/nodelift"}
if [[ ! "$dashboard_port" =~ '^[0-9]+$' || ! "$pairing_port" =~ '^[0-9]+$' ]]; then
  print -u2 'Invalid port configuration.'
  exit 1
fi
if /usr/sbin/lsof -nP -iTCP:"$dashboard_port" -sTCP:LISTEN >/dev/null 2>&1; then
  print -u2 'The dashboard port is already in use. Close the existing host before starting another.'
  exit 1
fi
umask 077
session_log=$(/usr/bin/mktemp "${TMPDIR:-/tmp}/nodelift-host-session.XXXXXXXX")
host_pid=''
cleanup() {
  if [[ -n "$host_pid" ]] && kill -0 "$host_pid" 2>/dev/null; then kill "$host_pid" 2>/dev/null || true; fi
  /bin/rm -f "$session_log"
}
trap cleanup EXIT INT TERM
"$bundle_dir/NodeLift-host" --address "$host_address" --port "$pairing_port" --dashboard-port "$dashboard_port" --state "$state_dir" >"$session_log" 2>&1 &
host_pid=$!
dashboard_url=''
for attempt in {1..300}; do
  dashboard_url=$(/usr/bin/sed -nE 's/^Dashboard \(local, private link\): (http:\/\/127\.0\.0\.1:[0-9]+\/#[A-Za-z0-9_-]+)$/\1/p' "$session_log" | /usr/bin/tail -n 1)
  [[ -n "$dashboard_url" ]] && break
  if ! kill -0 "$host_pid" 2>/dev/null; then
    print -u2 'NodeLift did not start. Run NodeLift-host --self-check for diagnostic status.'
    exit 1
  fi
  /bin/sleep 0.2
done
if [[ -z "$dashboard_url" ]]; then
  print -u2 'NodeLift did not become ready within one minute.'
  exit 1
fi
print 'NodeLift is running. Keep this window open while using the dashboard.'
if [[ "${NODELIFT_OPEN_DASHBOARD:-1}" == 1 ]]; then /usr/bin/open "$dashboard_url"; fi
wait "$host_pid"
