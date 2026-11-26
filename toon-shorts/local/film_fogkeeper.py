"""
Shot-by-shot animation for "The Lighthouse That Sold Fog" (stories/fog-keeper.json).
Each SHOTS[id](cv, W, H, t, T) draws frame at time t (s) of a shot lasting T (s).
"""
import math
import random

import skia

from draw import (Pose, beam, bill, cash_stack, clamp01, draw_character, ease, fill, fog_bank, fog_jet,
                  fog_machine, glow, grain_vignette, lantern, lerp, lighthouse, path, puff, rowboat, stroke,
                  INK, lin, rad, outlined, soft_shadow)
from sets import (Cam, dock_night, gulls, island, lamp_room, lamp_table, night_sky, sale_table, sea,
                  ship, ship_bridge, ships_wheel, sky_day, theatre)


def blink(t, every=3.1, off=0.0):
    return 1.0 if ((t + off) % every) < 0.12 else 0.0


def push(u, a=1.0, b=1.12):
    return lerp(a, b, ease(u))


# 1 ---------------------------------------------------------------------------
def s1(cv, W, H, t, T):
    u = t / T
    cam = Cam(W, H, zoom=push(u, 1.0, 1.45), cy=H * 0.55)
    with cam.layer(cv, 0.0):
        sky_day(cv, W, H, t)
    with cam.layer(cv, 0.4):
        sea(cv, W, H, H * 0.5, t)
    with cam.layer(cv, 0.8):
        island(cv, W * 0.5, H * 0.6, 230, t, lamp=0.4)
        ship(cv, W * 0.15 + t * 14, H * 0.53, 26)
    with cam.layer(cv, 1.0):
        gulls(cv, W, H, t, 5)
    grain_vignette(cv, W, H, 110)


# 2 ---------------------------------------------------------------------------
def s2(cv, W, H, t, T):
    u = t / T
    cam = Cam(W, H, zoom=1.08, dx=lerp(30, -30, ease(u)))
    lamp_room(cv, cam, W, H, t, lens_x=0.6)
    with cam.layer(cv, 1.0):
        rub = (math.cos(t * 4) * 0.35, math.sin(t * 4) * 0.35)
        def rag(cv_, p):
            cv_.drawCircle(p.hand_r[0], p.hand_r[1], 0.3, fill((235, 225, 200)))
            cv_.drawCircle(p.hand_r[0], p.hand_r[1], 0.3, stroke(INK, 0.06))
        p = Pose(eyes="half", mouth="smile", blink=blink(t), hand_r=(1.9 + rub[0], -3.2 + rub[1]),
                 hand_l=(-1.1, -1.7), bob=abs(math.sin(t * 4)) * 0.05)
        draw_character(cv, "gus", W * 0.28, H * 0.88, 66, p, props=[rag])
    grain_vignette(cv, W, H)


# 3 ---------------------------------------------------------------------------
def s3(cv, W, H, t, T):
    u = t / T
    cam = Cam(W, H, zoom=push(u, 1.25, 1.0))
    with cam.layer(cv, 0.0):
        night_sky(cv, W, H, t)
    with cam.layer(cv, 0.3):
        sea(cv, W, H, H * 0.52, t, night=True)
        lp, _ = island(cv, W * 0.8, H * 0.55, 110, t, lamp=1.0, night=True)
    with cam.layer(cv, 0.6):
        fog_bank(cv, W, H, t, H * 0.35, H * 0.75, 30, 120, seed=3, speed=15)
        beam(cv, lp, math.pi + 0.3 * math.sin(t * 0.8), W * 1.1, 120, 150)
        turn = ease(clamp01((u - 0.2) / 0.6))
        cv.save(); cv.translate(W * lerp(0.25, 0.4, turn), H * 0.66); cv.scale(lerp(-1, 1, turn) or 0.01, 1)
        ship(cv, 0, 0, 60, lights=1, night=True)
        cv.restore()
    with cam.layer(cv, 1.0):
        fog_bank(cv, W, H, t, H * 0.6, H * 1.0, 20, 140, seed=4, speed=25)
    grain_vignette(cv, W, H, 170)


# 4 ---------------------------------------------------------------------------
def s4(cv, W, H, t, T):
    u = t / T
    cam = Cam(W, H, zoom=1.05, dx=lerp(40, -40, u))
    with cam.layer(cv, 0.0):
        sky_day(cv, W, H, t)
    with cam.layer(cv, 0.3):
        sea(cv, W, H, H * 0.46, t)
        ship(cv, W * 0.1 + t * 30, H * 0.47, 22)
        ship(cv, W * 0.9 - t * 22, H * 0.5, 30)
    with cam.layer(cv, 1.0):
        from sets import rocks
        rocks(cv, W * 0.75, H * 1.0, W * 1.2, H * 0.25, seed=8)
        ledge = path([(-40, H * 0.84), (W * 0.15, H * 0.8), (W * 0.62, H * 0.805), (W * 0.75, H * 0.86), (W * 0.7, H + 40), (-40, H + 40)], close=True)
        outlined(cv, ledge, (112, 102, 96), 3)
        cv.drawPath(path([(W * 0.15, H * 0.8), (W * 0.62, H * 0.805)]), stroke((150, 140, 132), 5))
        p = Pose(sit=True, eyes="half", mouth="flat", blink=blink(t, 2.6), hand_l=(-0.8, -1.4), hand_r=(0.8, -1.4))
        draw_character(cv, "gus", W * 0.4, H * 0.81, 62, p)
        # seagull lands next to him
        g = ease(clamp01((u - 0.25) / 0.4))
        gx, gy = lerp(W * 1.1, W * 0.6, g), lerp(H * 0.4, H * 0.805, g)
        flap = math.sin(t * 14) * 10 * (1 - g)
        cv.save(); cv.translate(gx, gy)
        body = skia.Path(); body.addOval(skia.Rect.MakeLTRB(-26, -40, 26, 0))
        outlined(cv, body, (250, 250, 250), 3)
        cv.drawCircle(-18, -44, 14, fill((250, 250, 250))); cv.drawCircle(-18, -44, 14, stroke(INK, 3))
        cv.drawCircle(-22, -46, 2.5, fill(INK))
        cv.drawPath(path([(-32, -44), (-44, -40), (-32, -38)], close=True), fill((240, 180, 40)))
        cv.drawPath(path([(0, -28), (34, -40 - flap), (20, -18)], close=True), fill((180, 185, 195)))
        cv.drawPath(path([(-6, 0), (-6, 10)]), stroke((240, 180, 40), 3))
        cv.drawPath(path([(6, 0), (6, 10)]), stroke((240, 180, 40), 3))
        cv.restore()
    grain_vignette(cv, W, H, 110)


# 5 ---------------------------------------------------------------------------
def s5(cv, W, H, t, T):
    u = t / T
    cam = Cam(W, H, zoom=push(u, 1.0, 1.1), cy=H * 0.45)
    lamp_room(cv, cam, W, H, t, lens_x=0.85)
    cv.drawRect(skia.Rect.MakeWH(W, H), fill((20, 12, 8), 90))
    with cam.layer(cv, 1.0):
        def wallet(cv_, p):
            x, y = p.hand_r
            cv_.save(); cv_.translate(x - 0.6, y); cv_.scale(1.4, 1.4)
            w = skia.Rect.MakeLTRB(-0.75, -0.5, 0.75, 0.5)
            cv_.drawRoundRect(w, 0.1, 0.1, fill((120, 70, 40))); cv_.drawRoundRect(w, 0.1, 0.1, stroke(INK, 0.05))
            cv_.drawRect(skia.Rect.MakeLTRB(-0.65, -0.45, 0.65, -0.1), fill((60, 35, 20)))
            cv_.restore()
            mu = clamp01((u - 0.2) / 0.7)
            if mu > 0:
                mx = x - 0.6 + math.sin(t * 6) * 0.4 * mu + mu * 0.6
                my = y - 0.4 - mu * 2.2
                fl = abs(math.sin(t * 30)) * 0.18
                cv_.drawOval(skia.Rect.MakeLTRB(mx - 0.25, my - fl, mx, my + 0.12), fill((200, 190, 170)))
                cv_.drawOval(skia.Rect.MakeLTRB(mx, my - fl, mx + 0.25, my + 0.12), fill((200, 190, 170)))
                cv_.drawCircle(mx, my + 0.05, 0.05, fill(INK))
        p = Pose(eyes="half", mouth="flat", blink=1.0 if 0.55 < u < 0.62 else 0.0,
                 hand_r=(1.1, -2.5), hand_l=(-0.2, -2.45), look=(0.3, 0.6))
        draw_character(cv, "gus", W * 0.45, H * 1.08, 150, p, props=[wallet])
    grain_vignette(cv, W, H, 170)


# 6 ---------------------------------------------------------------------------
def s6(cv, W, H, t, T):
    u = t / T
    cam = Cam(W, H, zoom=push(u, 1.0, 1.15), cy=H * 0.55)
    theatre(cv, cam, W, H, t, spot=(0.6, 0.72))
    with cam.layer(cv, 0.8):
        sale_table(cv, W * 0.62, H * 0.66, 300)
    with cam.layer(cv, 1.0):
        rise = ease(clamp01((u - 0.4) / 0.25))
        p = Pose(eyes="wide" if rise > 0.5 else "half", brow=rise * 1.4, mouth="open" if rise > 0.5 else "flat",
                 lean=10 * rise, hand_r=(1.3, -2.2 - rise * 0.4), look=(0.8, 0.3))
        draw_character(cv, "gus", W * 0.25, H * 0.9, 70, p)
    grain_vignette(cv, W, H, 190)


# 7 ---------------------------------------------------------------------------
def s7(cv, W, H, t, T):
    u = t / T
    cam = Cam(W, H, zoom=push(u, 1.0, 1.2), cy=H * 0.6)
    theatre(cv, cam, W, H, t, spot=(0.5, 0.66), spot_on=1.0 if u > 0.08 or (t * 20) % 2 > 1 else 0.3)
    with cam.layer(cv, 1.0):
        fog_machine(cv, W * 0.46, H * 0.7, 360, on=0.0)
        if u > 0.55:
            fog_jet(cv, W * 0.46 + 360 * 0.68, H * 0.7 - 360 * 0.33, 70, clamp01((u - 0.55) * 3) * 0.6, t, dirx=1)
    grain_vignette(cv, W, H, 200)


# 8 ---------------------------------------------------------------------------
def s8(cv, W, H, t, T):
    stroke_ph = t * 2.2
    pull = (math.sin(stroke_ph) + 1) / 2
    cam = Cam(W, H, zoom=1.0, dx=math.sin(t * 1.3) * 10, dy=math.sin(t * 2.2) * 8)
    with cam.layer(cv, 0.0):
        night_sky(cv, W, H, t, moon=(0.7, 0.12))
    with cam.layer(cv, 0.2):
        sea(cv, W, H, H * 0.42, t, night=True)
        lp, _ = island(cv, W * 0.3, H * 0.44, 80, t, lamp=1.0, night=True)
        beam(cv, lp, t * 0.9, W * 0.9, 70, 110)
    with cam.layer(cv, 1.0):
        cv.save(); cv.rotate(math.sin(t * 1.5) * 2)
        # inside of the boat (POV)
        hull = skia.Path(); hull.moveTo(-60, H * 1.1); hull.quadTo(W * 0.15, H * 0.62, W / 2, H * 0.58)
        hull.quadTo(W * 0.85, H * 0.62, W + 60, H * 1.1); hull.close()
        outlined(cv, hull, (130, 82, 48), 4)
        for k in range(4):
            yy = H * 0.66 + k * 70
            cv.drawPath(path([(W * 0.12 + k * 10, yy), (W * 0.88 - k * 10, yy)]), stroke((100, 62, 35), 4))
        fog_machine(cv, W * 0.5, H * 0.72, 170, on=0)
        # oars + hands
        for side in (-1, 1):
            hx = W / 2 + side * lerp(150, 230, pull)
            hy = H * lerp(0.98, 0.9, pull)
            tip = (W / 2 + side * (W * 0.7), H * lerp(0.62, 0.7, pull))
            cv.drawPath(path([(hx, hy), tip]), stroke((170, 120, 70), 16))
            cv.drawPath(path([(hx, hy), tip]), stroke(INK, 2))
            cv.drawCircle(hx, hy, 26, fill(INK))
            cv.drawPath(path([(hx, hy), (W / 2 + side * 120, H * 1.15)]), stroke(INK, 12))
        cv.restore()
    fog_bank(cv, W, H, t, H * 0.45, H * 0.65, 10, 50, seed=8)
    grain_vignette(cv, W, H, 180)


# 9 ---------------------------------------------------------------------------
def s9(cv, W, H, t, T):
    u = t / T
    on = 1.0 if u > 0.3 else 0.0
    cam = Cam(W, H, zoom=1.0 + (0.04 * math.sin(t * 40) * clamp01((u - 0.3) * 4) * (1 - u)))
    with cam.layer(cv, 0.0):
        night_sky(cv, W, H, t)
        sea(cv, W, H, H * 0.5, t, night=True)
    with cam.layer(cv, 1.0):
        p = Pose(eyes="narrow", mouth="smirk", brow=-0.6, look=(0.6, 0.6))
        draw_character(cv, "gus", W * 0.3, H * 1.0, 125, p)
        fog_machine(cv, W * 0.45, H * 1.12, 700, on=on)
        # finger on switch
        fx, fy = W * 0.45 + 700 * 0.125, H * 1.12 + 700 * (-0.3 if on else -0.36)
        cv.drawPath(path([(fx - 160, fy + 160), (fx, fy)]), stroke(INK, 16))
        cv.drawCircle(fx, fy, 22, fill(INK))
        if on:
            fog_jet(cv, W * 0.45 + 700 * 0.66, H * 1.12 - 700 * 0.33, 160, clamp01((u - 0.3) * 2.5), t, seed=5)
            cv.drawRect(skia.Rect.MakeWH(W, H), fill((230, 235, 240), 120 * ease(clamp01((u - 0.55) * 2))))
    grain_vignette(cv, W, H, 160)


# 10 --------------------------------------------------------------------------
def s10(cv, W, H, t, T):
    u = t / T
    cam = Cam(W, H, zoom=push(u, 1.0, 1.2), dy=lerp(220, 0, ease(u)))
    with cam.layer(cv, 0.0):
        night_sky(cv, W, H, t)
    with cam.layer(cv, 0.4):
        sea(cv, W, H, H * 0.45, t, night=True)
        lp, _ = island(cv, W * 0.55, H * 0.62, 140, t, lamp=1.0, night=True)
        for i, (sx, sy) in enumerate(((0.15, 0.55), (0.88, 0.7), (0.3, 0.8))):
            if math.sin(t * 3 + i * 2) > 0:
                glow(cv, W * sx, H * sy, 30, (255, 80, 80), 180)
    with cam.layer(cv, 0.7):
        fog_bank(cv, W, H, t, H * 0.4, H * 1.05, 60, 170, seed=1, speed=18, rmin=100, rmax=260)
        beam(cv, lp, t * 1.1, W * 1.2, 140, 170)
    grain_vignette(cv, W, H, 150)


# 11 --------------------------------------------------------------------------
def s11(cv, W, H, t, T):
    u = t / T
    ba = clamp01(1 - abs(u - 0.55) / 0.18)
    relief = u > 0.6
    cam = Cam(W, H, zoom=push(u, 1.0, 1.1), cy=H * 0.5)
    ship_bridge(cv, cam, W, H, t, beam_amt=ba)
    with cam.layer(cv, 1.0):
        sp = 0 if relief else math.sin(t * 9) * 25
        p = Pose(eyes="happy" if relief else "wide", mouth="smile" if relief else "open",
                 sweat=0 if relief else (t * 0.8) % 1, brow=0.4 if relief else 1.0,
                 hand_l=(-1.4, -2.9 + sp / 200), hand_r=(1.4, -2.9 - sp / 200), bob=0 if relief else abs(math.sin(t * 9)) * 0.1)
        draw_character(cv, "captain", W * 0.5, H * 1.02, 110, p)
        ships_wheel(cv, W * 0.5, H * 0.95, 150, sp * 2 + t * 10)
    if ba:
        cv.drawRect(skia.Rect.MakeWH(W, H), fill((255, 225, 150), 70 * ba, blend=skia.BlendMode.kPlus))
    grain_vignette(cv, W, H, 180)


# 12 --------------------------------------------------------------------------
def s12(cv, W, H, t, T):
    u = t / T
    cam = Cam(W, H, zoom=1.08, dx=lerp(-30, 30, ease(u)))
    lamp_room(cv, cam, W, H, t, night=True, beam_ang=t * 1.4, lens_x=0.85)
    with cam.layer(cv, 0.9):
        lantern(cv, W * 0.12, H * 0.72, 46)
        cv.drawRect(skia.Rect.MakeLTRB(W * 0.08, H * 0.72, W * 0.92, H * 0.74), fill((130, 85, 50)))
        cv.drawRect(skia.Rect.MakeLTRB(W * 0.08, H * 0.72, W * 0.92, H * 0.74), stroke(INK, 3))
        n = 3 + int(t * 3)
        cash_stack(cv, W * 0.7, H * 0.72, 110, min(n, 22))
    with cam.layer(cv, 1.0):
        flick = (t * 3) % 1
        p = Pose(eyes="happy", mouth="grin", hand_l=(-1.2, -2.0), hand_r=(lerp(0.9, 2.2, flick), lerp(-2.0, -2.3, flick)),
                 bob=abs(math.sin(t * 6)) * 0.04)
        draw_character(cv, "gus", W * 0.42, H * 0.98, 92, p)
        bx = W * 0.42 + lerp(0.9, 2.2, flick) * 92
        by = H * 0.98 - 92 * 3 * 0 + lerp(-2.0, -2.3, flick) * 92
        bill(cv, bx, by - flick * 40, 60, flick * 160)
    grain_vignette(cv, W, H, 170)


# 13 --------------------------------------------------------------------------
def s13(cv, W, H, t, T):
    u = t / T
    cam = Cam(W, H, zoom=1.05, dx=lerp(50, -50, u))
    dock_night(cv, cam, W, H, t)
    with cam.layer(cv, 1.0):
        sink = ease(clamp01((u - 0.5) / 0.3)) * 18
        bx, by = W * 0.62, H * 0.74 + sink
        cv.save(); cv.clipRect(skia.Rect.MakeLTRB(0, 0, W, H * 0.8))
        rowboat(cv, bx, by, 190, rock=math.sin(t * 1.5) * 2)
        for i, (ox, oy) in enumerate(((-110, 0), (-30, -6), (50, -2), (-70, -60), (10, -64))):
            fog_machine(cv, bx + ox, by - 40 + oy, 85)
        cv.restore()
        # Gus lifting one more
        lift = ease(clamp01(u / 0.5))
        p = Pose(eyes="dot", mouth="smile", hand_l=(0.6, -3.2 - lift * 0.4), hand_r=(1.7, -3.2 - lift * 0.4),
                 lean=-8 * lift, squash=0.2 * (1 - lift))
        draw_character(cv, "gus", W * 0.28, H * 0.86, 62, p)
        if u < 0.65:
            fog_machine(cv, W * 0.28 + 72, H * 0.86 - 62 * (3.1 + lift * 0.4), 95)
        else:
            fog_machine(cv, bx + 100, by - 120 + 70 * ease(clamp01((u - 0.65) / 0.2)), 85)
    grain_vignette(cv, W, H, 170)


# 14 --------------------------------------------------------------------------
def s14(cv, W, H, t, T):
    u = t / T
    cam = Cam(W, H, zoom=push(u, 1.35, 1.0), dy=lerp(-80, 40, ease(u)), cy=H * 0.5)
    with cam.layer(cv, 0.0):
        night_sky(cv, W, H, t, moon=(0.8, 0.1))
    with cam.layer(cv, 0.5):
        sea(cv, W, H, H * 0.45, t, night=True)
        lp, _ = island(cv, W * 0.5, H * 0.72, 150, t, lamp=1.0, night=True)
        fog_bank(cv, W, H, t, H * 0.38, H * 1.2, 90, 235, seed=2, speed=10, rmin=110, rmax=260)
        lighthouse(cv, W * 0.5 - 150 * 0.15, H * 0.72 - 150 * 0.3, 150 * 1.25, 1.0)  # tip pokes out
        fog_bank(cv, W, H, t + 3, H * 0.62, H * 1.2, 40, 230, seed=9, speed=12, rmin=120, rmax=260)
        beam(cv, lp, t * 1.2, W * 1.3, 120, 170)
    grain_vignette(cv, W, H, 150)


# 15 --------------------------------------------------------------------------
def s15(cv, W, H, t, T):
    u = t / T
    cam = Cam(W, H, zoom=push(u, 1.0, 1.12), cy=H * 0.62)
    dock_night(cv, cam, W, H, t, mist=1.6)
    with cam.layer(cv, 1.0):
        arrive = ease(clamp01(u / 0.4))
        pi = Pose(eyes="dot", mouth="flat", walk=None if arrive >= 1 else t * 8, blink=blink(t, 2.3),
                  hand_r=(1.4, -2.4), hand_l=(-1.2, -1.6))
        def clip(cv_, p):
            x, y = p.hand_r
            r = skia.Rect.MakeLTRB(x - 0.15, y - 0.9, x + 0.55, y + 0.1)
            cv_.drawRect(r, fill((180, 140, 90))); cv_.drawRect(r, stroke(INK, 0.05))
            cv_.drawRect(skia.Rect.MakeLTRB(x - 0.05, y - 0.8, x + 0.45, y), fill((250, 250, 245)))
        draw_character(cv, "inspector", lerp(W * 1.05, W * 0.64, arrive), H * 0.86, 62, pi, flip=True, props=[clip])
        pg = Pose(eyes="wide", mouth="flat", sweat=clamp01((u - 0.4) * 1.5), look=(0.8, 0), brow=0.6)
        draw_character(cv, "gus", W * 0.3, H * 0.88, 64, pg)
    fog_bank(cv, W, H, t, H * 0.75, H * 1.0, 14, 90, seed=31, speed=10)
    grain_vignette(cv, W, H, 170)


# 16 --------------------------------------------------------------------------
def s16(cv, W, H, t, T):
    u = t / T
    cam = Cam(W, H, zoom=1.0)
    dock_night(cv, cam, W, H, t, mist=2.0)
    cv.drawRect(skia.Rect.MakeWH(W, H), fill((200, 210, 220), 60))
    with cam.layer(cv, 1.0):
        delight = ease(clamp01((u - 0.35) / 0.15))
        scrib = math.sin(t * 25) * 0.12 if u > 0.5 else 0
        p = Pose(eyes="happy" if delight > 0.5 else "dot", brow=delight * 1.3, mouth="grin" if delight > 0.5 else "flat",
                 hand_l=(-0.9 + scrib, -1.9), hand_r=(0.6, -2.0), look=(0.6, -0.3))
        def clip(cv_, p_):
            r = skia.Rect.MakeLTRB(-0.2, -2.9, 1.2, -1.6)
            cv_.drawRect(r, fill((180, 140, 90))); cv_.drawRect(r, stroke(INK, 0.05))
            cv_.drawRect(skia.Rect.MakeLTRB(-0.1, -2.8, 1.1, -1.7), fill((250, 250, 245)))
            if u > 0.5:
                pts = [(0.0 + i * 0.05, -2.6 + (i // 20) * 0.2 + math.sin(i * 2.1) * 0.04) for i in range(int((u - 0.5) * 120))]
                if len(pts) > 1:
                    cv_.drawPath(path([(x % 1.1, y) for x, y in pts]), stroke((40, 40, 120), 0.03))
        draw_character(cv, "inspector", W * 0.48, H * 1.2, 170, p, props=[clip])
    fog_bank(cv, W, H, t, H * 0.0, H * 0.6, 12, 60, seed=41, speed=14)
    grain_vignette(cv, W, H, 150)


# 17 --------------------------------------------------------------------------
def s17(cv, W, H, t, T):
    u = t / T
    cam = Cam(W, H, zoom=push(u, 1.4, 1.0), cx=W * 0.68, cy=H * 0.48)
    with cam.layer(cv, 0.0):
        sky_day(cv, W, H, t)
    with cam.layer(cv, 0.4):
        sea(cv, W, H, H * 0.5, t)
    with cam.layer(cv, 0.8):
        lit = 1.0 if (u > 0.35 and (u > 0.5 or (t * 12) % 2 > 1)) else 0.0
        lp, lp2 = island(cv, W * 0.42, H * 0.62, 210, t, lamp=0.3, second=1.0 if lit else 0.99)
        # rival waving on the new gallery
        gx, gy = W * 0.42 + 210 * 0.65, H * 0.62 - 210 * 0.22 - 210 * 1.05 * 0.88
        wave = math.sin(t * 8)
        p = Pose(eyes="narrow", mouth="smirk", hand_r=(1.2 + wave * 0.3, -4.3), hand_l=(-1.1, -1.7))
        draw_character(cv, "rival", gx + 30, gy + 4, 11, p)
    with cam.layer(cv, 1.0):
        gulls(cv, W, H, t, 3, seed=7)
    grain_vignette(cv, W, H, 110)


# 18 --------------------------------------------------------------------------
def s18(cv, W, H, t, T):
    u = t / T
    cam = Cam(W, H, zoom=1.05, dx=lerp(40, -40, u))
    dock_night(cv, cam, W, H, t, high=True)
    with cam.layer(cv, 1.0):
        x = lerp(W * 0.25, W * 0.72, u)
        step = t * 3.2
        look = math.sin(t * 2.4)
        def carry(cv_, p):
            fog_machine(cv_, 0.0, -1.4, 1.9)
        p = Pose(eyes="narrow", mouth="smirk", walk=step, bob=abs(math.sin(step)) * 0.35, lean=-6,
                 hand_l=(-0.9, -2.2), hand_r=(0.9, -2.2), look=(look, 0))
        draw_character(cv, "rival", x, H * 0.74, 34, p, flip=look < 0, props=[carry])
    # window frame of Gus's lighthouse (we are looking down from it)
    frame = skia.Path(); frame.addRect(skia.Rect.MakeLTRB(-10, -10, W + 10, H + 10))
    hole = skia.Path(); hole.addCircle(W / 2, H * 0.55, W * 0.62)
    frame = skia.Op(frame, hole, skia.PathOp.kDifference_PathOp)
    cv.drawPath(frame, fill((40, 30, 28)))
    cv.drawCircle(W / 2, H * 0.55, W * 0.62, stroke((170, 130, 60), 18))
    grain_vignette(cv, W, H, 120)


# 19 --------------------------------------------------------------------------
def s19(cv, W, H, t, T):
    u = t / T
    cam = Cam(W, H, zoom=push(u, 1.0, 1.18), cy=H * 0.5)
    lamp_room(cv, cam, W, H, t, night=True, beam_ang=t * 1.4, lens_x=1.1)
    cv.drawRect(skia.Rect.MakeWH(W, H), fill((10, 10, 25), 80))
    with cam.layer(cv, 1.0):
        tw = 0.0
        for k in (0.35, 0.55):
            if k < u < k + 0.06:
                tw = 1.0
        p = Pose(eyes="half", mouth="flat", twitch=tw, blink=0)
        draw_character(cv, "gus", W * 0.5, H * 1.25, 190, p)
    beam(cv, (W * -0.2, H * 0.25), t * 1.4, W * 1.5, 200, 50)
    grain_vignette(cv, W, H, 200)


SHOTS = {i: globals()[f"s{i}"] for i in range(1, 20)}
