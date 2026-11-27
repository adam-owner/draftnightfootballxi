"""
Composite 2D characters onto Blender-rendered 3D background plates (the reference shorts' look:
3D world, 2D cut-out characters).

A plate directory holds bg_0001.png ... and anchors.json written by blender/bl_common.export_anchors:
per frame, per anchor: [x 0..1, y 0..1 (top-left origin), pixels-per-metre at the anchor, camera depth].
"""
import json
import math
import os
from functools import lru_cache

import skia

from draw import Pose, draw_character, fill

CHAR_HEIGHT_M = 1.75        # a character's feet-to-hat height in the 3D world
HEADS_TALL = 4.65           # our 2D characters are ~4.65 head-radii tall (feet to top of head/hat)


@lru_cache(maxsize=8)
def anchors(plate_dir):
    with open(os.path.join(plate_dir, "anchors.json")) as f:
        return json.load(f)


@lru_cache(maxsize=4)
def _frame_count(plate_dir):
    return len([n for n in os.listdir(plate_dir) if n.startswith("bg_") and n.endswith(".png")])


def load_image(path):
    """skia.Image.MakeFromEncoded(bytes) can return None and then crash on draw; use the file loader."""
    img = skia.Image.open(path)
    if img is None:
        raise RuntimeError(f"could not load plate image {path}")
    return img


def frame_index(plate_dir, t, fps=30):
    n = _frame_count(plate_dir)
    return max(1, min(n, int(t * fps) + 1))


def draw_plate(cv, plate_dir, t, W, H, fps=30):
    i = frame_index(plate_dir, t, fps)
    img = load_image(os.path.join(plate_dir, "bg_%04d.png" % i))
    cv.drawImageRect(img, skia.Rect.MakeWH(img.width(), img.height()), skia.Rect.MakeWH(W, H),
                     skia.SamplingOptions(skia.CubicResampler.Mitchell()))
    return i


def anchor_at(plate_dir, name, t, W, H, fps=30):
    """Screen position (px), head radius (px) and depth for anchor `name` at time t."""
    a = anchors(plate_dir)
    fr = a["frames"][frame_index(plate_dir, t, fps) - 1]
    if name not in fr:
        return None
    x, y, ppm, z = fr[name]
    scale = H / a["H"]
    head_r = ppm * scale * CHAR_HEIGHT_M / HEADS_TALL
    return x * W, y * H, head_r, z


def stand(cv, plate_dir, name, who, t, W, H, pose=None, tint=(232, 234, 240), flip=False, props=None, fps=30):
    """Draw a 2D character standing on 3D anchor `name`, lit to match the plate (multiply tint)."""
    at = anchor_at(plate_dir, name, t, W, H, fps)
    if not at:
        return False
    x, y, r, z = at
    if z <= 0.3 or r < 1.2 or y > H * 1.6 or x < -W * 0.3 or x > W * 1.3:
        return False
    p = skia.Paint()
    p.setColorFilter(skia.ColorFilters.Blend(skia.Color(*tint), skia.BlendMode.kModulate))
    cv.saveLayer(None, p)
    draw_character(cv, who, x, y, r, pose or Pose(), flip=flip, props=props)
    cv.restore()
    return True


def crowd(cv, plate_dir, t, W, H, cast, frozen=False, alert=0.0, tint=(232, 234, 240), fps=30, phone=None):
    """All anchors named ped*: depth-sorted, walking toward (front view) or away (back view)."""
    a = anchors(plate_dir)
    fr = a["frames"][frame_index(plate_dir, t, fps) - 1]
    names = sorted([n for n in fr if n.startswith("ped")], key=lambda n: -fr[n][3])   # far first
    for k, n in enumerate(names):
        i = int(n[3:].split("_")[0])
        who, extra = cast[i % len(cast)]
        away = n.endswith("_away") and not frozen
        walk = None if frozen else t * 7.5 + i * 1.3
        sw = 0.25 * math.sin(walk) if walk else 0
        pose = Pose(walk=walk, bob=abs(math.sin(walk)) * 0.07 if walk else 0, back=away,
                    eyes="wide" if frozen else "dot", mouth="open" if frozen else "flat",
                    look=(0, 0.9) if frozen else (0, 0),
                    hand_r=(0.6, -2.5) if frozen else (1.2, -1.6 + sw), hand_l=(-1.2, -1.6 - sw), **extra)
        stand(cv, plate_dir, n, who, t, W, H, pose, tint=tint, flip=fr[n][0] > 0.5,
              props=[phone] if (frozen or alert) and phone else None, fps=fps)
