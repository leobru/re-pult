#!/bin/sh
# Keep dispak's ~/.besm6 state inside the writable build directory.
# Usage: DISPAK=/path/to/dispak tools/run-dispak.sh [dispak options] job.b6
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
run_home="$root/build/dispak-home"
mkdir -p "$run_home"
exec env HOME="$run_home" "${DISPAK:-dispak}" "$@"
