#!/usr/bin/env bash
# Street plates for THE LAST 10 MINUTES (12 fps renders, interpolated to 30 fps afterwards).
set -euo pipefail
cd "$(dirname "$0")"
BPY=${BPY:-python3}
OUT=${1:-../out/the-last-10-minutes/plates}
SAMPLES=${SAMPLES:-20}
mkdir -p "$OUT"
# shot 2: 7.2 s busy avenue, camera push  -> 12 fps x 7.6 s = 92 frames
$BPY set_street_kenney.py -- "$OUT/s02" 92 540 960 $SAMPLES --fps 12 --cam push
# shot 3: 3.8 s, traffic brakes when the alert lands (~1.7 s)  -> 48 frames
$BPY set_street_kenney.py -- "$OUT/s03" 48 540 960 $SAMPLES --fps 12 --cam push --stop_at 1.7
# shot 5: the stopped street, closer camera, single frame (scene evaluated at the end of shot 3)
$BPY set_street_kenney.py -- "$OUT/s05" 48 540 960 $((SAMPLES + 12)) --fps 12 --cam close --stop_at 1.7 --still 48
echo "street plates done"
