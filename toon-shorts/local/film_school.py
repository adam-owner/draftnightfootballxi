"""
"The School That Texted Back" - interactive horror episode (stories/school-texted-back.json).
SHOTS[id](cv, W, H, t, T, shot): shot carries "line_times" = [(start, end, who, bubble)].
"""
import math
import random

import skia

from draw import (INK, Pose, clamp01, draw_character, ease, fill, glow, grain_vignette, lerp, lin, outlined,
                  path, puff, rad, soft_shadow, stroke, text, font, wrap)
from sets import Cam

BLUE_NIGHT = (14, 22, 44)


def flicker(t, seed, rate=1.0, dead=False):
    """Fluorescent flicker 0..1; mostly on, with stutters."""
    rnd = random.Random(seed)
    ph = rnd.uniform(0, 10)
    base = 0.85 + 0.15 * math.sin(t * 60 + ph)
    if dead:
        return 0.08
    k = math.sin(t * 2.3 * rate + ph) * math.sin(t * 5.7 * rate + ph * 2)
    if k > 0.82:
        return 0.15
    return base


# ============================================================ CLASSROOM
def classroom(cv, cam, W, H, t, lights=0.0):
    with cam.layer(cv, 0.2):
        cv.drawRect(skia.Rect.MakeLTRB(-W, -H, 2 * W, 2 * H), lin((0, 0), (0, H), [(22, 30, 52), (10, 14, 26)]))
        # tall windows with moonlight
        for i in range(3):
            x0 = W * (0.08 + i * 0.3)
            win = skia.Rect.MakeXYWH(x0, H * 0.1, W * 0.22, H * 0.34)
            cv.drawRect(win, lin((0, win.top()), (0, win.bottom()), [(40, 60, 110), (70, 95, 150)]))
            cv.drawRect(skia.Rect.MakeXYWH(x0 + W * 0.105, win.top(), 6, win.height()), fill((20, 26, 44)))
            cv.drawRect(skia.Rect.MakeXYWH(x0, H * 0.27, W * 0.22, 6), fill((20, 26, 44)))
            cv.drawRect(win, stroke((20, 26, 44), 10))
        glow(cv, W * 0.75, H * 0.16, 70, (220, 230, 255), 140)
        cv.drawCircle(W * 0.75, H * 0.16, 22, fill((240, 245, 255)))
        # clock 11:47
        draw_clock(cv, W * 0.5, H * 0.06 + 40, 34, glow_a=0)
        # moonlight shafts on floor
        for i in range(3):
            x0 = W * (0.08 + i * 0.3)
            p = path([(x0, H * 0.44), (x0 + W * 0.22, H * 0.44), (x0 + W * 0.5, H * 0.95), (x0 + W * 0.1, H * 0.95)], close=True)
            pt = lin((0, H * 0.44), (0, H * 0.95), [((120, 150, 220), 50), ((120, 150, 220), 0)])
            pt.setBlendMode(skia.BlendMode.kPlus)
            cv.drawPath(p, pt)
    with cam.layer(cv, 0.45):
        cv.drawRect(skia.Rect.MakeLTRB(-W, H * 0.55, 2 * W, 2 * H), lin((0, H * 0.55), (0, H), [(30, 32, 44), (16, 18, 26)]))
        # back row desks
        for i in range(4):
            desk(cv, W * (0.12 + i * 0.26), H * 0.6, 80)


def desk(cv, x, y, w):
    top = skia.Rect.MakeLTRB(x - w, y - 10, x + w, y + 6)
    cv.drawRect(top, fill((90, 70, 52))); cv.drawRect(top, stroke(INK, 3))
    for lx in (x - w * 0.85, x + w * 0.85):
        cv.drawRect(skia.Rect.MakeLTRB(lx - 4, y + 6, lx + 4, y + w * 0.9), fill((60, 62, 70)))


def draw_clock(cv, x, y, r, glow_a=80, hh=11, mm=47, wobble=0.0):
    if glow_a:
        glow(cv, x, y, r * 2.5, (230, 240, 255), glow_a)
    cv.drawCircle(x, y, r, fill((235, 235, 228)))
    cv.drawCircle(x, y, r, stroke(INK, max(2, r * 0.12)))
    for k in range(12):
        a = k * math.pi / 6
        cv.drawPath(path([(x + math.cos(a) * r * 0.8, y + math.sin(a) * r * 0.8),
                          (x + math.cos(a) * r * 0.92, y + math.sin(a) * r * 0.92)]), stroke(INK, max(1, r * 0.05)))
    am = (mm / 60) * 2 * math.pi - math.pi / 2 + wobble
    ah = ((hh % 12 + mm / 60) / 12) * 2 * math.pi - math.pi / 2
    cv.drawPath(path([(x, y), (x + math.cos(ah) * r * 0.5, y + math.sin(ah) * r * 0.5)]), stroke(INK, max(2, r * 0.1)))
    cv.drawPath(path([(x, y), (x + math.cos(am) * r * 0.78, y + math.sin(am) * r * 0.78)]), stroke(INK, max(1.5, r * 0.06)))
    cv.drawCircle(x, y, max(2, r * 0.07), fill((200, 30, 30)))


# ============================================================ HALLWAY
class Hall:
    """One-point-perspective hallway. z=1 is the camera plane, z->ZEND is the far wall."""
    ZEND = 0.13

    def __init__(self, W, H, vx=None, vy=None):
        self.W, self.H = W, H
        self.vx = W / 2 if vx is None else vx
        self.vy = H * 0.45 if vy is None else vy
        self.hw = W * 0.8          # half width at z=1
        self.fy = H * 0.62         # floor offset at z=1
        self.cy = -H * 0.5         # ceiling offset

    def p(self, X, Y, z):
        return (self.vx + X * z, self.vy + Y * z)


def hallway(cv, cam, W, H, t, lights_dead_from=None, lights_off=0.0, seed=1):
    hl = Hall(W, H)
    Z = hl.ZEND
    with cam.layer(cv, 0.6):
        cv.drawRect(skia.Rect.MakeLTRB(-W, -H, 2 * W, 2 * H), fill((8, 10, 18)))
        # floor, ceiling, walls
        fl = path([hl.p(-hl.hw, hl.fy, 1.3), hl.p(hl.hw, hl.fy, 1.3), hl.p(hl.hw, hl.fy, Z), hl.p(-hl.hw, hl.fy, Z)], close=True)
        cv.drawPath(fl, lin(hl.p(0, hl.fy, 1.3), hl.p(0, hl.fy, Z), [(48, 54, 66), (20, 24, 34)]))
        # floor tiles
        for k in range(1, 18):
            z = Z + (1.3 - Z) * (k / 18) ** 2
            cv.drawPath(path([hl.p(-hl.hw, hl.fy, z), hl.p(hl.hw, hl.fy, z)]), stroke((28, 32, 42), 1 + 2 * z))
        for X in (-0.5, 0, 0.5):
            cv.drawPath(path([hl.p(hl.hw * X, hl.fy, 1.3), hl.p(hl.hw * X, hl.fy, Z)]), stroke((28, 32, 42), 2))
        ce = path([hl.p(-hl.hw, hl.cy, 1.3), hl.p(hl.hw, hl.cy, 1.3), hl.p(hl.hw, hl.cy, Z), hl.p(-hl.hw, hl.cy, Z)], close=True)
        cv.drawPath(ce, fill((22, 24, 32)))
        for side in (-1, 1):
            wall = path([hl.p(side * hl.hw, hl.cy, 1.3), hl.p(side * hl.hw, hl.fy, 1.3),
                         hl.p(side * hl.hw, hl.fy, Z), hl.p(side * hl.hw, hl.cy, Z)], close=True)
            cv.drawPath(wall, lin(hl.p(side * hl.hw, 0, 1.3), hl.p(side * hl.hw, 0, Z), [(44, 58, 78), (18, 22, 34)]))
        # end wall + stairs going up on the right
        end = skia.Rect.MakeLTRB(*hl.p(-hl.hw, hl.cy, Z), *hl.p(hl.hw, hl.fy, Z))
        cv.drawRect(end, fill((26, 30, 42)))
        ex0, ey0 = hl.p(hl.hw * 0.25, hl.fy, Z)
        for k in range(7):
            sx = ex0 + k * 9; sy = ey0 - k * 11
            cv.drawRect(skia.Rect.MakeLTRB(sx, sy - 11, ex0 + 70, sy), fill((40 - k * 3, 44 - k * 3, 58 - k * 3)))
        cv.drawRect(skia.Rect.MakeLTRB(ex0 - 4, ey0 - 90, ex0 + 70, ey0), stroke((15, 18, 26), 2))
        # exit sign
        sx, sy = hl.p(-hl.hw * 0.35, hl.cy * 0.6, Z)
        glow(cv, sx, sy, 60, (255, 40, 40), 170)
        cv.drawRect(skia.Rect.MakeXYWH(sx - 22, sy - 8, 44, 16), fill((220, 30, 30)))
        text(cv, "EXIT", sx, sy + 5, 12, (255, 220, 220), align="center")
        # lockers + open doors on both walls
        zs = [Z + (1.25 - Z) * (k / 22) ** 1.7 for k in range(23)]
        for side in (-1, 1):
            for k in range(22):
                z0, z1 = zs[k], zs[k + 1]
                is_door = k in (4, 9, 14, 18) if side < 0 else k in (6, 11, 16, 20)
                xw = side * hl.hw
                top, bot = hl.cy * 0.55, hl.fy * 0.98
                q = path([hl.p(xw, top, z0), hl.p(xw, top, z1), hl.p(xw, bot, z1), hl.p(xw, bot, z0)], close=True)
                if is_door:
                    cv.drawPath(q, fill((4, 5, 9)))
                    # door panel swung into the hall
                    hx, hy0 = hl.p(xw, top, z1)
                    _, hy1 = hl.p(xw, bot, z1)
                    ox = hx - side * (hl.hw * 0.28) * z1
                    door = path([(hx, hy0), (ox, hy0 + 4 * z1), (ox, hy1 - 4 * z1), (hx, hy1)], close=True)
                    outlined(cv, door, (70, 56, 46), 2)
                    cv.drawCircle(ox + side * 6 * z1, (hy0 + hy1) / 2, 3 * z1 + 1, fill((180, 170, 120)))
                else:
                    shade = 0.9 + 0.1 * (k % 2)
                    cv.drawPath(q, fill(tuple(int(c * shade) for c in (52, 82, 110))))
                    cv.drawPath(q, stroke((20, 30, 44), 1 + 1.5 * z1))
                    vx_, vy_ = hl.p(xw, top + 30, (z0 + z1) / 2)
                    for v in range(3):
                        cv.drawPath(path([(vx_, vy_ + v * 6 * z1), (vx_ + side * -8 * z1, vy_ + v * 6 * z1)]), stroke((20, 30, 44), 1))
            # clocks on the walls, all 11:47
            for zc in (0.95, 0.55, 0.33):
                cx, cyy = hl.p(side * hl.hw * 0.985, hl.cy * 0.75, zc)
                cv.save(); cv.translate(cx, cyy); cv.scale(0.55, 1)
                draw_clock(cv, 0, 0, 46 * zc, glow_a=60 * zc)
                cv.restore()
    # ceiling lights + floor pools
    lzs = [0.95, 0.62, 0.42, 0.3, 0.22, 0.17]
    for i, z in enumerate(lzs):
        on = flicker(t, seed + i)
        if lights_dead_from is not None and i >= lights_dead_from:
            on = 0.05
        if lights_off:
            # lights die from far to near
            if (len(lzs) - i) / len(lzs) <= lights_off:
                on = 0.04
        with cam.layer(cv, 0.6):
            a = hl.p(-hl.hw * 0.25, hl.cy * 0.98, z); b = hl.p(hl.hw * 0.25, hl.cy * 0.98, z * 0.93)
            tube = skia.Rect.MakeLTRB(a[0], a[1], b[0], b[1] + 10 * z)
            cv.drawRect(tube, fill((230, 240, 255) if on > 0.5 else (60, 64, 72)))
            if on > 0.3:
                glow(cv, (a[0] + b[0]) / 2, a[1], 180 * z, (200, 220, 255), 110 * on)
                fx, fy = hl.p(0, hl.fy, z)
                cv.save(); cv.translate(fx, fy); cv.scale(1, 0.25)
                cv.drawCircle(0, 0, hl.hw * 0.7 * z, rad((0, 0), hl.hw * 0.7 * z, [((170, 200, 255), 70 * on), ((170, 200, 255), 0)],
                                                         blend=skia.BlendMode.kPlus))
                cv.restore()
    return hl


# ============================================================ HOME LANDING
def landing(cv, cam, W, H, t, handle=0.0, shadow=0.0):
    with cam.layer(cv, 0.3):
        cv.drawRect(skia.Rect.MakeLTRB(-W, -H, 2 * W, 2 * H), lin((0, 0), (0, H), [(40, 30, 34), (20, 14, 18)]))
        # wallpaper stripes
        for i in range(-6, 20):
            cv.drawRect(skia.Rect.MakeXYWH(i * 60, -H, 20, 3 * H), fill((48, 36, 40)))
        # framed photos
        for i, (px, py) in enumerate(((0.12, 0.25), (0.2, 0.4), (0.85, 0.3))):
            r = skia.Rect.MakeXYWH(W * px - 40, H * py - 50, 80, 100)
            cv.drawRect(r, fill((180, 150, 110))); cv.drawRect(r.makeInset(8, 8), fill((70, 80, 100)))
            cv.drawCircle(r.centerX(), r.centerY() - 8, 14, fill((230, 228, 220)))
        # bedroom door
        door = skia.Rect.MakeLTRB(W * 0.42, H * 0.2, W * 0.78, H * 0.78)
        cv.drawRect(door.makeOutset(14, 14), fill((60, 44, 34)))
        cv.drawRect(door, lin((door.left(), 0), (door.right(), 0), [(120, 90, 66), (96, 70, 52)]))
        for r in (skia.Rect.MakeLTRB(door.left() + 26, door.top() + 30, door.right() - 26, door.top() + 230),
                  skia.Rect.MakeLTRB(door.left() + 26, door.top() + 270, door.right() - 26, door.bottom() - 40)):
            cv.drawRect(r, stroke((80, 58, 42), 5))
        cv.drawRect(door, stroke(INK, 4))
        # light under the door + passing shadow
        strip = skia.Rect.MakeLTRB(door.left(), door.bottom() - 6, door.right(), door.bottom() + 2)
        cv.drawRect(strip, fill((255, 210, 140)))
        glow(cv, door.centerX(), door.bottom() + 10, 160, (255, 200, 120), 120)
        if shadow:
            sx = lerp(door.left() - 80, door.right() + 80, shadow)
            cv.drawRect(skia.Rect.MakeLTRB(sx - 50, door.bottom() - 8, sx + 50, door.bottom() + 30), fill((10, 6, 6), 230))
        # handle
        hx, hy = door.right() - 40, door.centerY()
        cv.save(); cv.translate(hx, hy); cv.rotate(-35 * handle)
        cv.drawRoundRect(skia.Rect.MakeLTRB(-34, -7, 6, 7), 6, 6, fill((200, 170, 90)))
        cv.drawRoundRect(skia.Rect.MakeLTRB(-34, -7, 6, 7), 6, 6, stroke(INK, 2))
        cv.restore()
        cv.drawCircle(hx, hy, 12, fill((200, 170, 90))); cv.drawCircle(hx, hy, 12, stroke(INK, 2))
        # nightlight
        glow(cv, W * 0.2, H * 0.72, 90, (140, 200, 255), 110)
        cv.drawRect(skia.Rect.MakeLTRB(-W, H * 0.8, 2 * W, 2 * H), lin((0, H * 0.8), (0, H), [(60, 40, 40), (30, 20, 20)]))


# ============================================================ PHONE UI
def heart(cv, x, y, s, rgb=(255, 59, 92)):
    p = skia.Path()
    p.moveTo(x, y + s * 0.35)
    p.cubicTo(x - s * 1.1, y - s * 0.35, x - s * 0.45, y - s * 1.0, x, y - s * 0.4)
    p.cubicTo(x + s * 0.45, y - s * 1.0, x + s * 1.1, y - s * 0.35, x, y + s * 0.35)
    cv.drawPath(p, fill(rgb))


def phone_frame(cv, W, H, t, shake=0.0, bg=None):
    """Hand-held phone filling most of the frame. Returns screen rect."""
    if bg:
        bg()
    cv.drawRect(skia.Rect.MakeWH(W, H), fill((0, 0, 0), 120))
    sx = math.sin(t * 90) * 6 * shake
    cv.save()  # balanced by end_phone()
    cv.translate(sx, 0); cv.rotate(-2 + math.sin(t * 0.8) * 0.6)
    body = skia.Rect.MakeLTRB(W * 0.07, H * 0.1, W * 0.93, H * 0.98)
    soft_shadow(cv, W / 2, H * 0.98, W * 0.5, 40, 160)
    cv.drawRoundRect(body, 60, 60, fill((24, 24, 28)))
    cv.drawRoundRect(body, 60, 60, stroke((70, 70, 78), 4))
    scr = body.makeInset(16, 16)
    cv.drawRoundRect(scr, 46, 46, fill((0, 0, 0)))
    glow(cv, W / 2, H * 0.5, W * 0.8, (120, 140, 200), 40)
    # notch
    cv.drawRoundRect(skia.Rect.MakeXYWH(W / 2 - 60, scr.top() + 12, 120, 28), 14, 14, fill((10, 10, 12)))
    # thumb
    th = skia.Path(); th.addOval(skia.Rect.MakeLTRB(W * 0.82, H * 0.72, W * 1.05, H * 1.05))
    cv.drawPath(th, fill((250, 248, 242))); cv.drawPath(th, stroke(INK, 5))
    return scr, sx


def end_phone(cv):
    cv.restore()


def lock_screen(cv, W, H, t, T, shot):
    def bg():
        cv.drawRect(skia.Rect.MakeWH(W, H), fill(BLUE_NIGHT))
    scr, _ = phone_frame(cv, W, H, t, bg=bg)
    cv.save(); cv.clipRRect(skia.RRect.MakeRectXY(scr, 46, 46), doAntiAlias=True)
    cv.drawRect(scr, lin((0, scr.top()), (0, scr.bottom()), [(20, 30, 70), (60, 20, 60)]))
    text(cv, "Tuesday, 14 November", W / 2, scr.top() + 170, 30, (230, 230, 240), 220, "semi", "center")
    text(cv, "11:47", W / 2, scr.top() + 330, 150, (255, 255, 255), 245, "bold", "center")
    glow(cv, W / 2, scr.top() + 270, 260, (180, 200, 255), 50)
    text(cv, "PM", W / 2, scr.top() + 390, 34, (230, 230, 240), 200, "semi", "center")
    # battery low
    text(cv, "3%", scr.right() - 60, scr.top() + 32, 22, (255, 80, 80), 255, "semi", "right")
    cv.restore()
    end_phone(cv)


def messages(cv, W, H, t, T, shot):
    ph = shot.get("phone", {})
    lt = [x for x in shot.get("line_times", []) if x[3]]
    first = lt[0][0] if lt else 0
    buzz = clamp01(1 - abs(t - max(0, first - 0.3)) / 0.35)

    def bg():
        cv.drawRect(skia.Rect.MakeWH(W, H), fill(BLUE_NIGHT))
    scr, _ = phone_frame(cv, W, H, t, shake=buzz, bg=bg)
    cv.save(); cv.clipRRect(skia.RRect.MakeRectXY(scr, 46, 46), doAntiAlias=True)
    cv.drawRect(scr, fill((10, 10, 12)))
    # status bar
    text(cv, ph.get("time", "11:48 PM").replace(" PM", ""), scr.left() + 50, scr.top() + 32, 22, (255, 255, 255), 255, "semi")
    text(cv, "3%", scr.right() - 50, scr.top() + 32, 22, (255, 80, 80), 255, "semi", "right")
    # header
    hy = scr.top() + 120
    unknown = ph.get("contact", "").startswith("UNKNOWN")
    cv.drawCircle(W / 2, hy, 40, fill((80, 80, 90) if unknown else (240, 120, 150)))
    text(cv, "?" if unknown else "M", W / 2, hy + 14, 40, (255, 255, 255), 255, "bold", "center")
    name = ph.get("contact", "MOM")
    w = font(28, "semi").measureText(name)
    text(cv, name, W / 2 - (14 if ph.get("heart") else 0), hy + 80, 28, (255, 255, 255), 255, "semi", "center")
    if ph.get("heart"):
        heart(cv, W / 2 + w / 2 + 2, hy + 70, 13)
    cv.drawRect(skia.Rect.MakeLTRB(scr.left(), hy + 105, scr.right(), hy + 107), fill((40, 40, 46)))
    # timestamp
    text(cv, ph.get("time", ""), W / 2, hy + 150, 20, (140, 140, 150), 255, "semi", "center")
    # bubbles (grey, left), appear at their line start; typing dots just before
    y = hy + 180
    f = font(29, "reg")
    bubble_w = scr.width() * 0.72
    shown = [x for x in lt if t >= x[0] - 0.05]
    for (st, en, who, txt) in shown:
        lines = wrap(txt, f, bubble_w - 44)
        bh = 22 + 38 * len(lines)
        pop = ease(clamp01((t - st + 0.05) / 0.18))
        r = skia.Rect.MakeXYWH(scr.left() + 28, y, min(bubble_w, max(f.measureText(l) for l in lines) + 44), bh)
        cv.save(); cv.translate(r.left(), r.bottom()); cv.scale(0.8 + 0.2 * pop, 0.8 + 0.2 * pop); cv.translate(-r.left(), -r.bottom())
        red = unknown or "WHO" in txt
        cv.drawRoundRect(r, 26, 26, fill((120, 20, 26) if red and unknown else (52, 52, 58)))
        for i, l in enumerate(lines):
            text(cv, l, r.left() + 22, r.top() + 44 + i * 38, 29, (255, 255, 255), 255 * pop,
                 "bold" if l.isupper() and len(l) > 3 else "reg")
        cv.restore()
        y += bh + 16
    pending = [x for x in lt if x[0] - 0.9 < t < x[0] - 0.05]
    if pending:
        r = skia.Rect.MakeXYWH(scr.left() + 28, y, 110, 56)
        cv.drawRoundRect(r, 28, 28, fill((52, 52, 58)))
        for k in range(3):
            a = 0.4 + 0.6 * (math.sin(t * 9 - k) + 1) / 2
            cv.drawCircle(r.left() + 30 + k * 25, r.centerY(), 7, fill((170, 170, 180), 255 * a))
    # input bar
    bar = skia.Rect.MakeLTRB(scr.left() + 24, scr.bottom() - 90, scr.right() - 24, scr.bottom() - 40)
    cv.drawRoundRect(bar, 25, 25, stroke((70, 70, 78), 2))
    text(cv, "iMessage", bar.left() + 24, bar.centerY() + 9, 24, (110, 110, 120), 255, "reg")
    cv.restore()
    end_phone(cv)
    if unknown:
        cv.drawRect(skia.Rect.MakeWH(W, H), fill((120, 0, 0), 30 + 20 * math.sin(t * 3)))


def call_screen(cv, W, H, t, T, shot):
    lt = shot.get("line_times", [])
    ans = lt[1][0] if len(lt) > 1 else T * 0.5
    def bg():
        cv.drawRect(skia.Rect.MakeWH(W, H), fill(BLUE_NIGHT))
    scr, _ = phone_frame(cv, W, H, t, bg=bg)
    cv.save(); cv.clipRRect(skia.RRect.MakeRectXY(scr, 46, 46), doAntiAlias=True)
    cv.drawRect(scr, lin((0, scr.top()), (0, scr.bottom()), [(40, 30, 50), (12, 10, 20)]))
    cy = scr.top() + 260
    if t < ans:
        for k in range(3):
            rr = 90 + ((t * 60 + k * 40) % 120)
            cv.drawCircle(W / 2, cy, rr, stroke((240, 120, 150), 3, 160 * (1 - (rr - 90) / 120)))
    cv.drawCircle(W / 2, cy, 90, fill((240, 120, 150)))
    text(cv, "M", W / 2, cy + 32, 90, (255, 255, 255), 255, "bold", "center")
    w = font(44, "bold").measureText("MOM")
    text(cv, "MOM", W / 2 - 16, cy + 170, 44, (255, 255, 255), 255, "bold", "center")
    heart(cv, W / 2 + w / 2 + 4, cy + 154, 16)
    status = "calling..." if t < ans else "00:%02d" % int(t - ans)
    text(cv, status, W / 2, cy + 220, 28, (200, 200, 210), 255, "semi", "center")
    by = scr.bottom() - 170
    for i, (lbl, col) in enumerate((("mute", (60, 60, 70)), ("speaker", (60, 60, 70)), ("end", (230, 50, 50)))):
        bx = scr.left() + scr.width() * (0.22 + 0.28 * i)
        cv.drawCircle(bx, by, 46, fill(col))
        text(cv, lbl, bx, by + 82, 20, (200, 200, 210), 255, "semi", "center")
    if t >= ans:
        # voice waveform
        for k in range(30):
            hgt = 8 + 30 * abs(math.sin(t * 12 + k * 0.7)) * abs(math.sin(t * 3.1 + k))
            x = scr.left() + 90 + k * ((scr.width() - 180) / 29)
            cv.drawPath(path([(x, cy + 300 - hgt), (x, cy + 300 + hgt)]), stroke((240, 120, 150), 5))
    cv.restore()
    end_phone(cv)


# ============================================================ SHOTS
def s1(cv, W, H, t, T, shot):
    u = t / T
    cam = Cam(W, H, zoom=lerp(1.0, 1.12, ease(u)), cy=H * 0.62)
    classroom(cv, cam, W, H, t)
    with cam.layer(cv, 1.0):
        draw_character(cv, "adam", W * 0.5, H * 0.86, 70, Pose(sit=True, eyes="closed", mouth="flat", lean=18,
                       hand_l=(-0.4, -2.4), hand_r=(0.6, -2.3), bob=math.sin(t * 1.4) * 0.03))
        desk(cv, W * 0.5, H * 0.75, 160)
        cv.drawRect(skia.Rect.MakeLTRB(W * 0.5 - 160, H * 0.755, W * 0.5 + 160, H * 0.83), fill((70, 54, 40)))
        cv.drawRect(skia.Rect.MakeLTRB(W * 0.5 - 160, H * 0.755, W * 0.5 + 160, H * 0.83), stroke(INK, 3))
        # backpack on the floor
        bp = skia.Rect.MakeXYWH(W * 0.78, H * 0.82, 90, 110)
        cv.drawRoundRect(bp, 30, 30, fill((110, 116, 124))); cv.drawRoundRect(bp, 30, 30, stroke(INK, 4))
    grain_vignette(cv, W, H, 200)


def s2(cv, W, H, t, T, shot):
    u = t / T
    cam = Cam(W, H, zoom=lerp(1.0, 1.08, ease(u)), cy=H * 0.5)
    classroom(cv, cam, W, H, t)
    cv.drawRect(skia.Rect.MakeWH(W, H), fill((5, 8, 16), 110))
    with cam.layer(cv, 1.0):
        wake = ease(clamp01((u - 0.15) / 0.3))
        eyes = "closed" if wake < 0.3 else ("half" if wake < 0.8 else "wide")
        p = Pose(eyes=eyes, mouth="flat", lean=lerp(25, 0, wake), look=(math.sin(t * 2) * 0.8, 0) if wake > 0.8 else (0, 0),
                 brow=0.6 * wake)
        draw_character(cv, "adam", W * 0.5, H * 1.22, 170, p)
        glow(cv, W * 0.85, H * 0.3, 300, (120, 150, 220), 50)
    grain_vignette(cv, W, H, 220)


def s3(cv, W, H, t, T, shot):
    lock_screen(cv, W, H, t, T, shot)
    grain_vignette(cv, W, H, 140)


def s4(cv, W, H, t, T, shot):
    u = t / T
    cam = Cam(W, H, zoom=1.04, dx=lerp(30, -30, u))
    classroom(cv, cam, W, H, t)
    with cam.layer(cv, 0.9):
        # classroom door on the right, open, hallway light flickering beyond
        dr = skia.Rect.MakeLTRB(W * 0.78, H * 0.3, W * 1.0, H * 0.82)
        on = flicker(t, 3)
        cv.drawRect(dr, fill((150, 170, 210) if on > 0.5 else (30, 36, 50)))
        cv.drawRect(dr, stroke(INK, 6))
    with cam.layer(cv, 1.0):
        x = lerp(W * 0.25, W * 0.6, ease(u))
        walk = t * 6 if 0.1 < u < 0.9 else None
        def pack(cv_, p):
            r = skia.Rect.MakeLTRB(-1.3, -2.8, -0.6, -1.5)
            cv_.drawRoundRect(r, 0.2, 0.2, fill((110, 116, 124))); cv_.drawRoundRect(r, 0.2, 0.2, stroke(INK, 0.08))
        p = Pose(straps=True, eyes="half", mouth="frown", walk=walk, bob=abs(math.sin(t * 6)) * 0.08 if walk else 0,
                 look=(0.9, 0), brow=0.3 + 0.6 * clamp01((u - 0.6) * 3))
        draw_character(cv, "adam", x, H * 0.9, 70, p, props=[pack])
    grain_vignette(cv, W, H, 200)


def s5(cv, W, H, t, T, shot):
    u = t / T
    cam = Cam(W, H, zoom=lerp(1.0, 1.25, ease(u)), cy=H * 0.45)
    hallway(cv, cam, W, H, t)
    grain_vignette(cv, W, H, 200)


def s6(cv, W, H, t, T, shot):
    u = t / T
    # pan across three wall clocks, all 11:47; the second hands are frozen
    cv.drawRect(skia.Rect.MakeWH(W, H), lin((0, 0), (0, H), [(44, 58, 78), (20, 26, 40)]))
    for i in range(12):
        cv.drawRect(skia.Rect.MakeXYWH(-200 + i * 110 - u * 200, 0, 8, H), fill((36, 48, 66)))
    on = flicker(t, 11)
    for i in range(4):
        cx = W * (0.25 + i * 0.5) - lerp(0, W * 0.9, ease(u))
        cy = H * (0.38 + 0.12 * (i % 2))
        draw_clock(cv, cx, cy, 120, glow_a=90 * on, wobble=0.02 * math.sin(t * 40) if i == 2 else 0)
    cv.drawRect(skia.Rect.MakeWH(W, H), fill((0, 0, 0), 120 * (1 - on)))
    grain_vignette(cv, W, H, 200)


def s7(cv, W, H, t, T, shot):
    messages(cv, W, H, t, T, shot)
    grain_vignette(cv, W, H, 120)


def s8(cv, W, H, t, T, shot):
    u = t / T
    cam = Cam(W, H, zoom=lerp(1.0, 1.15, ease(u)), cy=H * 0.4)
    hallway(cv, cam, W, H, t)
    cv.drawRect(skia.Rect.MakeWH(W, H), fill((0, 10, 40), 90))
    with cam.layer(cv, 1.0):
        p = Pose(straps=True, eyes="wide", mouth="open" if u > 0.5 else "flat", brow=1.2, sweat=clamp01(u * 1.3),
                 look=(math.sin(t * 7) * 0.4, 0), hand_r=(0.7, -2.6))
        def phone(cv_, p_):
            r = skia.Rect.MakeLTRB(0.4, -3.2, 1.0, -2.2)
            cv_.drawRoundRect(r, 0.1, 0.1, fill((20, 20, 24))); cv_.drawRoundRect(r, 0.1, 0.1, stroke(INK, 0.05))
            cv_.drawRect(r.makeInset(0.05, 0.08), fill((150, 170, 230)))
        draw_character(cv, "adam", W * 0.5, H * 1.25, 175, p, props=[phone])
        glow(cv, W * 0.62, H * 0.62, 260, (130, 160, 255), 80)
    grain_vignette(cv, W, H, 230)


def s9(cv, W, H, t, T, shot):
    call_screen(cv, W, H, t, T, shot)
    grain_vignette(cv, W, H, 120)


def s10(cv, W, H, t, T, shot):
    u = t / T
    cam = Cam(W, H, zoom=lerp(1.05, 1.12, u), cy=H * 0.5)
    hallway(cv, cam, W, H, t)
    with cam.layer(cv, 1.0):
        p = Pose(straps=True, eyes="wide", mouth="open" if 0.1 < u < 0.8 and math.sin(t * 14) > 0 else "flat", brow=1.0,
                 hand_r=(0.75, -3.6), hand_l=(-1.1, -1.7), sweat=0.6)
        def phone(cv_, p_):
            r = skia.Rect.MakeLTRB(0.6, -4.2, 1.05, -3.1)
            cv_.drawRoundRect(r, 0.1, 0.1, fill((20, 20, 24))); cv_.drawRoundRect(r, 0.1, 0.1, stroke(INK, 0.05))
        draw_character(cv, "adam", W * 0.48, H * 1.0, 110, p, props=[phone])
    grain_vignette(cv, W, H, 220)


def s11(cv, W, H, t, T, shot):
    u = t / T
    cam = Cam(W, H, zoom=lerp(1.0, 1.18, ease(u)), cx=W * 0.6, cy=H * 0.55)
    handle = ease(clamp01((u - 0.7) / 0.25))
    landing(cv, cam, W, H, t, handle=handle)
    with cam.layer(cv, 1.0):
        p = Pose(eyes="wide", brow=1.1, mouth="open" if 0.3 < u < 0.7 and math.sin(t * 11) > 0 else "frown",
                 hand_r=(0.75, -3.6), look=(1.0, 0.2), sweat=clamp01(u * 1.2), lean=-4)
        def phone(cv_, p_):
            r = skia.Rect.MakeLTRB(0.6, -4.2, 1.05, -3.1)
            cv_.drawRoundRect(r, 0.1, 0.1, fill((20, 20, 24))); cv_.drawRoundRect(r, 0.1, 0.1, stroke(INK, 0.05))
            cv_.drawRect(r.makeInset(0.05, 0.08), fill((150, 170, 230)))
        draw_character(cv, "mom", W * 0.27, H * 1.02, 112, p, props=[phone])
    cv.drawRect(skia.Rect.MakeWH(W, H), fill((0, 0, 0), 60))
    grain_vignette(cv, W, H, 230)


def s12(cv, W, H, t, T, shot):
    u = t / T
    # split: phone message, then cut to the light under the bedroom door as a shadow passes
    lt = shot.get("line_times", [])
    end = lt[0][1] if lt else T * 0.6
    if t < end + 0.4:
        messages(cv, W, H, t, T, shot)
    else:
        v = clamp01((t - end - 0.4) / max(0.5, T - end - 0.4))
        cam = Cam(W, H, zoom=2.2, cx=W * 0.6, cy=H * 0.78)
        landing(cv, cam, W, H, t, shadow=v)
        cv.drawRect(skia.Rect.MakeWH(W, H), fill((0, 0, 0), 80))
    grain_vignette(cv, W, H, 160)


def s13(cv, W, H, t, T, shot):
    u = t / T
    cam = Cam(W, H, zoom=1.08, dy=math.sin(t * 5.2) * 3)
    hallway(cv, cam, W, H, t, lights_off=clamp01((u - 0.15) / 0.75))
    with cam.layer(cv, 1.0):
        p = Pose(straps=True, eyes="wide", brow=1.3, mouth="flat", sweat=(t * 0.6) % 1, look=(-0.9, -0.2), hand_l=(-0.9, -2.4))
        draw_character(cv, "adam", W * 0.62, H * 1.08, 120, p)
    # thuds shake
    k = (t % 1.15)
    if k < 0.08:
        cv.drawRect(skia.Rect.MakeWH(W, H), fill((0, 0, 0), 60))
    grain_vignette(cv, W, H, 240)


def s14(cv, W, H, t, T, shot):
    messages(cv, W, H, t, T, shot)
    grain_vignette(cv, W, H, 160)


def s15(cv, W, H, t, T, shot):
    u = t / T
    turn = ease(clamp01(u / 0.25))
    z_end = Hall.ZEND
    cam = Cam(W, H, zoom=lerp(1.0, 2.0, ease(clamp01((u - 0.25) / 0.75))), cx=W / 2, cy=H * 0.53)
    hl = hallway(cv, cam, W, H, t, lights_dead_from=3)
    with cam.layer(cv, 0.6):
        fx, fy = hl.p(-hl.hw * 0.3, hl.fy, z_end + 0.02)
        draw_character(cv, "double", fx, fy, 170 * (z_end + 0.02), Pose(back=True, hand_l=(-0.95, -1.4), hand_r=(0.95, -1.4)))
        glow(cv, fx, fy - 60, 60, (140, 170, 255), 40)
    if turn < 1:
        # Adam's shoulder sweeps away as he turns
        with cam.layer(cv, 1.0):
            draw_character(cv, "adam", lerp(W * 0.5, W * 1.4, turn), H * 1.45, 220, Pose(back=True))
    grain_vignette(cv, W, H, 240)


TURN_KEYS = [(0.0, 0.0, 0), (1.2, 0.0, 0), (1.4, 0.38, 34), (2.2, 0.42, 38), (2.4, 0.74, -12), (2.85, 0.76, -16),
             (3.0, 1.0, 28), (9.0, 1.0, 28)]   # (time, head_turn, head_tilt) - jerky, held, then snaps
CLOSE_AT = 3.7


def _turn(t):
    for (t0, a0, d0), (t1, a1, d1) in zip(TURN_KEYS, TURN_KEYS[1:]):
        if t0 <= t <= t1:
            k = clamp01((t - t0) / max(1e-3, t1 - t0))
            k = k ** 0.25 if a1 != a0 else k      # snap fast into each pose
            return lerp(a0, a1, k), lerp(d0, d1, k)
    return TURN_KEYS[-1][1], TURN_KEYS[-1][2]


def s16(cv, W, H, t, T, shot):
    u = t / T
    turn, tilt = _turn(t)
    grin = clamp01((t - 2.9) / 0.7)
    jitter = math.sin(t * 47) * 1.5 if t > 3.0 else 0.0
    on = flicker(t * 2, 99)
    if t < CLOSE_AT:
        cam = Cam(W, H, zoom=lerp(3.2, 3.8, ease(t / CLOSE_AT)), cx=W * 0.5, cy=H * 0.53)
        hl = hallway(cv, cam, W, H, t, lights_dead_from=2)
        with cam.layer(cv, 0.6):
            fx, fy = hl.p(-hl.hw * 0.3, hl.fy, Hall.ZEND + 0.02)
            p = Pose(back=True, head_turn=turn, head_tilt=tilt + jitter, eyes="creepy", mouth="creepy",
                     grin=0.15 + 0.85 * grin, hand_l=(-0.95, -1.4), hand_r=(0.95, -1.4))
            draw_character(cv, "double", fx, fy, 170 * (Hall.ZEND + 0.02), p)
        cv.drawRect(skia.Rect.MakeWH(W, H), fill((0, 0, 0), 150 * (1 - on)))
    else:
        # extreme close-up: body still facing the wall, face twisted round, grin too wide
        k = t - CLOSE_AT
        cam = Cam(W, H, zoom=lerp(1.0, 1.12, clamp01(k / 4)), cy=H * 0.45)
        hallway(cv, Cam(W, H, zoom=5.5, cx=W * 0.5, cy=H * 0.5), W, H, t, lights_dead_from=0)
        cv.drawRect(skia.Rect.MakeWH(W, H), fill((0, 0, 0), 140))
        with cam.layer(cv, 1.0):
            lt = shot.get("line_times", [])
            talking = lt and lt[0][0] < t < lt[0][1]
            g = 1.0 + (0.06 * math.sin(t * 30) if talking else 0.02 * math.sin(t * 9))
            p = Pose(back=True, head_turn=1.0, head_tilt=24 + math.sin(t * 31) * (2.5 if talking else 0.8),
                     eyes="creepy", mouth="creepy", grin=g, look=(math.sin(t * 0.7) * 0.2, 0.1))
            draw_character(cv, "double", W * 0.5, H * 1.2, 250, p)
            glow(cv, W * 0.5, H * 0.1, 360, (180, 200, 255), 60 * on)
        cv.drawRect(skia.Rect.MakeWH(W, H), fill((0, 0, 0), 120 * (1 - on)))
        if k < 0.12:
            cv.drawRect(skia.Rect.MakeWH(W, H), fill((255, 255, 255), 160 * (1 - k / 0.12)))
    cv.drawRect(skia.Rect.MakeWH(W, H), fill((40, 0, 0), 40 + 20 * math.sin(t * 2.4)))
    grain_vignette(cv, W, H, 255)


def s17(cv, W, H, t, T, shot):
    ch = shot["choice"]
    cam = Cam(W, H, zoom=3.0, cx=W * 0.5, cy=H * 0.53)
    hl = hallway(cv, cam, W, H, t, lights_dead_from=1)
    with cam.layer(cv, 0.6):
        fx, fy = hl.p(-hl.hw * 0.3, hl.fy, Hall.ZEND + 0.02)
        draw_character(cv, "double", fx, fy, 170 * (Hall.ZEND + 0.02), Pose(back=True, lean=8))
    cv.drawRect(skia.Rect.MakeWH(W, H), fill((0, 0, 0), 170))
    a_title = ease(clamp01(t / 0.5))
    pulse = 1 + 0.03 * math.sin(t * 6)
    cv.save(); cv.translate(W / 2, H * 0.17); cv.scale(pulse, pulse)
    text(cv, ch["title"], 0, 0, 62, (255, 255, 255), 255 * a_title, "black", "center")
    cv.restore()
    text(cv, "Choose carefully. One decision will end the story.", W / 2, H * 0.215, 22, (200, 200, 210), 230 * a_title, "semi", "center")
    f = font(30, "semi")
    for i, opt in enumerate(ch["options"]):
        appear = ease(clamp01((t - 0.6 - i * 0.45) / 0.35))
        if appear <= 0:
            continue
        letter, rest = opt.split(". ", 1)
        lines = wrap(rest, f, W * 0.62)
        h = 40 + 40 * len(lines)
        y = H * 0.27 + i * 175
        x = W * 0.07 - (1 - appear) * 80
        r = skia.Rect.MakeXYWH(x, y, W * 0.86, h)
        cv.drawRoundRect(r, 24, 24, fill((24, 26, 36), 235 * appear))
        cv.drawRoundRect(r, 24, 24, stroke((255, 255, 255), 3, 90 * appear))
        bc = skia.Rect.MakeXYWH(r.left() + 20, r.centerY() - 36, 72, 72)
        cv.drawRoundRect(bc, 18, 18, fill((220, 40, 50), 255 * appear))
        text(cv, letter, bc.centerX(), bc.centerY() + 15, 42, (255, 255, 255), 255 * appear, "black", "center")
        for k, l in enumerate(lines):
            text(cv, l, r.left() + 115, r.top() + 50 + k * 40, 30, (255, 255, 255), 255 * appear, "semi")
    # lock-in button + countdown
    ab = ease(clamp01((t - 2.2) / 0.4))
    if ab > 0:
        bp = 1 + 0.04 * math.sin(t * 7)
        br = skia.Rect.MakeXYWH(W * 0.12, H * 0.8, W * 0.76, 96)
        cv.save(); cv.translate(br.centerX(), br.centerY()); cv.scale(bp, bp); cv.translate(-br.centerX(), -br.centerY())
        glow(cv, br.centerX(), br.centerY(), 300, (255, 50, 60), 70 * ab)
        cv.drawRoundRect(br, 48, 48, lin((br.left(), 0), (br.right(), 0), [(230, 40, 50), (255, 90, 60)]))
        text(cv, ch["button"], br.centerX(), br.centerY() + 13, 36, (255, 255, 255), 255 * ab, "black", "center")
        cv.restore()
        left = max(0, int(math.ceil(T - t)))
        cx, cy = W / 2, H * 0.74
        frac = (T - t) / T
        cv.drawCircle(cx, cy, 34, stroke((80, 80, 90), 6))
        arc = skia.Path(); arc.addArc(skia.Rect.MakeXYWH(cx - 34, cy - 34, 68, 68), -90, 360 * frac)
        cv.drawPath(arc, stroke((255, 70, 70), 6))
        text(cv, str(left), cx, cy + 13, 34, (255, 255, 255), 255, "bold", "center")
        text(cv, ch["footer"], W / 2, H * 0.915, 24, (255, 120, 120), 230 * ab, "semi", "center")
        text(cv, "Comment A, B or C", W / 2, H * 0.95, 26, (255, 255, 255), 230 * ab, "bold", "center")
    grain_vignette(cv, W, H, 180)


SHOTS = {i: globals()[f"s{i}"] for i in range(1, 18)}


# ============================================================ AUDIO (score + SFX)
def make_music(path_out, total, timeline):
    import horror_audio
    return horror_audio.render(path_out, total, timeline)
