#!/usr/bin/env python3
"""Channel banners: YouTube (2560x1440, safe area 1546x423) and X (1500x500)."""
import os, sys
import skia
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draw import Pose, draw_character, fill, glow, lin, rad, stroke, text, font
from film_school import hallway
from sets import Cam

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "branding")
RED = (235, 45, 58)

# pre-render a hallway tile (720x1280 portrait) once
hs = skia.Surface(720, 1280); hc = hs.getCanvas()
hallway(hc, Cam(720, 1280, zoom=1.6, cy=1280 * 0.47), 720, 1280, 2.0, lights_dead_from=4)
draw_character(hc, "double", 720 * 0.44, 1280 * 0.6, 22, Pose(back=True, hand_l=(-0.95, -1.4), hand_r=(0.95, -1.4)))
glow(hc, 720 * 0.44, 1280 * 0.55, 90, (160, 190, 255), 70)
HALL = hs.makeImageSnapshot()


def banner(W, H, sx, sy, sw, sh, name, scale):
    """(sx, sy, sw, sh) = the safe rectangle that must hold all text."""
    surf = skia.Surface(W, H); cv = surf.getCanvas()
    cv.drawRect(skia.Rect.MakeWH(W, H), lin((0, 0), (W, 0), [(8, 8, 12), (22, 6, 10), (8, 8, 12)]))
    # hallway glimpses on both sides, fading in to the middle
    hw = sh * 2.2 * 0.5625
    for side in (0, 1):
        x = sx - hw * 0.55 if side == 0 else sx + sw - hw * 0.45
        dst = skia.Rect.MakeXYWH(x, sy + sh / 2 - sh * 1.1, hw, sh * 2.2)
        cv.saveLayer(dst, None)
        cv.drawImageRect(HALL, skia.Rect.MakeWH(720, 1280), dst, skia.SamplingOptions(skia.FilterMode.kLinear))
        # feather: keep the centre of the tile, fade every edge to nothing
        m = rad((dst.centerX(), dst.centerY()), max(dst.width(), dst.height()) * 0.5,
                [((0, 0, 0), 200), ((0, 0, 0), 120), ((0, 0, 0), 0)], [0, 0.55, 1])
        m.setBlendMode(skia.BlendMode.kDstIn)
        cv.save(); cv.translate(dst.centerX(), dst.centerY()); cv.scale(dst.width() / dst.height(), 1)
        cv.translate(-dst.centerX(), -dst.centerY())
        cv.drawRect(skia.Rect.MakeXYWH(dst.centerX() - dst.height(), dst.top(), dst.height() * 2, dst.height()), m)
        cv.restore()
        cv.restore()
    for edge in (0, 1):   # fade top/bottom
        cv.drawRect(skia.Rect.MakeXYWH(0, 0 if edge == 0 else H - H * 0.3, W, H * 0.3),
                    lin((0, 0 if edge == 0 else H), (0, H * 0.3 if edge == 0 else H - H * 0.3), [((8, 8, 12), 255), ((8, 8, 12), 0)]))
    cx = sx + sw / 2
    glow(cv, cx, sy + sh / 2, sw * 0.45, (200, 20, 40), 80)
    k = scale
    text(cv, "WHAT WILL YOU DO?", cx, sy + sh * 0.3, 118 * k, (255, 255, 255), 255, "black", "center")
    text(cv, "Interactive horror stories.  You choose.  Only two survive.", cx, sy + sh * 0.45,
         34 * k, (210, 210, 220), 255, "semi", "center")
    bw, bh, gap = 140 * k, 92 * k, 32 * k
    x0 = cx - (3 * bw + 2 * gap) / 2
    for i, l in enumerate("ABC"):
        r = skia.Rect.MakeXYWH(x0 + i * (bw + gap), sy + sh * 0.55, bw, bh)
        sel = l == "B"
        if sel:
            glow(cv, r.centerX(), r.centerY(), bw * 1.6, RED, 110)
        cv.drawRoundRect(r, 28 * k, 28 * k, fill(RED if sel else (34, 36, 46)))
        cv.drawRoundRect(r, 28 * k, 28 * k, stroke((255, 255, 255), 4 * k, 255 if sel else 70))
        text(cv, l, r.centerX(), r.centerY() + 26 * k, 72 * k, (255, 255, 255), 255 if sel else 160, "black", "center")
    text(cv, "NEW STORY EVERY WEEK", cx, sy + sh * 0.55 + bh + 46 * k, 26 * k, RED, 255, "bold", "center")
    p = os.path.join(OUT, name); surf.makeImageSnapshot().save(p, skia.kPNG); print(p)
    return p


yt = banner(2560, 1440, (2560 - 1546) / 2, (1440 - 423) / 2, 1546, 423, "banner_youtube.png", 1.0)
x = banner(1500, 500, 150, 60, 1200, 380, "banner_x.png", 0.85)
