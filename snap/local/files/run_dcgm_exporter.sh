#!/bin/bash
set -euo pipefail

# Build the argument list for the dcgm-exporter command
args=()

# Add the dcgm-exporter-address option if it is set.
dcgm_exporter_address="$(snapctl get dcgm-exporter-address)"
# Add the dcgm-exporter-metrics-file option if it is set.
dcgm_exporter_metrics_file_path="$SNAP_COMMON/$(snapctl get dcgm-exporter-metrics-file)"

if [ -n "$dcgm_exporter_address" ]; then
    args+=("-a" "$dcgm_exporter_address")
fi

# File should be available in the snap data directory under $SNAP_COMMON
if [[ -f "$dcgm_exporter_metrics_file_path" && -s "$dcgm_exporter_metrics_file_path" ]]; then
    args+=("-f" "$dcgm_exporter_metrics_file_path")
else
    echo "Error: DCGM exporter metrics file not found or empty: $dcgm_exporter_metrics_file_path"
    echo "DCGM exporter is falling back to the default metrics at $SNAP/etc/nvidia/dcgm-exporter/default-counters.csv"
fi

exec "$SNAP/bin/dcgm-exporter" "${args[@]}"
