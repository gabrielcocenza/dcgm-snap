#!/bin/bash
set -euo pipefail

# Build the argument list for the nv-hostengine command
args=()

# Add the nv-hostengine-port option if it is set
nv_hostengine_port="$(snapctl get nv-hostengine-port)"

if [ -n "$nv_hostengine_port" ]; then
    args+=("-p" "$nv_hostengine_port")
fi

exec "$SNAP/usr/bin/nv-hostengine" -n --service-account nvidia-dcgm "${args[@]}"
