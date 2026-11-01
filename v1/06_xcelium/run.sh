#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")/.."
exec python3 py/run_linux.py --sim xrun --tag xcelium "$@"
