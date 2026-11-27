#!/usr/bin/env bash
# Times Square, apartment and skyline plates for THE LAST 10 MINUTES (all single 3D frames;
# camera moves on them are done in 2D). Then normalise every plate directory.
set -euo pipefail
cd "$(dirname "$0")"
BPY=${BPY:-python3}
OUT=${1:-../out/the-last-10-minutes/plates}
S=${SAMPLES:-32}
$BPY set_times_square.py -- "$OUT/tsq_ads" 540 960 $S --variant ads
$BPY set_times_square.py -- "$OUT/tsq_alert" 540 960 $S --variant alert
$BPY set_apartment.py -- "$OUT/apt_wide_on" 540 960 $S --cam wide --lights on
$BPY set_apartment.py -- "$OUT/apt_wide_off" 540 960 $S --cam wide --lights off
$BPY set_apartment.py -- "$OUT/apt_close_on" 540 960 $S --cam close --lights on
$BPY set_apartment.py -- "$OUT/apt_window_off" 540 960 $S --cam window --lights off
$BPY set_street_kenney.py -- "$OUT/skyline" 2 540 960 $S --cam aerial --still 1
for d in tsq_ads tsq_alert apt_wide_on apt_wide_off apt_close_on apt_window_off skyline; do
  python3 finalize_plate.py "$OUT/$d" still 1
done
echo "rest plates done"
