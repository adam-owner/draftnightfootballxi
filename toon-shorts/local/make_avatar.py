#!/usr/bin/env python3
"""TikTok profile picture: the half-turned grinning double. Writes 1080x1080 PNGs."""
import math, os, sys
import skia
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draw import Pose, draw_character, fill, glow, rad, stroke, text, font, INK

S = 1080
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "branding")


def base(cv):
    cv.drawRect(skia.Rect.MakeWH(S, S), fill((8, 4, 6)))
    cv.drawCircle(S / 2, S * 0.42, S * 0.62, rad((S / 2, S * 0.42), S * 0.62,
                  [((150, 14, 24), 255), ((70, 6, 12), 255), ((8, 4, 6), 255)], [0, 0.55, 1]))
    # thin hallway-light streaks behind the head
    for k in range(-3, 4):
        x = S / 2 + k * 120
        cv.drawRect(skia.Rect.MakeLTRB(x - 3, 0, x + 3, S), fill((255, 80, 90), 18))


def face(cv, cx, cy, r):
    turn = 0.72
    p = Pose(back=True, head_turn=turn, head_tilt=-14, eyes="creepy", mouth="creepy", grin=1.0, look=(0.3, 0.1))
    # draw_character puts feet at (x,y); the head centre is 3.55 head-radii above
    # the turning face is drawn shifted left by 1.9*(1-turn) head radii; re-centre it
    draw_character(cv, "double", cx + 1.9 * (1 - turn) * r * 0.55, cy + 3.55 * r, r, p)
    glow(cv, cx + r * 0.35, cy - r * 0.2, r * 1.4, (255, 60, 70), 50)


def ring(cv):
    cv.drawCircle(S / 2, S / 2, S / 2 - 14, stroke((230, 40, 50), 16))


def save(surf, name):
    path = os.path.join(OUT, name)
    surf.makeImageSnapshot().save(path, skia.kPNG)
    print(path)


# A: icon + name
surf = skia.Surface(S, S); cv = surf.getCanvas()
base(cv); face(cv, S / 2, S * 0.4, 255)
cv.drawRect(skia.Rect.MakeLTRB(0, S * 0.7, S, S), rad((S / 2, S * 1.05), S * 0.6, [((0, 0, 0), 235), ((0, 0, 0), 0)]))
text(cv, "WHAT WILL", S / 2, S * 0.79, 104, (255, 255, 255), 255, "black", "center")
text(cv, "YOU DO?", S / 2, S * 0.89, 104, (255, 60, 70), 255, "black", "center")
ring(cv); save(surf, "avatar_name.png")

# B: icon only (reads best at tiny sizes)
surf = skia.Surface(S, S); cv = surf.getCanvas()
base(cv); face(cv, S / 2, S * 0.5, 340)
ring(cv); save(surf, "avatar_icon.png")
