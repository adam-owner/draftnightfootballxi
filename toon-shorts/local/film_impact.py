"""
"THE LAST 10 MINUTES" - interactive nuclear thriller (stories/the-last-10-minutes.json).
SHOTS[id](cv, W, H, t, T, shot)
"""
import math
import random

import skia

from draw import (INK, Pose, clamp01, draw_character, ease, fill, glow, grain_vignette, lerp, lin, outlined,
                  path, rad, soft_shadow, stroke, text, font, wrap)
from sets import Cam
from film_school import phone_frame, end_phone, messages, call_screen, BLUE_NIGHT

RED = (230, 40, 50)


def speaking(shot, t, who):
    return any(a <= t <= b for a, b, w, _ in shot.get("line_times", []) if w == who)


def alarm(t, rate=2.2):
    return 0.5 + 0.5 * math.sin(t * rate * math.pi)


# ============================================================ SKYLINE
def skyline(cv, W, H, t, horizon=0.62, dark=0.0, light=0.0, seed=4, scale=1.0):
    """Midtown skyline. light 0..1 = blinding light rising on the horizon."""
    hy = H * horizon
    sky_top = tuple(int(lerp(c, d, light)) for c, d in zip((120, 134, 150), (255, 200, 150)))
    sky_bot = tuple(int(lerp(c, d, light)) for c, d in zip((176, 186, 196), (255, 245, 220)))
    cv.drawRect(skia.Rect.MakeLTRB(-W, -H, 2 * W, hy + 2), lin((0, 0), (0, hy), [sky_top, sky_bot]))
    if light > 0:
        glow(cv, W * 0.62, hy, W * (0.3 + 1.6 * light), (255, 250, 230), 255 * min(1, light * 1.4))
    rnd = random.Random(seed)
    for row, (depth, col, hmin, hmax) in enumerate(((0.35, (104, 112, 124), 0.12, 0.3), (0.7, (74, 80, 92), 0.15, 0.42),
                                                    (1.0, (46, 50, 60), 0.2, 0.55))):
        x = -40
        while x < W + 40:
            bw = rnd.uniform(40, 110) * scale * (0.6 + 0.4 * depth)
            bh = H * rnd.uniform(hmin, hmax) * scale
            if row == 2 and abs(x - W * 0.3) < 60:
                bh = H * 0.72 * scale   # the tall spire tower
            c = tuple(int(lerp(v, 18, dark * 0.7)) for v in col)
            if light > 0:
                c = tuple(int(lerp(v, 12, light * 0.6)) for v in c)
            r = skia.Rect.MakeLTRB(x, hy - bh, x + bw, hy + 4)
            cv.drawRect(r, fill(c))
            if row == 2 and bh > H * 0.7 * scale:
                cv.drawPath(path([(x + bw * 0.2, hy - bh), (x + bw / 2, hy - bh - 70 * scale), (x + bw * 0.8, hy - bh)], close=True), fill(c))
                cv.drawRect(skia.Rect.MakeXYWH(x + bw / 2 - 2, hy - bh - 140 * scale, 4, 75 * scale), fill(c))
            # windows
            if row >= 1:
                wr = random.Random(int(x * 7 + row))
                for wy in range(int(hy - bh + 10), int(hy - 6), int(14 * scale) + 1):
                    for wx in range(int(x + 6), int(x + bw - 8), int(12 * scale) + 1):
                        if wr.random() < 0.35:
                            on = (1 - dark) * (1 - light)
                            cv.drawRect(skia.Rect.MakeXYWH(wx, wy, 5 * scale, 7 * scale),
                                        fill((240, 220, 160) if on > 0.5 else (60, 64, 74), 200 if on > 0.5 else 120))
            if row == 0 and rnd.random() < 0.3:   # water tower
                tx = x + bw * 0.5
                cv.drawRect(skia.Rect.MakeXYWH(tx - 10, hy - bh - 26, 20, 22), fill(c))
                cv.drawPath(path([(tx - 12, hy - bh - 26), (tx, hy - bh - 38), (tx + 12, hy - bh - 26)], close=True), fill(c))
            x += bw + rnd.uniform(2, 14)
    return hy


# ============================================================ STREET
WALKERS = [("biz", {}), ("woman", {}), ("adam", {"straps": True}), ("inspector", {}), ("rival", {}), ("biz", {}),
           ("woman", {}), ("adam", {"straps": True})]


def street(cv, cam, W, H, t, frozen=0.0, alert=0.0, seed=2):
    vx, vy = W / 2, H * 0.44
    with cam.layer(cv, 0.3):
        cv.drawRect(skia.Rect.MakeLTRB(-W, -H, 2 * W, 2 * H), lin((0, 0), (0, vy), [(150, 160, 172), (196, 202, 208)]))
        # far skyline at the vanishing point
        cv.save(); cv.translate(vx - W * 0.2, 0); cv.scale(0.4, 0.4); cv.translate(0, H * 0.45)
        skyline(cv, W, H, t, horizon=0.62, seed=9)
        cv.restore()
    with cam.layer(cv, 0.6):
        road = path([(-W * 0.3, H * 1.1), (W * 1.3, H * 1.1), (vx + 40, vy), (vx - 40, vy)], close=True)
        cv.drawPath(road, lin((0, vy), (0, H), [(70, 72, 78), (46, 48, 54)]))
        for k in range(14):   # lane dashes
            f0 = ((k / 14) + (0 if frozen else t * 0.15)) % 1
            f1 = f0 + 0.03
            y0, y1 = lerp(vy, H * 1.1, f0 ** 2), lerp(vy, H * 1.1, f1 ** 2)
            cv.drawPath(path([(vx, y0), (vx, y1)]), stroke((230, 210, 90), 2 + 10 * f0 ** 2))
        # crosswalk
        for k in range(8):
            x = lerp(W * 0.05, W * 0.95, k / 7)
            cv.drawPath(path([(x, H * 0.86), (lerp(x, vx, 0.06), H * 0.82)]), stroke((220, 220, 215), 16))
        for side in (-1, 1):
            sw = path([(vx + side * 40, vy), (vx + side * 70, vy), (W / 2 + side * W * 0.95, H * 1.1), (W / 2 + side * W * 0.62, H * 1.1)], close=True)
            cv.drawPath(sw, fill((150, 148, 144)))
            # facades with window grids
            fac = path([(vx + side * 70, vy), (vx + side * 70, vy - H * 0.42), (W / 2 + side * W * 1.1, -H * 0.4), (W / 2 + side * W * 1.1, H * 1.1),
                        (W / 2 + side * W * 0.95, H * 1.1)], close=True)
            cv.drawPath(fac, lin((vx, 0), (W / 2 + side * W, 0), [(96, 98, 108), (130, 120, 112)]))
            for k in range(10):
                f = (k / 10) ** 1.6
                x = lerp(vx + side * 70, W / 2 + side * W * 1.05, f)
                cv.drawPath(path([(x, lerp(vy - H * 0.42, -H * 0.4, f)), (x, lerp(vy, H * 1.05, f))]), stroke((70, 72, 80), 1 + 4 * f))
            # window rows receding along the facade
            for k in range(1, 12):
                yy = -H * 0.4 + k * H * 0.11
                cv.drawPath(path([(vx + side * 70, lerp(vy - H * 0.42, vy, k / 12)), (W / 2 + side * W * 1.1, yy)]),
                            stroke((80, 82, 92), 2))
            # lit shop windows at street level
            for k in range(3):
                f0, f1 = 0.3 + k * 0.22, 0.42 + k * 0.22
                xa, xb = lerp(vx + side * 70, W / 2 + side * W, f0), lerp(vx + side * 70, W / 2 + side * W, f1)
                ya, yb = lerp(vy, H * 0.95, f0), lerp(vy, H * 0.95, f1)
                q = path([(xa, ya - 30 * f0), (xb, yb - 30 * f1), (xb, yb - 170 * f1), (xa, ya - 170 * f0)], close=True)
                cv.drawPath(q, fill((255, 226, 150), 170)); cv.drawPath(q, stroke((50, 50, 56), 3))
        # traffic light
        tl = skia.Rect.MakeXYWH(W * 0.8, H * 0.32, 26, 70)
        cv.drawRect(skia.Rect.MakeXYWH(W * 0.8 + 11, H * 0.32 + 70, 4, 180), fill((40, 40, 44)))
        cv.drawRoundRect(tl, 6, 6, fill((30, 30, 34)))
        cv.drawCircle(tl.centerX(), tl.top() + 16, 8, fill((240, 60, 50) if frozen else (60, 30, 30)))
        cv.drawCircle(tl.centerX(), tl.bottom() - 16, 8, fill((60, 220, 120) if not frozen else (30, 60, 40)))
    # --- moving things, drawn far-to-near so nearer ones overlap farther ones
    items = []
    # cabs: lane 0 comes toward camera, lane 1 drives away (f = depth 0 far .. 1 near)
    for k in range(6):
        lane = k % 2
        speed = 0.32 if lane == 0 else 0.22
        ph = (k // 2) / 3 + lane * 0.17
        f = (ph + (t * speed if lane == 0 else -t * speed)) % 1.0
        items.append((f, "cab", lane, k))
    # pedestrians on both sidewalks, walking toward (dir=+1) or away (dir=-1)
    for i in range(12):
        side = -1 if i % 2 else 1
        d = 1 if (i // 2) % 2 == 0 else -1
        speed = 0.05 + 0.02 * ((i * 7) % 3)
        f = (0.25 + ((i * 0.29) % 1) * 1.35 + d * t * speed - 0.25) % 1.35 + 0.25   # 0.25 .. 1.6, wraps off-screen
        items.append((f, "ped", side, i, d))
    items.sort(key=lambda it: it[0])
    for it in items:
        f = it[0]
        if it[1] == "cab":
            _, _, lane, k = it
            g = f ** 1.6
            y = lerp(vy, H * 1.12, g)
            off = (-1 if lane == 0 else 1) * lerp(14, W * 0.24, g)
            with cam.layer(cv, 0.6):
                cab(cv, vx + off, y, 0.12 + 1.25 * g, away=(lane == 1))
        else:
            _, _, side, i, d = it
            if f > 1.55:
                continue
            who, extra = WALKERS[i % len(WALKERS)]
            x = W / 2 + side * lerp(70, W * 0.72, (f - 0.25) / 1.0)
            y = lerp(vy, H * 1.02, (f - 0.25) / 0.85)
            ph = i * 1.3
            walk = None if frozen else t * 7.5 + ph
            def phone(cv_, p, a=alert):
                r = skia.Rect.MakeLTRB(0.35, -2.9, 0.85, -2.1)
                cv_.drawRoundRect(r, 0.08, 0.08, fill((20, 20, 24)))
                if a > 0:
                    cv_.drawRect(r.makeInset(0.05, 0.07), fill(RED))
                    glow(cv_, r.centerX(), r.centerY(), 0.9, RED, 140 * a)
            away = d < 0 and not frozen
            p = Pose(walk=walk, bob=abs(math.sin(walk)) * 0.08 if walk else 0, back=away,
                     eyes="wide" if frozen else "dot", mouth="open" if frozen > 0.5 else "flat",
                     look=(0, 0.9) if frozen else (side * -0.4, 0),
                     hand_r=(0.6, -2.5) if frozen else (1.2, -1.6 + (0.25 * math.sin(walk) if walk else 0)),
                     hand_l=(-1.2, -1.6 - (0.25 * math.sin(walk) if walk else 0)), **extra)
            with cam.layer(cv, 0.9):
                draw_character(cv, who, x, y, 8 + 50 * min(f, 1.4), p, flip=side < 0, props=[phone] if frozen or alert else None)
    if alert:
        cv.drawRect(skia.Rect.MakeWH(W, H), fill(RED, 50 * alert * alarm(t)))


def cab(cv, x, y, s, away=False):
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    soft_shadow(cv, 0, 0, 70, 10, 120)
    body = skia.Rect.MakeLTRB(-60, -70, 60, -12)
    cv.drawRoundRect(body, 14, 14, fill((245, 196, 40))); cv.drawRoundRect(body, 14, 14, stroke(INK, 3))
    cv.drawRoundRect(skia.Rect.MakeLTRB(-44, -104, 44, -68), 12, 12, fill((245, 196, 40)))
    cv.drawRoundRect(skia.Rect.MakeLTRB(-44, -104, 44, -68), 12, 12, stroke(INK, 3))
    cv.drawRoundRect(skia.Rect.MakeLTRB(-38, -98, 38, -72), 8, 8, fill((70, 90, 110)))
    cv.drawRect(skia.Rect.MakeLTRB(-14, -114, 14, -104), fill((250, 250, 240)))
    cv.drawRect(skia.Rect.MakeLTRB(-60, -40, 60, -32), fill((30, 30, 30)))   # checker stripe
    for k in range(10):
        if k % 2:
            cv.drawRect(skia.Rect.MakeLTRB(-60 + k * 12, -40, -48 + k * 12, -32), fill((250, 250, 240)))
    for wx in (-40, 40):
        cv.drawCircle(wx, -12, 14, fill((30, 30, 32)))
        cv.drawCircle(wx, -12, 6, fill((120, 120, 126)))
    for hx in (-46, 46):
        if away:
            cv.drawRect(skia.Rect.MakeXYWH(hx - 8, -50, 16, 10), fill((230, 40, 40)))
            glow(cv, hx, -45, 24, (255, 40, 40), 120)
        else:
            cv.drawCircle(hx, -50, 8, fill((255, 245, 200)))
            glow(cv, hx, -50, 30, (255, 240, 200), 90)
    cv.restore()


# ============================================================ TIMES SQUARE
def times_square(cv, cam, W, H, t, mode="ads", glitch=0.0, frozen=1.0):
    rnd = random.Random(31)
    with cam.layer(cv, 0.4):
        cv.drawRect(skia.Rect.MakeLTRB(-W, -H, 2 * W, 2 * H), fill((40, 40, 48)))
        # walls of billboards
        for i in range(26):
            x = rnd.uniform(-W * 0.3, W * 1.2); y = rnd.uniform(-H * 0.1, H * 0.6)
            w = rnd.uniform(120, 300); h = rnd.uniform(80, 220)
            r = skia.Rect.MakeXYWH(x, y, w, h)
            if mode == "ads":
                col = [(250, 60, 120), (40, 180, 250), (250, 200, 40), (120, 230, 90), (180, 80, 250)][i % 5]
                cv.drawRect(r, lin((r.left(), r.top()), (r.right(), r.bottom()), [col, tuple(int(c * 0.5) for c in col)]))
                cv.drawRect(skia.Rect.MakeXYWH(x + w * 0.1, y + h * (0.2 + 0.1 * math.sin(t + i)), w * 0.5, h * 0.18), fill((255, 255, 255), 200))
            elif mode == "alert":
                on = alarm(t + i * 0.1)
                cv.drawRect(r, fill(tuple(int(c * (0.5 + 0.5 * on)) for c in RED)))
                text(cv, "ALERT", r.centerX(), r.centerY() + 12, min(40, w / 4), (255, 255, 255), 230, "black", "center")
            else:
                cv.drawRect(r, fill((12, 12, 14)))
            cv.drawRect(r, stroke((20, 20, 24), 6))
    with cam.layer(cv, 0.6):
        big = skia.Rect.MakeXYWH(W * 0.12, H * 0.12, W * 0.76, H * 0.3)
        cv.drawRect(big.makeOutset(14, 14), fill((16, 16, 20)))
        if mode == "ads":
            cv.drawRect(big, lin((big.left(), 0), (big.right(), 0), [(250, 120, 40), (240, 40, 120)]))
        elif mode == "alert":
            cv.drawRect(big, fill(RED))
            text(cv, "EMERGENCY", big.centerX(), big.centerY() - 10, 64, (255, 255, 255), 255, "black", "center")
            text(cv, "BROADCAST", big.centerX(), big.centerY() + 60, 64, (255, 255, 255), 255, "black", "center")
        elif mode == "news":
            news(cv, big, t, talking=False)
        else:
            cv.drawRect(big, fill((4, 4, 6)))
        if glitch:
            glitch_fx(cv, big, t, glitch)
    # crowd below, looking up
    with cam.layer(cv, 0.95):
        cv.drawRect(skia.Rect.MakeLTRB(-W, H * 0.72, 2 * W, 2 * H), fill((60, 60, 66)))
        cr = random.Random(5)
        for row in range(3):
            for k in range(9):
                who = WALKERS[(k + row) % len(WALKERS)][0]
                x = W * (k / 8) + cr.uniform(-30, 30)
                y = H * (0.86 + row * 0.08)
                ph = cr.uniform(0, 6)
                p = Pose(eyes="wide", mouth="open" if cr.random() < 0.4 else "flat",
                         look=(0.5 * math.sin(t * 0.9 + ph), -1), brow=0.8, bob=0.05 * math.sin(t * 2.2 + ph),
                         lean=3 * math.sin(t * 0.7 + ph), blink=1.0 if (t + ph) % 3.3 < 0.12 else 0.0)
                draw_character(cv, who, x, y + 60, 22 + row * 9, p)
    if mode == "alert":
        cv.drawRect(skia.Rect.MakeWH(W, H), fill(RED, 60 * alarm(t)))


def news(cv, rect, t, talking=False, tremble=0.0):
    cv.save(); cv.clipRect(rect)
    cv.drawRect(rect, lin((0, rect.top()), (0, rect.bottom()), [(20, 40, 90), (10, 18, 44)]))
    for k in range(6):
        cv.drawCircle(rect.left() + rect.width() * (0.1 + k * 0.18), rect.top() + rect.height() * 0.3, rect.width() * 0.05,
                      fill((60, 90, 160), 120))
    s = rect.height() / 700
    p = Pose(eyes="wide", brow=0.9, mouth=("open" if talking and math.sin(t * 15) > 0 else "frown"), sweat=(t * 0.7) % 1,
             look=(0.1 * math.sin(t * 9) * tremble, 0), hand_l=(-0.9, -2.2), hand_r=(0.9, -2.2))
    r = rect.height() * 0.22                       # head radius
    head_y = rect.top() + rect.height() * 0.42
    draw_character(cv, "reporter", rect.centerX() + math.sin(t * 23) * 2 * tremble, head_y + 3.55 * r, r, p)
    desk = skia.Rect.MakeLTRB(rect.left(), rect.bottom() - rect.height() * 0.28, rect.right(), rect.bottom())
    cv.drawRect(desk, lin((0, desk.top()), (0, desk.bottom()), [(40, 50, 70), (20, 24, 34)]))
    bar = skia.Rect.MakeLTRB(rect.left(), rect.bottom() - rect.height() * 0.24, rect.right(), rect.bottom() - rect.height() * 0.13)
    cv.drawRect(bar, fill(RED))
    text(cv, "BREAKING NEWS", max(bar.left(), 0) + 16 * s * 3, bar.centerY() + 9 * s * 3, 26 * s * 3, (255, 255, 255), 255, "black")
    tick = skia.Rect.MakeLTRB(rect.left(), bar.bottom(), rect.right(), rect.bottom())
    cv.drawRect(tick, fill((14, 14, 18)))
    msg = "NUCLEAR MISSILE DETECTED  •  IMPACT LOCATION UNKNOWN  •  SEEK SHELTER IMMEDIATELY  •  "
    f = font(20 * s * 3, "bold"); mw = f.measureText(msg)
    off = (t * 120 * s * 3) % mw
    for k in range(3):
        text(cv, msg, tick.left() - off + k * mw, tick.centerY() + 7 * s * 3, 20 * s * 3, (255, 255, 255), 255, "bold")
    cv.restore()


def glitch_fx(cv, rect, t, amt):
    rnd = random.Random(int(t * 24))
    cv.save(); cv.clipRect(rect)
    for _ in range(int(14 * amt)):
        y = rnd.uniform(rect.top(), rect.bottom()); h = rnd.uniform(4, 40)
        col = rnd.choice([(255, 40, 60), (40, 255, 200), (255, 255, 255), (0, 0, 0)])
        cv.drawRect(skia.Rect.MakeLTRB(rect.left() + rnd.uniform(-40, 40), y, rect.right(), y + h), fill(col, 180 * amt))
    cv.restore()


# ============================================================ APARTMENT
def apartment(cv, cam, W, H, t, lights=1.0, light=0.0, dark_city=0.0):
    with cam.layer(cv, 0.25):
        win = skia.Rect.MakeLTRB(-W * 0.05, H * 0.08, W * 1.05, H * 0.64)
        cv.save(); cv.clipRect(win)
        skyline(cv, W, H, t, horizon=0.62, dark=dark_city, light=light, seed=4, scale=0.9)
        cv.restore()
        for fx in (0.33, 0.66):
            cv.drawRect(skia.Rect.MakeXYWH(W * fx - 6, win.top(), 12, win.height()), fill((40, 40, 46)))
        cv.drawRect(win, stroke((40, 40, 46), 16))
    with cam.layer(cv, 0.5):
        wall = (110, 104, 100) if lights > 0.5 else (36, 36, 44)
        cv.drawRect(skia.Rect.MakeLTRB(-W, -H, 2 * W, win.top()), fill(wall))
        cv.drawRect(skia.Rect.MakeLTRB(-W, win.bottom(), 2 * W, 2 * H), lin((0, win.bottom()), (0, H), [(120, 96, 76), (70, 54, 42)]))
        # couch
        c = skia.Rect.MakeXYWH(W * 0.08, H * 0.7, W * 0.6, H * 0.12)
        cv.drawRoundRect(c, 24, 24, fill((70, 90, 120))); cv.drawRoundRect(c, 24, 24, stroke(INK, 4))
        cv.drawRoundRect(skia.Rect.MakeXYWH(c.left(), c.top() - 70, c.width(), 90), 24, 24, fill((60, 78, 106)))
        cv.drawRoundRect(skia.Rect.MakeXYWH(c.left(), c.top() - 70, c.width(), 90), 24, 24, stroke(INK, 4))
        # lamp
        lx = W * 0.85
        cv.drawRect(skia.Rect.MakeXYWH(lx - 4, H * 0.55, 8, H * 0.27), fill((40, 40, 44)))
        shade = path([(lx - 46, H * 0.55), (lx + 46, H * 0.55), (lx + 30, H * 0.48), (lx - 30, H * 0.48)], close=True)
        outlined(cv, shade, (240, 220, 170) if lights > 0.5 else (90, 86, 80), 3)
        if lights > 0.5:
            glow(cv, lx, H * 0.56, 240, (255, 210, 140), 110)
    if lights < 0.5:
        cv.drawRect(skia.Rect.MakeWH(W, H), fill((0, 0, 10), 120))
    if light > 0:
        cv.drawRect(skia.Rect.MakeWH(W, H), fill((255, 240, 210), 200 * light ** 2, blend=skia.BlendMode.kPlus))


# ============================================================ PHONE: ALERTS
def alert_screen(cv, W, H, t, T, shot):
    al = shot["alert"]
    kind = al.get("kind", "fema")
    lt = shot.get("line_times", [])
    # the alert pops up when the first silent (on-screen only) line starts
    reveal_at = next((x[0] for x, ln in zip(lt, shot.get("lines", [])) if ln.get("silent")), 0.0)
    shake = clamp01(1 - abs(t - reveal_at) / 0.4) if kind != "impact" else clamp01(1 - t / 0.6)

    def bg():
        cv.drawRect(skia.Rect.MakeWH(W, H), fill((10, 6, 8)))
    scr, _ = phone_frame(cv, W, H, t, shake=shake, bg=bg)
    cv.save(); cv.clipRRect(skia.RRect.MakeRectXY(scr, 46, 46), doAntiAlias=True)
    if kind == "impact":
        on = 0.6 + 0.4 * alarm(t, 4)
        cv.drawRect(scr, fill(tuple(int(c * on) for c in RED)))
        text(cv, "IMPACT", W / 2, scr.centerY() - 20, 120, (255, 255, 255), 255, "black", "center")
        text(cv, "CONFIRMED.", W / 2, scr.centerY() + 110, 92, (255, 255, 255), 255, "black", "center")
        cv.restore(); end_phone(cv)
        fl = clamp01((t - (T - 1.0)) / 0.6)
        if fl:
            cv.drawRect(skia.Rect.MakeWH(W, H), fill((255, 255, 255), 255 * fl))
        return
    cv.drawRect(scr, lin((0, scr.top()), (0, scr.bottom()), [(30, 26, 40), (12, 10, 16)]))
    text(cv, "11:5" + ("0" if kind == "fema" else "5"), W / 2, scr.top() + 210, 120, (255, 255, 255), 200, "bold", "center")
    shown = t >= reveal_at - 0.05
    if shown:
        pop = ease(clamp01((t - reveal_at) / 0.25))
        card = skia.Rect.MakeLTRB(scr.left() + 26, scr.top() + 270, scr.right() - 26, scr.bottom() - 120)
        cv.save(); cv.translate(0, (1 - pop) * -40)
        if kind == "unknown":
            cv.drawRoundRect(card, 30, 30, fill((6, 14, 10), 240 * pop))
            cv.drawRoundRect(card, 30, 30, stroke((60, 255, 150), 3, 200 * pop))
            hc = (60, 255, 150)
        else:
            cv.drawRoundRect(card, 30, 30, fill((235, 235, 240), 245 * pop))
            hc = (20, 20, 24)
        y = card.top() + 70
        tri = path([(card.left() + 50, y - 34), (card.left() + 26, y + 8), (card.left() + 74, y + 8)], close=True)
        cv.drawPath(tri, fill(RED if kind == "fema" else hc, 255 * pop))
        text(cv, "!", card.left() + 50, y + 2, 30, (255, 255, 255) if kind == "fema" else (0, 0, 0), 255 * pop, "black", "center")
        text(cv, al["header"], card.left() + 92, y, 34 if kind == "fema" else 28, hc, 255 * pop, "black")
        y += 50
        if al.get("level"):
            lbl = skia.Rect.MakeXYWH(card.left() + 28, y - 30, 160, 42)
            cv.drawRoundRect(lbl, 10, 10, fill(RED, 255 * pop))
            text(cv, al["level"], lbl.centerX(), lbl.centerY() + 10, 26, (255, 255, 255), 255 * pop, "black", "center")
            y += 46
        if al.get("from"):
            text(cv, al["from"], card.left() + 28, y, 20, (120, 120, 130) if kind == "fema" else (60, 200, 130), 255 * pop, "bold")
            y += 50
        f = font(30, "semi")
        body = al["body"]
        if kind == "unknown":   # typed out, with scrambled characters at the cursor
            n = int(len(body) * clamp01((t - reveal_at) / max(0.5, (T - reveal_at) * 0.75)))
            rnd = random.Random(int(t * 20))
            body = body[:n] + "".join(rnd.choice("#$%&@!?01") for _ in range(min(3, len(body) - n)))
        for ln in wrap(body, f, card.width() - 56):
            text(cv, ln, card.left() + 28, y, 30, hc if kind == "unknown" else (30, 30, 34), 255 * pop, "semi")
            y += 42
        cv.restore()
    cv.restore()
    end_phone(cv)
    if al.get("dead"):
        lt0 = lt[0][0] if lt else 0
        g = clamp01((t - lt0) / 0.5)
        glitch_fx(cv, skia.Rect.MakeWH(W, H), t, 1 - g)
        cv.drawRect(skia.Rect.MakeWH(W, H), fill((0, 0, 0), 255 * ease(g)))
    if kind == "fema" and shown:
        cv.drawRect(skia.Rect.MakeWH(W, H), fill(RED, 40 * alarm(t)))


# ============================================================ CARDS
def card(cv, W, H, t, T, shot):
    c = shot["card"]
    cv.drawRect(skia.Rect.MakeWH(W, H), fill((4, 4, 6)))
    jit = random.Random(int(t * 12)).uniform(-3, 3) if t % 1.0 < 0.12 else 0
    if c.get("title"):
        a = ease(clamp01(t / 0.6))
        text(cv, c["title"], W / 2, H * 0.42, 74, (255, 255, 255), 255 * a, "black", "center")
        cv.drawRect(skia.Rect.MakeXYWH(W * 0.2, H * 0.45, W * 0.6 * a, 6), fill(RED))
        text(cv, c["time"] + "  —  " + c.get("place", ""), W / 2, H * 0.52, 36, RED, 255 * ease(clamp01((t - 0.5) / 0.5)), "bold", "center")
        return
    on = alarm(t, 2)
    glow(cv, W / 2, H * 0.46, 380, RED, 50 * on)
    text(cv, c["time"], W / 2 + jit, H * 0.5, 150, (255, 255, 255), 255, "bold", "center")
    text(cv, c["time"], W / 2 + jit + 4, H * 0.5, 150, RED, 90, "bold", "center")
    mins = 60 - int(c["time"].split(":")[1][:2])
    text(cv, f"{mins} MINUTE{'S' if mins != 1 else ''} LEFT", W / 2, H * 0.58, 30, RED, 255, "bold", "center")


def choice4(cv, W, H, t, T, shot):
    ch = shot["choice"]
    skyline(cv, W, H, t, horizon=0.8, dark=1.0, light=0.0)
    cv.drawRect(skia.Rect.MakeWH(W, H), fill((0, 0, 0), 175))
    glow(cv, W * 0.6, H * 0.8, W * 0.8, (255, 220, 170), 70)
    a_title = ease(clamp01(t / 0.5))
    pulse = 1 + 0.03 * math.sin(t * 6)
    cv.save(); cv.translate(W / 2, H * 0.14); cv.scale(pulse, pulse)
    text(cv, ch["title"], 0, 0, 56, (255, 255, 255), 255 * a_title, "black", "center")
    cv.restore()
    f = font(28, "semi")
    for i, opt in enumerate(ch["options"]):
        appear = ease(clamp01((t - 0.6 - i * 0.4) / 0.35))
        if appear <= 0:
            continue
        letter, rest = opt.split(". ", 1) if ". " in opt else opt.split(") ", 1)
        lines = wrap(rest, f, W * 0.6)
        h = 34 + 38 * len(lines)
        y = H * 0.2 + i * 150
        r = skia.Rect.MakeXYWH(W * 0.07 - (1 - appear) * 80, y, W * 0.86, h)
        cv.drawRoundRect(r, 22, 22, fill((24, 26, 36), 235 * appear))
        cv.drawRoundRect(r, 22, 22, stroke((255, 255, 255), 3, 90 * appear))
        bc = skia.Rect.MakeXYWH(r.left() + 18, r.centerY() - 33, 66, 66)
        cv.drawRoundRect(bc, 16, 16, fill(RED, 255 * appear))
        text(cv, letter, bc.centerX(), bc.centerY() + 14, 40, (255, 255, 255), 255 * appear, "black", "center")
        for k, l in enumerate(lines):
            text(cv, l, r.left() + 104, r.top() + 46 + k * 38, 28, (255, 255, 255), 255 * appear, "semi")
    ab = ease(clamp01((t - 2.4) / 0.4))
    if ab > 0:
        left = max(0, int(math.ceil(T - t)))
        cx, cy = W / 2, H * 0.8
        frac = (T - t) / T
        cv.drawCircle(cx, cy, 34, stroke((80, 80, 90), 6))
        arc = skia.Path(); arc.addArc(skia.Rect.MakeXYWH(cx - 34, cy - 34, 68, 68), -90, 360 * frac)
        cv.drawPath(arc, stroke((255, 70, 70), 6))
        text(cv, str(left), cx, cy + 13, 34, (255, 255, 255), 255, "bold", "center")
        bp = 1 + 0.04 * math.sin(t * 7)
        br = skia.Rect.MakeXYWH(W * 0.12, H * 0.85, W * 0.76, 92)
        cv.save(); cv.translate(br.centerX(), br.centerY()); cv.scale(bp, bp); cv.translate(-br.centerX(), -br.centerY())
        glow(cv, br.centerX(), br.centerY(), 300, (255, 50, 60), 70 * ab)
        cv.drawRoundRect(br, 46, 46, lin((br.left(), 0), (br.right(), 0), [(230, 40, 50), (255, 90, 60)]))
        text(cv, ch["button"], br.centerX(), br.centerY() + 13, 34, (255, 255, 255), 255 * ab, "black", "center")
        cv.restore()
        text(cv, ch["footer"], W / 2, H * 0.965, 26, (255, 255, 255), 230 * ab, "bold", "center")
    grain_vignette(cv, W, H, 160)


# ============================================================ SHOTS
def s1(cv, W, H, t, T, shot):
    skyline(cv, W, H, t, horizon=0.72)
    cv.drawRect(skia.Rect.MakeWH(W, H), fill((0, 0, 0), 150))
    c = shot["card"]
    a = ease(clamp01(t / 0.6))
    text(cv, "THE LAST", W / 2, H * 0.36, 92, (255, 255, 255), 255 * a, "black", "center")
    text(cv, "10 MINUTES", W / 2, H * 0.45, 92, RED, 255 * a, "black", "center")
    cv.drawRect(skia.Rect.MakeXYWH(W * 0.5 - W * 0.32 * a, H * 0.48, W * 0.64 * a, 5), fill((255, 255, 255)))
    b = ease(clamp01((t - 0.7) / 0.5))
    text(cv, c["time"] + "  —  " + c["place"], W / 2, H * 0.535, 34, (230, 230, 235), 255 * b, "bold", "center")
    grain_vignette(cv, W, H, 150)


def s2(cv, W, H, t, T, shot):
    cam = Cam(W, H, zoom=lerp(1.0, 1.1, ease(t / T)), cy=H * 0.5)
    street(cv, cam, W, H, t)
    grain_vignette(cv, W, H, 120)


def s3(cv, W, H, t, T, shot):
    u = t / T
    stop = ease(clamp01((u - 0.45) / 0.2))
    cam = Cam(W, H, zoom=1.1 + 0.05 * stop, cy=H * 0.5)
    street(cv, cam, W, H, t if stop < 0.5 else T * 0.45, frozen=stop, alert=stop)
    grain_vignette(cv, W, H, 140)


def s4(cv, W, H, t, T, shot):
    alert_screen(cv, W, H, t, T, shot)
    grain_vignette(cv, W, H, 120)


def s5(cv, W, H, t, T, shot):
    cam = Cam(W, H, zoom=lerp(1.15, 1.35, ease(t / T)), cy=H * 0.6)
    street(cv, cam, W, H, 0.0, frozen=1.0, alert=1.0)
    grain_vignette(cv, W, H, 170)


def s6(cv, W, H, t, T, shot):
    u = t / T
    mode = "ads" if u < 0.35 else "alert"
    g = clamp01(1 - abs(u - 0.35) / 0.06)
    cam = Cam(W, H, zoom=lerp(1.0, 1.08, ease(u)), cy=H * 0.4)
    times_square(cv, cam, W, H, t, mode=mode, glitch=g)
    grain_vignette(cv, W, H, 140)


def s7(cv, W, H, t, T, shot):
    u = t / T
    cv.drawRect(skia.Rect.MakeWH(W, H), fill((10, 10, 14)))
    z = lerp(0.0, 1.0, ease(clamp01(u / 0.25)))
    rect = skia.Rect.MakeLTRB(lerp(W * 0.12, -W * 0.12, z), lerp(H * 0.12, H * 0.1, z),
                              lerp(W * 0.88, W * 1.12, z), lerp(H * 0.42, H * 0.62, z))
    if z < 1:
        times_square(cv, Cam(W, H, zoom=1.0 + z * 0.2, cy=H * 0.27), W, H, t, mode="news")
    cv.drawRect(rect.makeOutset(12, 12), fill((16, 16, 20)))
    news(cv, rect, t, talking=speaking(shot, t, "reporter"), tremble=1.0)
    # scanlines
    for y in range(int(rect.top()), int(rect.bottom()), 6):
        cv.drawRect(skia.Rect.MakeLTRB(rect.left(), y, rect.right(), y + 2), fill((0, 0, 0), 40))
    if z >= 1:
        # crowd heads watching, lower frame
        for k in range(6):
            draw_character(cv, WALKERS[k][0], W * (0.08 + k * 0.17), H * 1.12, 60, Pose(back=True))
    grain_vignette(cv, W, H, 160)


def s8(cv, W, H, t, T, shot):
    u = t / T
    cam = Cam(W, H, zoom=1.12, cy=H * 0.3)
    g = clamp01(1 - abs(u - 0.4) / 0.12)
    times_square(cv, cam, W, H, t, mode="news" if u < 0.4 else "black", glitch=g)
    grain_vignette(cv, W, H, 170)


def s_card(cv, W, H, t, T, shot):
    card(cv, W, H, t, T, shot)
    grain_vignette(cv, W, H, 150)


def s10(cv, W, H, t, T, shot):
    u = t / T
    cam = Cam(W, H, zoom=lerp(1.0, 1.15, ease(u)), cy=H * 0.6)
    apartment(cv, cam, W, H, t)
    with cam.layer(cv, 1.0):
        ring_on = u > 0.55
        def phone(cv_, p):
            r = skia.Rect.MakeLTRB(0.55, -3.0, 1.05, -2.1)
            cv_.drawRoundRect(r, 0.08, 0.08, fill((20, 20, 24)))
            cv_.drawRect(r.makeInset(0.05, 0.07), fill((90, 200, 120) if ring_on and math.sin(t * 12) > 0 else (130, 150, 200)))
        p = Pose(eyes="wide" if ring_on else "half", mouth="flat", hand_r=(0.8, -2.6), look=(0.6, 0.4), brow=0.4)
        draw_character(cv, "alex", W * 0.38, H * 0.92, 88, p, props=[phone])
        draw_character(cv, "sister", W * 0.7, H * 0.9, 52, Pose(sit=True, eyes="dot", mouth="frown", look=(-0.8, 0)))
    grain_vignette(cv, W, H, 150)


def s_call(cv, W, H, t, T, shot):
    call_screen(cv, W, H, t, T, shot)
    grain_vignette(cv, W, H, 130)


def s_msg(cv, W, H, t, T, shot):
    messages(cv, W, H, t, T, shot)
    grain_vignette(cv, W, H, 130)


def s14(cv, W, H, t, T, shot):
    u = t / T
    cam = Cam(W, H, zoom=lerp(1.25, 1.5, ease(u)), cx=W * 0.62, cy=H * 0.62)
    apartment(cv, cam, W, H, t)
    cv.drawRect(skia.Rect.MakeWH(W, H), fill((0, 0, 20), 60))
    with cam.layer(cv, 1.0):
        sob = abs(math.sin(t * 5))
        draw_character(cv, "sister", W * 0.66, H * 0.92, 64,
                       Pose(sit=True, eyes="closed", mouth="open" if sob > 0.5 else "frown", tears=clamp01(u * 1.5), brow=1.2,
                            bob=sob * 0.06, hand_l=(-0.5, -3.3), hand_r=(0.5, -3.3)))
        talk = speaking(shot, t, "alex")
        draw_character(cv, "alex", W * 0.3, H * 0.98, 80,
                       Pose(eyes="half" if talk else "wide", brow=0.6 if talk else 1.0, look=(1, 0.3),
                            mouth=("open" if math.sin(t * 16) > 0 else "smile") if talk else "frown",
                            hand_r=(1.6, -2.3) if talk else (1.25, -1.6)))
    grain_vignette(cv, W, H, 180)


def s_alert(cv, W, H, t, T, shot):
    alert_screen(cv, W, H, t, T, shot)
    grain_vignette(cv, W, H, 130)


def s20(cv, W, H, t, T, shot):
    u = t / T
    lt = shot.get("line_times", [])
    off = lt[0][0] + 0.4 if lt else T * 0.3
    lights = 1.0 if t < off else (0.0 if t > off + 0.35 or math.sin(t * 60) > 0 else 1.0)
    cam = Cam(W, H, zoom=lerp(1.05, 1.12, u), cy=H * 0.55)
    apartment(cv, cam, W, H, t, lights=lights, dark_city=0.0 if t < off else 1.0)
    with cam.layer(cv, 1.0):
        a_talk, s_talk = speaking(shot, t, "alex"), speaking(shot, t, "sister")
        flap = math.sin(t * 16) > 0
        draw_character(cv, "alex", W * 0.36, H * 0.94, 86,
                       Pose(eyes="wide", brow=1.2, look=(0.8, 0.2) if a_talk else (0.4, -0.6),
                            mouth=("open" if flap else "flat") if a_talk else ("open" if lights < 0.5 else "flat"),
                            hand_r=(1.7, -2.2) if a_talk else (1.25, -1.6)))
        draw_character(cv, "sister", W * 0.66, H * 0.92, 54,
                       Pose(eyes="closed" if s_talk else "wide", brow=1.2, tears=0.8 if t > (shot.get("line_times") or [[0]])[0][0] else 0,
                            mouth=("open" if flap else "frown") if s_talk else "open", look=(-0.6, -0.4),
                            bob=0.05 * abs(math.sin(t * 5)), hand_l=(-0.5, -3.3) if s_talk else (-1.25, -1.6)))
    grain_vignette(cv, W, H, 200)


def s22(cv, W, H, t, T, shot):
    cam = Cam(W, H, zoom=lerp(1.0, 1.06, ease(t / T)), cy=H * 0.55)
    with cam.layer(cv, 1.0):
        skyline(cv, W, H, t, horizon=0.75, dark=1.0)
    cv.drawRect(skia.Rect.MakeWH(W, H), fill((0, 0, 10), 70))
    grain_vignette(cv, W, H, 180)


def s23(cv, W, H, t, T, shot):
    u = t / T
    light = ease(clamp01((u - 0.3) / 0.7)) * 0.85
    cam = Cam(W, H, zoom=lerp(1.0, 1.2, ease(u)), cy=H * 0.4)
    apartment(cv, cam, W, H, t, lights=0.0, light=light, dark_city=1.0)
    with cam.layer(cv, 1.0):
        draw_character(cv, "alex", W * 0.42, H * 1.02, 110, Pose(back=True, hand_l=(-1.0, -1.5), hand_r=(1.0, -1.5)))
        draw_character(cv, "sister", W * 0.68, H * 0.98, 64, Pose(back=True, hand_l=(-1.2, -2.0)))
    if light:
        cv.drawRect(skia.Rect.MakeWH(W, H), fill((255, 250, 235), 120 * light ** 3, blend=skia.BlendMode.kPlus))
    grain_vignette(cv, W, H, 150)


SHOTS = {1: s1, 2: s2, 3: s3, 4: s4, 5: s5, 6: s6, 7: s7, 8: s8, 9: s_card, 10: s10, 11: s_call, 12: s_msg,
         13: s_msg, 14: s14, 15: s_card, 16: s_alert, 17: s_alert, 18: s_card, 19: s_call, 20: s20, 21: s_card,
         22: s22, 23: s23, 24: s_alert, 25: choice4}


def make_music(path_out, total, timeline):
    import horror_audio
    return horror_audio.render(path_out, total, timeline)
