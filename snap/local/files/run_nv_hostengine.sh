#!/bin/bash
set -euo pipefail

# Build the argument list for the nv-hostengine command
args=()

# Add the nv-hostengine-port option if it is set
nv_hostengine_port="$(snapctl get nv-hostengine-port)"

if [ -n "$nv_hostengine_port" ]; then
    args+=("-p" "$nv_hostengine_port")
fi

# Check if dcgm-exporter service is running and restart it
# systemctl will not work in strict confinement
dcgm_exporter_status=$(snapctl services dcgm.dcgm-exporter | awk '/dcgm\.dcgm-exporter/ {print $3}')
if [ "$dcgm_exporter_status" == "active" ]; then
    snapctl restart dcgm.dcgm-exporter
fi

exec "$SNAP/usr/bin/nv-hostengine" -n --service-account nvidia-dcgm "${args[@]}"
