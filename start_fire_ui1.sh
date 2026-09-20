#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
exec python3 fire_ui1_launch.py "$@"
