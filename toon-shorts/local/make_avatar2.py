#!/usr/bin/env python3
"""Alternative TikTok profile-picture concepts (1080x1080)."""
import math, os, sys
import skia
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draw import Pose, draw_character, fill, glow, lin, rad, stroke, text, font, path, INK
from film_school import Hall, hallway, heart
from sets import Cam

S = 1080
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "branding")
RED = (235, 45, 58)


def new():
    surf = skia.Surface(S, S); return surf, surf.getCanvas()


def save(surf, name):
    p = os.path.join(OUT, name); surf.makeImageSnapshot().save(p, skia.kPNG); print(p)


# 1. the text message -----------------------------------------------------------
surf, cv = new()
cv.drawRect(skia.Rect.MakeWH(S, S), lin((0, 0), (0, S), [(18, 18, 26), (6, 6, 10)]))
glow(cv, S / 2, S / 2, S * 0.6, (200, 30, 50), 70)
cv.drawCircle(S / 2, 300, 82, fill((70, 70, 80)))
text(cv, "?", S / 2, 336, 104, (255, 255, 255), 255, "black", "center")
text(cv, "UNKNOWN", S / 2, 450, 46, (200, 200, 210), 255, "bold", "center")
b = skia.Rect.MakeLTRB(150, 520, 930, 790)
cv.drawRoundRect(b, 70, 70, fill((60, 60, 68)))
tail = path([(190, 760), (150, 830), (260, 780)], close=True); cv.drawPath(tail, fill((60, 60, 68)))
text(cv, "What will", S / 2, 640, 96, (255, 255, 255), 255, "bold", "center")
text(cv, "you do?", S / 2, 750, 96, RED, 255, "bold", "center")
text(cv, "11:47 PM", S / 2, 870, 40, (140, 140, 150), 255, "semi", "center")
save(surf, "avatar_text.png")

# 2. the choice -----------------------------------------------------------------
surf, cv = new()
cv.drawRect(skia.Rect.MakeWH(S, S), fill((10, 10, 14)))
for i, l in enumerate("ABC"):
    y = 210 + i * 230
    sel = (l == "B")
    r = skia.Rect.MakeXYWH(170, y, 740, 180)
    if sel:
        glow(cv, S / 2, y + 90, 520, RED, 110)
    cv.drawRoundRect(r, 50, 50, fill(RED if sel else (34, 36, 46)))
    cv.drawRoundRect(r, 50, 50, stroke((255, 255, 255), 6, 255 if sel else 60))
    text(cv, l, S / 2, y + 128, 140, (255, 255, 255), 255 if sel else 150, "black", "center")
# cursor/finger tap on B
cx, cy = 760, 480
cv.drawCircle(cx, cy, 46, stroke((255, 255, 255), 8, 200))
cv.drawCircle(cx, cy, 18, fill((255, 255, 255)))
save(surf, "avatar_choice.png")

# 3. the hallway ----------------------------------------------------------------
surf, cv = new()
cv.save(); cv.translate(0, -(1280 - S) * 0.45)
hl = hallway(cv, Cam(720, 1280, zoom=1.9, cy=1280 * 0.47), 720, 1280, 2.0, lights_dead_from=4)
cv.restore()
# hallway was drawn for 720x1280; stretch onto the square
img = surf.makeImageSnapshot()
surf, cv = new()
cv.drawImageRect(img, skia.Rect.MakeXYWH(0, 0, 720, 720 * 1.0), skia.Rect.MakeWH(S, S), skia.SamplingOptions(skia.FilterMode.kLinear))
draw_character(cv, "double", S * 0.44, S * 0.845, 32, Pose(back=True, hand_l=(-0.95, -1.4), hand_r=(0.95, -1.4)))
glow(cv, S * 0.44, S * 0.77, 140, (160, 190, 255), 70)
cv.drawRect(skia.Rect.MakeWH(S, S), rad((S / 2, S / 2), S * 0.75, [((0, 0, 0), 0), ((0, 0, 0), 0), ((0, 0, 0), 230)], [0, 0.45, 1]))
save(surf, "avatar_hallway.png")

# 4. the monogram ---------------------------------------------------------------
surf, cv = new()
cv.drawRect(skia.Rect.MakeWH(S, S), lin((0, 0), (S, S), [(150, 14, 26), (40, 4, 10)]))
text(cv, "WW", S / 2, 520, 300, (255, 255, 255), 255, "black", "center")
f = font(300, "black")
w_yd, w_q = f.measureText("YD"), f.measureText("?")
x0 = S / 2 - (w_yd + 40 + w_q) / 2
text(cv, "YD", x0, 820, 300, (255, 255, 255), 255, "black")
text(cv, "?", x0 + w_yd + 40, 820, 300, (255, 70, 80), 255, "black")
save(surf, "avatar_monogram.png")
