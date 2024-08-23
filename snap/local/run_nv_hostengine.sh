#!/bin/bash

# Build the argument list for the nv-hostengine command
args=()

# Function to add options if they are set
add_option() {
    key=$1
    value="$(snapctl get "$key")"
    [ -n "$value" ] && args+=("-p" "$value")
}

add_option nv-hostengine-port

exec "$SNAP/usr/bin/nv-hostengine" -n --service-account nvidia-dcgm "${args[@]}"
