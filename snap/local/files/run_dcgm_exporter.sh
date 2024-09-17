#!/bin/bash
set -euo pipefail

# Build the argument list for the dcgm-exporter command
args=()

# Add the dcgm-exporter-address option if it is set. Default: “:9400”
dcgm_exporter_address="$(snapctl get dcgm-exporter-address)"

if [ -n "$dcgm_exporter_address" ]; then
    args+=("-a" "$dcgm_exporter_address")
fi

exec "$SNAP/bin/dcgm-exporter" "${args[@]}"
