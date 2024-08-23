#!/bin/sh

PORT_FILE="$SNAP_DATA/dcgm_port"
DCGM_PORT=$(cat "$PORT_FILE")
echo "Running nv-hostengine on port: $DCGM_PORT"

# Run the nv-hostengine command with the determined port
exec $SNAP/usr/bin/nv-hostengine -n --service-account nvidia-dcgm -p "$DCGM_PORT"