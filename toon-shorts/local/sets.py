"""Reusable sets (locations) for the offline renderer, plus a parallax camera."""
import contextlib
import math
import random

import skia

from draw import (INK, beam, fill, fog_bank, glow, lerp, lighthouse, lin, path, puff, rad,
                  stars, stroke, outlined, lantern, fog_machine, soft_shadow)


class Cam:
    """2.5D camera: zoom/offset applied more strongly to near layers (parallax)."""

    def __init__(self, W, H, zoom=1.0, dx=0.0, dy=0.0, cx=None, cy=None):
        self.W, self.H = W, H
        self.zoom, self.dx, self.dy = zoom, dx, dy
        self.cx = W / 2 if cx is None else cx
        self.cy = H / 2 if cy is None else cy

    @contextlib.contextmanager
    def layer(self, cv, depth=1.0):
        s = 1 + (self.zoom - 1) * (0.25 + 0.75 * depth)
        cv.save()
        cv.translate(self.cx, self.cy)
        cv.scale(s, s)
        cv.translate(-self.cx + self.dx * (0.15 + 0.85 * depth), -self.cy + self.dy * (0.15 + 0.85 * depth))
        try:
            yield
        finally:
            cv.restore()


# ---------------------------------------------------------------- outdoor day
def sky_day(cv, W, H, t):
    cv.drawRect(skia.Rect.MakeWH(W, H), lin((0, 0), (0, H * 0.6), [(92, 168, 225), (190, 225, 245)]))
    glow(cv, W * 0.78, H * 0.12, 260, (255, 245, 210), 180)
    cv.drawCircle(W * 0.78, H * 0.12, 48, fill((255, 250, 225)))
    rnd = random.Random(5)
    for i in range(6):
        x = (rnd.uniform(0, W) + t * 6 * (1 + i % 3)) % (W + 300) - 150
        y = rnd.uniform(H * 0.05, H * 0.3)
        for k in range(5):
            puff(cv, x + k * 38 - 76, y + (12 if k in (0, 4) else 0), 70 - abs(k - 2) * 10, 200, (255, 255, 255))


def sea(cv, W, H, y, t, night=False):
    top, bot = ((22, 40, 78), (8, 16, 36)) if night else ((70, 140, 170), (30, 85, 120))
    cv.drawRect(skia.Rect.MakeLTRB(-W, y, 2 * W, H * 2), lin((0, y), (0, H), [top, bot]))
    hl = (90, 120, 170) if night else (200, 235, 245)
    for i in range(26):
        yy = y + (i / 26) ** 1.6 * (H - y) + 4
        amp = 2 + 6 * (yy - y) / max(1, H - y)
        pts = [(x, yy + math.sin(x * 0.03 + t * 1.6 + i) * amp) for x in range(-40, W + 60, 30)]
        cv.drawPath(path(pts, smooth=True), stroke(hl, 1.2 + 2.5 * (yy - y) / max(1, H - y), 70))


def gulls(cv, W, H, t, n=4, seed=2, y0=0.15, y1=0.35):
    rnd = random.Random(seed)
    for _ in range(n):
        cx, cy, r = rnd.uniform(0, W), rnd.uniform(H * y0, H * y1), rnd.uniform(40, 120)
        ph = rnd.uniform(0, 6)
        x = cx + math.cos(t * 0.6 + ph) * r
        y = cy + math.sin(t * 0.6 + ph) * r * 0.3
        f = math.sin(t * 9 + ph) * 6
        cv.drawPath(path([(x - 14, y - f), (x, y), (x + 14, y - f)], smooth=False), stroke(INK, 3))


def ship(cv, x, y, s, lights=0.0, night=False):
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    hull = path([(-1.2, -0.3), (1.25, -0.3), (1.0, 0.1), (-1.0, 0.1)], close=True)
    outlined(cv, hull, (30, 34, 40) if night else (180, 50, 45), 0.04)
    cv.drawRect(skia.Rect.MakeLTRB(-1.15, -0.32, 1.2, -0.22), fill((240, 240, 235) if not night else (60, 64, 70)))
    cab = skia.Rect.MakeLTRB(0.4, -0.75, 0.95, -0.3)
    cv.drawRect(cab, fill((235, 235, 228) if not night else (50, 54, 60)))
    cv.drawRect(cab, stroke(INK, 0.03))
    for i in range(3):
        cv.drawRect(skia.Rect.MakeXYWH(-0.9 + i * 0.42, -0.62, 0.36, 0.3), fill((60, 120, 160) if not night else (40, 46, 52)))
    cv.drawRect(skia.Rect.MakeLTRB(0.6, -1.05, 0.72, -0.75), fill((60, 60, 60)))
    if lights:
        for wx in (0.5, 0.68, 0.86):
            cv.drawRect(skia.Rect.MakeXYWH(wx - 0.05, -0.62, 0.1, 0.1), fill((255, 220, 140)))
            glow(cv, wx, -0.57, 0.25, (255, 210, 120), 120 * lights)
        glow(cv, -1.1, -0.35, 0.2, (255, 60, 60), 160 * lights)
    cv.restore()


def rocks(cv, x, y, w, h, seed=4, rgb=(96, 88, 84)):
    rnd = random.Random(seed)
    for i in range(7):
        rx = x + rnd.uniform(-0.5, 0.5) * w
        rw = rnd.uniform(0.25, 0.5) * w
        rh = rnd.uniform(0.4, 1.0) * h
        p = path([(rx - rw / 2, y), (rx - rw * 0.4, y - rh * 0.7), (rx - rw * 0.1, y - rh),
                  (rx + rw * 0.3, y - rh * 0.85), (rx + rw / 2, y)], close=True)
        shade = rnd.uniform(0.85, 1.1)
        outlined(cv, p, tuple(min(255, c * shade) for c in rgb), 2.5)
        cv.drawPath(path([(rx - rw * 0.1, y - rh), (rx - rw * 0.25, y - rh * 0.4)]), stroke((140, 130, 125), 2, 150))


def island(cv, x, y, s, t, lamp=0.0, second=0.0, night=False):
    """Gull Rock: base centre (x,y), s = island half-width px. Returns lamp pos(es)."""
    # rocks + turf
    rocks(cv, x, y + s * 0.04, s * 2.0, s * 0.35, rgb=(70, 66, 66) if night else (110, 100, 94))
    turf = skia.Path()
    turf.moveTo(x - s * 0.8, y - s * 0.2)
    turf.quadTo(x, y - s * 0.42, x + s * 0.85, y - s * 0.2)
    turf.lineTo(x + s * 0.7, y - s * 0.05); turf.lineTo(x - s * 0.7, y - s * 0.05); turf.close()
    outlined(cv, turf, (40, 70, 50) if night else (110, 160, 80), 2.5)
    # cottage
    cx, cy = x + s * 0.3, y - s * 0.27
    house = skia.Rect.MakeLTRB(cx - s * 0.14, cy - s * 0.16, cx + s * 0.14, cy)
    cv.drawRect(house, fill((235, 225, 205) if not night else (80, 80, 90)))
    cv.drawRect(house, stroke(INK, 2))
    roof = path([(cx - s * 0.18, cy - s * 0.15), (cx, cy - s * 0.28), (cx + s * 0.18, cy - s * 0.15)], close=True)
    outlined(cv, roof, (170, 60, 50) if not night else (70, 40, 40), 2)
    cv.drawRect(skia.Rect.MakeXYWH(cx - s * 0.04, cy - s * 0.1, s * 0.06, s * 0.06),
                fill((255, 210, 120) if night else (90, 140, 180)))
    # dock
    for i in range(5):
        px = x - s * 0.95 - i * s * 0.1
        cv.drawRect(skia.Rect.MakeXYWH(px, y - s * 0.07, s * 0.09, s * 0.03), fill((140, 100, 65)))
    lp = lighthouse(cv, x - s * 0.15, y - s * 0.3, s * 1.25, lamp)
    lp2 = None
    if second > 0:
        lp2 = lighthouse(cv, x + s * 0.65, y - s * 0.22, s * 1.05 * second, lamp=second if second > 0.95 else 0,
                         stripes=((60, 120, 200), (245, 245, 250)), new=True)
    return lp, lp2


# ------------------------------------------------------------------ night bay
def night_sky(cv, W, H, t, moon=(0.25, 0.14)):
    cv.drawRect(skia.Rect.MakeWH(W, H), lin((0, 0), (0, H * 0.55), [(10, 16, 40), (34, 50, 90)]))
    stars(cv, W, H, t, 140, H * 0.45)
    mx, my = W * moon[0], H * moon[1]
    glow(cv, mx, my, 170, (210, 220, 255), 110)
    cv.drawCircle(mx, my, 40, fill((245, 245, 230)))
    cv.drawCircle(mx + 10, my - 6, 8, fill((220, 220, 205)))


# ---------------------------------------------------------------- lamp room
def lamp_room(cv, cam, W, H, t, night=False, beam_ang=None, lens_x=0.62):
    with cam.layer(cv, 0.2):
        wall = ((120, 92, 70), (70, 50, 40)) if not night else ((60, 48, 52), (30, 24, 30))
        cv.drawRect(skia.Rect.MakeLTRB(-W, -H, 2 * W, 2 * H), lin((0, 0), (0, H), list(wall)))
        # round windows with view
        for wx in (0.18, 0.82):
            r = W * 0.17
            cx, cy = W * wx, H * 0.3
            win = skia.Path(); win.addCircle(cx, cy, r)
            cv.save(); cv.clipPath(win, doAntiAlias=True)
            if night:
                cv.drawRect(skia.Rect.MakeLTRB(cx - r, cy - r, cx + r, cy + r), lin((0, cy - r), (0, cy + r), [(12, 18, 44), (30, 46, 86)]))
                stars(cv, W, H, t, 30, H * 0.5, seed=int(wx * 10))
                if beam_ang is not None:
                    beam(cv, (cx - r * 1.5, cy), beam_ang, r * 3.2, r * 0.6, 150)
            else:
                cv.drawRect(skia.Rect.MakeLTRB(cx - r, cy - r, cx + r, cy + r), lin((0, cy - r), (0, cy + r), [(110, 180, 230), (200, 232, 248)]))
                cv.drawRect(skia.Rect.MakeLTRB(cx - r, cy + r * 0.25, cx + r, cy + r), fill((60, 130, 165)))
                ship(cv, cx + math.sin(t * 0.2) * r * 0.5, cy + r * 0.3, r * 0.12)
            cv.restore()
            cv.drawCircle(cx, cy, r, stroke((170, 130, 60), 14))
            cv.drawCircle(cx, cy, r, stroke(INK, 3))
            for a in range(8):
                ang = a * math.pi / 4
                cv.drawCircle(cx + math.cos(ang) * r, cy + math.sin(ang) * r, 4, fill((220, 190, 110)))
    with cam.layer(cv, 0.45):
        # floor
        cv.drawRect(skia.Rect.MakeLTRB(-W, H * 0.7, 2 * W, 2 * H), lin((0, H * 0.7), (0, H), [(110, 80, 55), (70, 48, 32)]))
        for i in range(-6, 14):
            cv.drawPath(path([(W / 2 + i * 50, H * 0.7), (W / 2 + i * 130, H * 1.1)]), stroke((60, 40, 25), 2, 120))
    with cam.layer(cv, 0.55):
        # giant fresnel lens
        lx, ly = W * lens_x, H * 0.5
        glow(cv, lx, ly, 330, (255, 220, 140), 120 if not night else 170)
        cv.drawRoundRect(skia.Rect.MakeLTRB(lx - 150, ly - 230, lx + 150, ly + 210), 60, 60,
                         lin((lx - 150, 0), (lx + 150, 0), [(255, 245, 215), (230, 210, 160), (255, 245, 215)]))
        for k in range(7):
            yy = ly - 200 + k * 60
            cv.drawPath(path([(lx - 140, yy), (lx, yy + 18), (lx + 140, yy)], smooth=True), stroke((200, 160, 80), 5, 200))
        cv.drawCircle(lx, ly, 70, rad((lx, ly), 70, [(255, 255, 240), (255, 230, 150)]))
        for k in range(4):
            cv.drawCircle(lx, ly, 70 + k * 18, stroke((210, 170, 90), 3, 180))
        cv.drawRoundRect(skia.Rect.MakeLTRB(lx - 150, ly - 230, lx + 150, ly + 210), 60, 60, stroke((150, 110, 50), 10))
        cv.drawRoundRect(skia.Rect.MakeLTRB(lx - 150, ly - 230, lx + 150, ly + 210), 60, 60, stroke(INK, 3))
        cv.drawRect(skia.Rect.MakeLTRB(lx - 120, ly + 210, lx + 120, H * 0.78), fill((120, 90, 40)))
        cv.drawRect(skia.Rect.MakeLTRB(lx - 120, ly + 210, lx + 120, H * 0.78), stroke(INK, 3))
        # glint
        g = (math.sin(t * 2.0) + 1) / 2
        cv.drawPath(path([(lx - 100, ly - 150), (lx - 60, ly - 190)]), stroke((255, 255, 255), 8, 120 + 100 * g))


def lamp_table(cv, W, H, t, x, y):
    cv.drawRect(skia.Rect.MakeLTRB(x - 110, y, x + 110, y + 16), fill((130, 85, 50)))
    cv.drawRect(skia.Rect.MakeLTRB(x - 110, y, x + 110, y + 16), stroke(INK, 3))
    for lx in (x - 95, x + 95):
        cv.drawRect(skia.Rect.MakeLTRB(lx - 6, y + 16, lx + 6, y + 150), fill((110, 70, 40)))
    # kettle
    k = skia.Path(); k.addOval(skia.Rect.MakeLTRB(x - 80, y - 60, x - 20, y))
    outlined(cv, k, (60, 110, 140), 3)
    cv.drawPath(path([(x - 22, y - 30), (x + 2, y - 50)]), stroke(INK, 6))
    for i in range(3):
        sy = y - 70 - ((t * 30 + i * 25) % 70)
        puff(cv, x + 4 + math.sin(t * 2 + i) * 6, sy, 12, 70)
    # mug
    m = skia.Rect.MakeLTRB(x + 20, y - 40, x + 52, y)
    cv.drawRect(m, fill((230, 230, 225))); cv.drawRect(m, stroke(INK, 3))


# ---------------------------------------------------------------- theatre
def theatre(cv, cam, W, H, t, spot=(0.5, 0.62), spot_on=1.0):
    with cam.layer(cv, 0.15):
        cv.drawRect(skia.Rect.MakeLTRB(-W, -H, 2 * W, 2 * H), lin((0, 0), (0, H), [(30, 22, 26), (14, 10, 14)]))
        # curtains
        for side in (-1, 1):
            for k in range(6):
                x0 = W / 2 + side * (W * 0.32 + k * 42)
                cv.drawRect(skia.Rect.MakeLTRB(x0 - 24, -50, x0 + 24, H * 0.8),
                            lin((x0 - 24, 0), (x0 + 24, 0), [(90, 10, 22), (170, 30, 45), (90, 10, 22)]))
        cv.drawRect(skia.Rect.MakeLTRB(-W, -50, 2 * W, H * 0.08), lin((0, 0), (0, H * 0.08), [(120, 15, 30), (160, 30, 45)]))
        # stacked props silhouettes
        for i, (px, pw, ph) in enumerate(((0.12, 90, 160), (0.24, 60, 220), (0.8, 120, 120), (0.9, 70, 260))):
            cv.drawRoundRect(skia.Rect.MakeXYWH(W * px - pw / 2, H * 0.62 - ph, pw, ph), 10, 10, fill((40, 32, 36)))
    with cam.layer(cv, 0.4):
        cv.drawRect(skia.Rect.MakeLTRB(-W, H * 0.62, 2 * W, 2 * H), lin((0, H * 0.62), (0, H), [(70, 50, 40), (40, 28, 24)]))
        sx, sy = W * spot[0], H * spot[1]
        if spot_on:
            cone = path([(sx - 40, -40), (sx + 40, -40), (sx + 240, sy), (sx - 240, sy)], close=True)
            pt = lin((0, 0), (0, sy), [((255, 240, 200), 30 * spot_on), ((255, 240, 200), 90 * spot_on)])
            pt.setBlendMode(skia.BlendMode.kPlus)
            cv.drawPath(cone, pt)
            cv.save(); cv.translate(sx, sy); cv.scale(1, 0.22)
            cv.drawCircle(0, 0, 250, rad((0, 0), 250, [((255, 235, 190), 120 * spot_on), ((255, 235, 190), 0)], blend=skia.BlendMode.kPlus))
            cv.restore()
            rnd = random.Random(9)
            for _ in range(40):
                yy = (rnd.uniform(0, sy) + t * rnd.uniform(4, 12)) % sy
                xx = sx + (rnd.uniform(-1, 1) * (40 + 200 * yy / sy)) + math.sin(t + yy) * 8
                cv.drawCircle(xx, yy, rnd.uniform(1, 2.6), fill((255, 240, 210), 160 * spot_on))


def sale_table(cv, x, y, w):
    top = skia.Rect.MakeLTRB(x - w / 2, y, x + w / 2, y + 18)
    cv.drawRect(top, fill((120, 80, 50))); cv.drawRect(top, stroke(INK, 3))
    cv.drawRect(skia.Rect.MakeLTRB(x - w / 2, y + 18, x + w / 2, y + 110), fill((150, 30, 40)))
    cv.drawRect(skia.Rect.MakeLTRB(x - w / 2, y + 18, x + w / 2, y + 110), stroke(INK, 3))
    # comedy mask, drum, a crown
    cv.drawOval(skia.Rect.MakeXYWH(x - w * 0.42, y - 52, 54, 52), fill((240, 220, 120)))
    cv.drawOval(skia.Rect.MakeXYWH(x - w * 0.42, y - 52, 54, 52), stroke(INK, 3))
    cv.drawRect(skia.Rect.MakeXYWH(x + w * 0.22, y - 50, 70, 50), fill((200, 60, 60)))
    cv.drawRect(skia.Rect.MakeXYWH(x + w * 0.22, y - 50, 70, 50), stroke(INK, 3))
    crown = path([(x - w * 0.2, y), (x - w * 0.2, y - 30), (x - w * 0.15, y - 15), (x - w * 0.1, y - 36),
                  (x - w * 0.05, y - 15), (x, y - 30), (x, y)], close=True)
    outlined(cv, crown, (230, 190, 60), 3)


# ----------------------------------------------------------- bridge & dock
def ship_bridge(cv, cam, W, H, t, beam_amt=0.0):
    with cam.layer(cv, 0.15):
        cv.drawRect(skia.Rect.MakeLTRB(-W, -H, 2 * W, 2 * H), fill((40, 28, 22)))
        win = skia.Rect.MakeLTRB(W * 0.05, H * 0.08, W * 0.95, H * 0.42)
        cv.save(); cv.clipRect(win)
        cv.drawRect(win, lin((0, win.top()), (0, win.bottom()), [(26, 34, 52), (60, 72, 90)]))
        fog_bank(cv, W, H, t, win.top(), win.bottom(), 18, 120, seed=11, speed=40, rmin=60, rmax=140)
        if beam_amt > 0:
            cv.drawRect(win, fill((255, 230, 160), 140 * beam_amt, blend=skia.BlendMode.kPlus))
        rnd = random.Random(12)
        for _ in range(70):
            x0 = rnd.uniform(win.left(), win.right())
            y0 = (rnd.uniform(win.top(), win.bottom()) + t * 420) % (win.height()) + win.top()
            cv.drawPath(path([(x0, y0), (x0 - 4, y0 + 18)]), stroke((180, 200, 230), 1.5, 120))
        cv.restore()
        cv.drawRect(win, stroke((90, 60, 40), 18))
        for fx in (0.35, 0.65):
            cv.drawRect(skia.Rect.MakeXYWH(W * fx - 8, win.top(), 16, win.height()), fill((90, 60, 40)))
        # wood planks
        for i in range(8):
            cv.drawPath(path([(0, H * 0.45 + i * 70), (W, H * 0.45 + i * 70)]), stroke((25, 16, 12), 3))
        # compass
        cv.drawCircle(W * 0.85, H * 0.5, 40, fill((200, 160, 70)))
        cv.drawCircle(W * 0.85, H * 0.5, 32, fill((240, 235, 220)))
        a = math.sin(t * 3) * 0.6
        cv.drawPath(path([(W * 0.85, H * 0.5), (W * 0.85 + math.sin(a) * 26, H * 0.5 - math.cos(a) * 26)]), stroke((200, 30, 30), 4))
    if beam_amt > 0:
        cv.drawRect(skia.Rect.MakeWH(W, H), fill((255, 220, 150), 50 * beam_amt, blend=skia.BlendMode.kPlus))


def ships_wheel(cv, x, y, r, ang):
    cv.save(); cv.translate(x, y); cv.rotate(ang)
    for k in range(8):
        a = k * math.pi / 4
        cv.drawPath(path([(0, 0), (math.cos(a) * r * 1.25, math.sin(a) * r * 1.25)]), stroke((120, 75, 40), r * 0.12))
        cv.drawCircle(math.cos(a) * r * 1.28, math.sin(a) * r * 1.28, r * 0.09, fill((120, 75, 40)))
    cv.drawCircle(0, 0, r, stroke((140, 90, 50), r * 0.16))
    cv.drawCircle(0, 0, r, stroke(INK, 3))
    cv.drawCircle(0, 0, r * 0.18, fill((200, 160, 70)))
    cv.restore()


def dock_night(cv, cam, W, H, t, mist=1.0, high=False):
    with cam.layer(cv, 0.1):
        night_sky(cv, W, H, t, moon=(0.78, 0.1))
        sea(cv, W, H, H * (0.2 if high else 0.38), t, night=True)
        island_far = H * (0.2 if high else 0.38)
        glow(cv, W * 0.2, island_far - 40, 60, (255, 200, 120), 100)
    with cam.layer(cv, 0.5):
        y0 = H * (0.45 if high else 0.58)
        deck = path([(-W * 0.2, H * 1.1), (W * 0.15, y0), (W * 0.85, y0), (W * 1.2, H * 1.1)], close=True)
        cv.drawPath(deck, lin((0, y0), (0, H), [(70, 50, 38), (110, 78, 52)]))
        for i in range(14):
            f = i / 14
            yy = y0 + (H * 1.1 - y0) * f ** 1.4
            xl = lerp(W * 0.15, -W * 0.2, f ** 1.4); xr = lerp(W * 0.85, W * 1.2, f ** 1.4)
            cv.drawPath(path([(xl, yy), (xr, yy)]), stroke((45, 30, 22), 2 + f * 3))
        cv.drawPath(deck, stroke(INK, 3))
        for px in (0.18, 0.82):
            cv.drawRect(skia.Rect.MakeLTRB(W * px - 10, y0 - 120, W * px + 10, y0 + 30), fill((80, 55, 38)))
            cv.drawRect(skia.Rect.MakeLTRB(W * px - 10, y0 - 120, W * px + 10, y0 + 30), stroke(INK, 3))
            lantern(cv, W * px, y0 - 122, 34, 1.0 + 0.1 * math.sin(t * 7 + px * 9))
        # crates + ropes
        for cx, cy, s in ((0.72, y0 + 120, 90), (0.83, y0 + 160, 70)):
            r = skia.Rect.MakeXYWH(W * cx - s / 2, cy - s, s, s)
            cv.drawRect(r, fill((150, 105, 60))); cv.drawRect(r, stroke(INK, 3))
            cv.drawPath(path([(r.left(), r.top()), (r.right(), r.bottom())]), stroke((110, 75, 40), 4))
        cv.save(); cv.translate(W * 0.26, y0 + 180); cv.scale(1, 0.4)
        for k in range(4):
            cv.drawCircle(0, 0, 30 + k * 7, stroke((190, 160, 110), 6))
        cv.restore()
    if mist:
        fog_bank(cv, W, H, t, H * 0.45, H * 0.9, 18, 55 * mist, seed=21, speed=12, rmin=90, rmax=200)
