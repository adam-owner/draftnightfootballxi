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


DEPTH_MAX_M = 300.0          # must match blender/bl_common.DEPTH_MAX_M


@lru_cache(maxsize=3)
def _depth(plate_dir, i, W, H):
    """Plate depth in metres, resized to the output frame, or None if no depth map was rendered."""
    import numpy as np
    from PIL import Image
    p = os.path.join(plate_dir, "depth_%04d.png" % i)
    if not os.path.exists(p):
        return None
    im = Image.open(p).resize((W, H), Image.NEAREST)
    a = np.asarray(im, dtype=np.float32)
    return a / (65535.0 if a.max() > 255 else 255.0) * DEPTH_MAX_M


def stand(cv, plate_dir, name, who, t, W, H, pose=None, tint=(255, 255, 255), flip=False, props=None, fps=30):
    """Draw a 2D character standing on 3D anchor `name`. Characters stay unlit like the reference
    shorts (tint only for special moods). If the plate has a depth map, any part of the character
    behind a nearer 3D object is hidden (true occlusion)."""
    at = anchor_at(plate_dir, name, t, W, H, fps)
    if not at:
        return False
    x, y, r, z = at
    if z <= 0.3 or r < 1.2 or y > H * 1.6 or x < -W * 0.3 or x > W * 1.3:
        return False
    depth = _depth(plate_dir, frame_index(plate_dir, t, fps), W, H)
    if depth is None:
        p = skia.Paint()
        p.setColorFilter(skia.ColorFilters.Blend(skia.Color(*tint), skia.BlendMode.kModulate))
        cv.saveLayer(None, p)
        draw_character(cv, who, x, y, r, pose or Pose(), flip=flip, props=props)
        cv.restore()
        return True
    import numpy as np
    # draw the character alone, then keep only pixels where the 3D scene is farther than the character
    x0, y0 = int(max(0, x - r * 2.2)), int(max(0, y - r * 5.6))
    x1, y1 = int(min(W, x + r * 2.2)), int(min(H, y + r * 0.6))
    if x1 <= x0 or y1 <= y0:
        return False
    surf = skia.Surface(x1 - x0, y1 - y0)
    c2 = surf.getCanvas(); c2.clear(skia.ColorTRANSPARENT); c2.translate(-x0, -y0)
    draw_character(c2, who, x, y, r, pose or Pose(), flip=flip, props=props)
    rgba = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType).copy()
    behind = depth[y0:y1, x0:x1] < (z - 0.4)          # 3D surface nearer than the character's depth
    rgba[behind] = 0
    if tint != (255, 255, 255):
        rgba[..., :3] = (rgba[..., :3].astype(np.uint16) * np.array(tint) // 255).astype(np.uint8)
    img = skia.Image.fromarray(rgba, colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kPremul_AlphaType)
    cv.drawImage(img, x0, y0)
    return True


def crowd(cv, plate_dir, t, W, H, cast, frozen=False, alert=0.0, tint=(255, 255, 255), fps=30, phone=None):
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
