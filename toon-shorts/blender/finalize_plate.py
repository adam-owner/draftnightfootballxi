#!/usr/bin/env python3
"""Normalise a rendered plate directory for the 2D compositor (runs with plain python3).

  finalize_plate.py DIR still FRAME   -> bg_0001.png, depth_0001.png, anchors.json reduced to that frame
  finalize_plate.py DIR anim          -> bg_####.png interpolated from the render fps to 30 fps
"""
import glob
import json
import os
import shutil
import subprocess
import sys

d, mode = sys.argv[1], sys.argv[2]
a = json.load(open(os.path.join(d, "anchors.json")))
if mode == "still":
    f = int(sys.argv[3])
    shutil.move(os.path.join(d, "still_%03d.png" % f), os.path.join(d, "bg_0001.png"))
    shutil.move(os.path.join(d, "depth_%04d.png" % f), os.path.join(d, "depth_0001.png"))
    idx = int(round((f - 1) / a.get("plate_fps", 30) * a["fps"]))
    a["frames"] = [a["frames"][min(idx, len(a["frames"]) - 1)]]
    a["still"] = True
    json.dump(a, open(os.path.join(d, "anchors.json"), "w"))
else:
    src = a.get("plate_fps", 30)
    if src != 30:
        tmp = os.path.join(d, "_src"); os.makedirs(tmp, exist_ok=True)
        for p in glob.glob(os.path.join(d, "bg_*.png")):
            shutil.move(p, tmp)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(src), "-i", os.path.join(tmp, "bg_%04d.png"),
                        "-vf", "minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1",
                        "-start_number", "1", os.path.join(d, "bg_%04d.png")], check=True)
        shutil.rmtree(tmp)
print("finalized", d, mode, len(glob.glob(os.path.join(d, "bg_*.png"))), "frames")
