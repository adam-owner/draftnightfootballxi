"""
Drawing primitives for the offline (no-API) renderer.

Characters follow the reference style: big round white head, thick dark-brown
outline, minimal face, bean-shaped torso that is the outfit, stick limbs,
an iconic hat. Everything is vector-drawn with skia, so it stays crisp.
"""
import math
import random

import skia

INK = (43, 27, 18)          # outline colour
SKIN = (250, 248, 242)      # head white


def _c8(v):
    return max(0, min(255, int(v)))


def C(rgb, a=255):
    return skia.Color(_c8(rgb[0]), _c8(rgb[1]), _c8(rgb[2]), _c8(a))


def fill(rgb, a=255, blend=None):
    p = skia.Paint(AntiAlias=True, Color=C(rgb, a))
    if blend:
        p.setBlendMode(blend)
    return p


def stroke(rgb, w, a=255, cap=skia.Paint.kRound_Cap):
    return skia.Paint(AntiAlias=True, Color=C(rgb, a), Style=skia.Paint.kStroke_Style,
                      StrokeWidth=w, StrokeCap=cap, StrokeJoin=skia.Paint.kRound_Join)


def lin(p0, p1, cols, pos=None):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeLinear(
        [skia.Point(*p0), skia.Point(*p1)], [C(*c) if isinstance(c[0], tuple) else C(c) for c in cols], pos))
    return p


def rad(center, r, cols, pos=None, blend=None):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(
        skia.Point(*center), max(r, 0.1), [C(*c) if isinstance(c[0], tuple) else C(c) for c in cols], pos))
    if blend:
        p.setBlendMode(blend)
    return p


def lerp(a, b, t):
    return a + (b - a) * t


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def clamp01(t):
    return max(0.0, min(1.0, t))


def path(points, close=False, smooth=False):
    p = skia.Path()
    p.moveTo(*points[0])
    if smooth and len(points) > 2:
        for i in range(1, len(points) - 1):
            mx = (points[i][0] + points[i + 1][0]) / 2
            my = (points[i][1] + points[i + 1][1]) / 2
            p.quadTo(points[i][0], points[i][1], mx, my)
        p.lineTo(*points[-1])
    else:
        for q in points[1:]:
            p.lineTo(*q)
    if close:
        p.close()
    return p


def outlined(cv, pth, rgb, w, a=255, ink=INK):
    cv.drawPath(pth, fill(rgb, a))
    cv.drawPath(pth, stroke(ink, w, a))


def soft_shadow(cv, x, y, rx, ry, a=90):
    cv.save()
    cv.translate(x, y)
    cv.scale(1, ry / rx)
    cv.drawCircle(0, 0, rx, rad((0, 0), rx, [((0, 0, 0), a), ((0, 0, 0), 0)]))
    cv.restore()


def glow(cv, x, y, r, rgb, a=160):
    cv.drawCircle(x, y, r, rad((x, y), r, [(rgb, a), (rgb, a * 0.35), (rgb, 0)], [0, 0.35, 1],
                               blend=skia.BlendMode.kPlus))


def puff(cv, x, y, r, a=110, rgb=(235, 240, 245)):
    cv.drawCircle(x, y, r, rad((x, y), r, [(rgb, a), (rgb, a * 0.6), (rgb, 0)], [0, 0.45, 1]))


def fog_bank(cv, W, H, t, y0, y1, density=40, a=90, seed=1, speed=20, rmin=80, rmax=220):
    rnd = random.Random(seed)
    for _ in range(density):
        x = rnd.uniform(-200, W + 200)
        y = rnd.uniform(y0, y1)
        r = rnd.uniform(rmin, rmax)
        sp = rnd.uniform(0.5, 1.5) * speed
        xx = (x + t * sp) % (W + 400) - 200
        puff(cv, xx, y + math.sin(t * 0.7 + x) * 6, r, a)


def stars(cv, W, H, t, n=120, ymax=None, seed=3):
    rnd = random.Random(seed)
    ymax = ymax or H * 0.5
    for _ in range(n):
        x, y = rnd.uniform(0, W), rnd.uniform(0, ymax)
        tw = 0.6 + 0.4 * math.sin(t * rnd.uniform(1, 4) + x)
        cv.drawCircle(x, y, rnd.uniform(0.7, 2.0), fill((255, 255, 240), 200 * tw))


def grain_vignette(cv, W, H, strength=150):
    cv.drawRect(skia.Rect.MakeWH(W, H),
                rad((W / 2, H * 0.45), H * 0.75, [((0, 0, 0), 0), ((0, 0, 0), 0), ((0, 0, 0), strength)],
                    [0, 0.55, 1]))


# ----------------------------------------------------------------------------
# Characters
# ----------------------------------------------------------------------------
CAST = {
    "gus": dict(hat="souwester", torso="sweater", torso_rgb=(38, 58, 110), beard=True,
                hair=None, brows="bushy", glasses=False, moustache=None),
    "inspector": dict(hat="bowler", torso="suit", torso_rgb=(128, 132, 140), beard=False,
                      hair=None, brows="thin", glasses=True, moustache="thin"),
    "rival": dict(hat="beanie", torso="stripes", torso_rgb=(220, 50, 50), beard=False,
                  hair="slick", brows="sly", glasses=False, moustache=None),
    "captain": dict(hat="captain", torso="peacoat", torso_rgb=(30, 42, 78), beard=False,
                    hair=None, brows="thick", glasses=False, moustache=None, stubble=True),
    "adam": dict(hat=None, torso="blazer", torso_rgb=(34, 44, 80), beard=False,
                 hair="messy", brows="thin", glasses=False, moustache=None),
    "double": dict(hat=None, torso="blazer", torso_rgb=(34, 44, 80), beard=False,
                   hair="messy", brows="thin", glasses=False, moustache=None),
    "mom": dict(hat=None, torso="robe", torso_rgb=(232, 160, 175), beard=False,
                hair="bun", brows="thin", glasses=False, moustache=None),
}

HAIR_RGB = {"messy": (92, 58, 34), "bun": (48, 30, 24), "slick": (25, 22, 24)}


class Pose:
    """All animatable bits of a character for one frame."""

    def __init__(self, **kw):
        self.bob = 0.0            # vertical offset (head units)
        self.lean = 0.0           # degrees
        self.hand_l = (-1.25, -1.6)   # hand targets relative to feet, head units (x left negative)
        self.hand_r = (1.25, -1.6)
        self.walk = None          # phase (radians) or None
        self.sit = False
        self.eyes = "dot"         # dot | half | wide | happy | closed | narrow
        self.blink = 0.0
        self.brow = 0.0           # -1 angry .. +1 raised
        self.mouth = "flat"       # flat | smile | grin | open | frown | smirk | none
        self.look = (0.0, 0.0)    # pupil offset
        self.sweat = 0.0          # 0..1 drop progress (0 = none)
        self.twitch = 0.0         # 0..1 squint on one eye
        self.hat_droop = 0.0
        self.wet = 0.0
        self.squash = 0.0
        self.back = False         # seen from behind: no face
        self.blank = False        # face with no features (the double)
        self.head_turn = 0.0      # 0 = back of head, 1 = face fully turned to camera (body stays)
        self.head_tilt = 0.0      # degrees, head only, about the neck
        self.grin = 1.0           # width of the creepy grin
        self.straps = False       # backpack straps over the shoulders
        self.__dict__.update(kw)


def _limb(cv, a, b, w, bend=0.0):
    (x0, y0), (x1, y1) = a, b
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    dx, dy = x1 - x0, y1 - y0
    nx, ny = -dy, dx
    p = skia.Path()
    p.moveTo(x0, y0)
    p.quadTo(mx + nx * bend, my + ny * bend, x1, y1)
    cv.drawPath(p, stroke(INK, w))


def draw_character(cv, who, x, y, scale, pose=None, flip=False, props=None):
    """Draw a character with feet centred at (x, y). scale = head radius in px."""
    spec = CAST[who]
    pose = pose or Pose()
    R = 1.0
    ow = 0.085                       # outline width in head units
    cv.save()
    cv.translate(x, y)
    cv.scale(scale * (-1 if flip else 1), scale)
    soft_shadow(cv, 0, 0, 1.25, 0.28, 110)
    cv.rotate(pose.lean)
    sq = pose.squash
    bob = pose.bob
    cv.translate(0, -bob)
    cv.scale(1 + sq * 0.15, 1 - sq * 0.15)

    # legs
    hip_y = -1.25
    if pose.sit:
        _limb(cv, (-0.3, hip_y), (-0.55, -0.15), 0.11, 0.15)
        _limb(cv, (0.3, hip_y), (0.55, -0.15), 0.11, -0.15)
        cv.drawPath(path([(-0.55, -0.15), (-0.85, -0.1)]), stroke(INK, 0.14))
        cv.drawPath(path([(0.55, -0.15), (0.85, -0.1)]), stroke(INK, 0.14))
    else:
        if pose.walk is not None:
            s = math.sin(pose.walk)
            fl, fr = (-0.3 + 0.45 * s, -max(0, -s) * 0.25), (0.3 - 0.45 * s, -max(0, s) * 0.25)
        else:
            fl, fr = (-0.38, 0.0), (0.38, 0.0)
        for hx, f in ((-0.28, fl), (0.28, fr)):
            _limb(cv, (hx, hip_y + bob), f, 0.11, 0.04)
            cv.drawPath(path([(f[0], f[1]), (f[0] + (0.2 if f[0] > 0 else -0.2), f[1])]), stroke(INK, 0.14))

    shoulder = (-0.62, -2.55), (0.62, -2.55)

    def arm(side):
        s = shoulder[0] if side == "l" else shoulder[1]
        h = pose.hand_l if side == "l" else pose.hand_r
        _limb(cv, s, h, 0.1, 0.12 if side == "l" else -0.12)
        cv.drawCircle(h[0], h[1], 0.15, fill(INK))

    arm("l")

    # torso (bean)
    tor = skia.Path()
    tor.moveTo(-0.72, -2.85)
    tor.cubicTo(-0.95, -2.2, -0.95, -1.4, -0.7, -1.15)
    tor.cubicTo(-0.4, -1.0, 0.4, -1.0, 0.7, -1.15)
    tor.cubicTo(0.95, -1.4, 0.95, -2.2, 0.72, -2.85)
    tor.close()
    trgb = spec["torso_rgb"]
    cv.drawPath(tor, fill(trgb))
    cv.save()
    cv.clipPath(tor, doAntiAlias=True)
    kind = spec["torso"]
    if kind == "sweater":
        for xx in (-0.45, -0.15, 0.15, 0.45):
            for k in range(7):
                yy = -2.75 + k * 0.23
                cv.drawPath(path([(xx - 0.07, yy), (xx, yy + 0.1), (xx + 0.07, yy)]),
                            stroke((70, 92, 150), 0.05))
        cv.drawRect(skia.Rect.MakeLTRB(-1, -1.35, 1, -1.0), fill((28, 44, 86)))
    elif kind == "suit":
        cv.drawPath(path([(-0.35, -2.85), (0, -2.15), (0.35, -2.85)], close=True), fill((245, 245, 240)))
        cv.drawPath(path([(-0.08, -2.7), (0.08, -2.7), (0.12, -1.9), (0, -1.75), (-0.12, -1.9)], close=True),
                    fill((200, 30, 40)))
        cv.drawPath(path([(-0.35, -2.85), (0, -2.15)]), stroke(INK, 0.05))
        cv.drawPath(path([(0.35, -2.85), (0, -2.15)]), stroke(INK, 0.05))
        for yy in (-1.9, -1.6):
            cv.drawCircle(0.0, yy, 0.05, fill(INK))
    elif kind == "stripes":
        for k in range(9):
            if k % 2:
                cv.drawRect(skia.Rect.MakeLTRB(-1, -2.9 + k * 0.2, 1, -2.9 + (k + 1) * 0.2), fill((250, 245, 240)))
    elif kind == "blazer":
        cv.drawPath(path([(-0.42, -2.88), (0, -2.2), (0.42, -2.88)], close=True), fill((245, 245, 242)))
        if not pose.back:
            tie = path([(-0.08, -2.75), (0.08, -2.75), (0.13, -2.0), (0, -1.85), (-0.13, -2.0)], close=True)
            cv.drawPath(tie, fill((180, 30, 40)))
            for k in range(4):
                cv.drawPath(path([(-0.12, -2.6 + k * 0.18), (0.12, -2.5 + k * 0.18)]), stroke((240, 200, 80), 0.035))
            cv.drawPath(path([(-0.42, -2.88), (-0.05, -2.1)]), stroke((20, 26, 50), 0.06))
            cv.drawPath(path([(0.42, -2.88), (0.05, -2.1)]), stroke((20, 26, 50), 0.06))
            cv.drawCircle(0.5, -2.2, 0.12, fill((214, 170, 60)))
        else:
            cv.drawRect(skia.Rect.MakeLTRB(-1, -2.95, 1, -2.7), fill((34, 44, 80)))
            cv.drawPath(path([(0, -2.7), (0, -1.15)]), stroke((20, 26, 50), 0.05))
    elif kind == "robe":
        cv.drawPath(path([(-0.4, -2.9), (0.15, -1.9), (0.4, -2.9)], close=True), fill((245, 200, 210)))
        cv.drawRect(skia.Rect.MakeLTRB(-1, -1.85, 1, -1.7), fill((200, 120, 140)))
        cv.drawPath(path([(-0.4, -2.9), (0.15, -1.9)]), stroke((190, 110, 130), 0.05))
    elif kind == "peacoat":
        for yy in (-2.4, -2.0, -1.6):
            for xx in (-0.25, 0.25):
                cv.drawCircle(xx, yy, 0.07, fill((214, 170, 60)))
        cv.drawPath(path([(-0.4, -2.85), (0, -2.45), (0.4, -2.85)]), stroke((20, 28, 54), 0.08))
    # wet sheen
    if pose.wet:
        cv.drawRect(skia.Rect.MakeLTRB(-1, -3, 1, -1), fill((150, 180, 220), 60 * pose.wet))
    cv.restore()
    cv.drawPath(tor, stroke(INK, ow))

    if pose.straps and not pose.back:
        for sx in (-1, 1):
            cv.drawPath(path([(sx * 0.55, -2.85), (sx * 0.62, -1.6)]), stroke((90, 96, 104), 0.16))
            cv.drawPath(path([(sx * 0.55, -2.85), (sx * 0.62, -1.6)]), stroke(INK, 0.03))

    # head (tilts about the neck independently of the body)
    hy = -3.55
    cv.save()
    if pose.head_tilt:
        cv.rotate(pose.head_tilt, 0, -2.75)
    if pose.back and spec.get("hair"):
        for sx in (-1, 1):   # ears from behind
            cv.drawOval(skia.Rect.MakeLTRB(sx * 1.08 - 0.16, hy - 0.2, sx * 1.08 + 0.16, hy + 0.25), fill(SKIN))
            cv.drawOval(skia.Rect.MakeLTRB(sx * 1.08 - 0.16, hy - 0.2, sx * 1.08 + 0.16, hy + 0.25), stroke(INK, 0.06))
    cv.drawCircle(0, hy, R, fill(SKIN))
    cv.drawCircle(0.25, hy + 0.3, R * 0.75, rad((0.25, hy + 0.35), 0.9, [((215, 210, 200), 0), ((215, 210, 200), 90)]))
    if pose.back and pose.head_turn > 0:
        # fake 3D head rotation: face slides in from one side, back hair slides out the other
        head = skia.Path(); head.addCircle(0, hy, R)
        cv.save(); cv.clipPath(head, doAntiAlias=True)
        tw = pose.head_turn
        cv.save(); cv.translate(-1.9 * (1 - tw), 0)
        _face(cv, spec, pose, hy)
        if spec.get("hair"):
            fp = Pose(**{k: v for k, v in pose.__dict__.items()}); fp.back = False
            _hair(cv, spec["hair"], hy, fp)
        cv.restore()
        cv.save(); cv.translate(1.9 * tw, 0)
        if spec.get("hair"):
            _hair(cv, spec["hair"], hy, pose)
        cv.restore()
        cv.restore()
        cv.drawCircle(0, hy, R, stroke(INK, ow))
    else:
        cv.drawCircle(0, hy, R, stroke(INK, ow))
        if not pose.back and not pose.blank:
            _face(cv, spec, pose, hy)
        if spec.get("hair"):
            _hair(cv, spec["hair"], hy, pose)
    if spec.get("hat"):
        _hat(cv, spec["hat"], hy, pose)
    cv.restore()

    arm("r")
    if props:
        for fn in props:
            fn(cv, pose)
    cv.restore()


def _eye(cv, ex, ey, kind, blink, look, twitch=0.0):
    k = kind
    if blink > 0.6 and kind != "creepy":
        k = "closed"
    lx, ly = look
    if k == "dot":
        cv.drawCircle(ex + lx * 0.06, ey + ly * 0.06, 0.095, fill(INK))
    elif k == "half":
        cv.drawCircle(ex + lx * 0.05, ey + 0.04, 0.085, fill(INK))
        cv.drawPath(path([(ex - 0.16, ey - 0.03), (ex + 0.16, ey - 0.03)]), stroke(INK, 0.07))
    elif k == "narrow":
        cv.drawPath(path([(ex - 0.15, ey), (ex + 0.15, ey - 0.02)]), stroke(INK, 0.08))
    elif k == "wide":
        cv.drawCircle(ex, ey, 0.2, fill((255, 255, 255)))
        cv.drawCircle(ex, ey, 0.2, stroke(INK, 0.05))
        cv.drawCircle(ex + lx * 0.08, ey + ly * 0.08, 0.075, fill(INK))
    elif k == "creepy":
        cv.drawCircle(ex, ey, 0.27, fill((255, 255, 255)))
        cv.drawCircle(ex, ey, 0.27, stroke(INK, 0.06))
        cv.drawCircle(ex + lx * 0.05, ey + ly * 0.05, 0.045, fill(INK))
        return
    elif k == "happy":
        p = skia.Path()
        p.moveTo(ex - 0.15, ey + 0.05)
        p.quadTo(ex, ey - 0.15, ex + 0.15, ey + 0.05)
        cv.drawPath(p, stroke(INK, 0.07))
    else:  # closed
        p = skia.Path()
        p.moveTo(ex - 0.15, ey)
        p.quadTo(ex, ey + 0.08, ex + 0.15, ey)
        cv.drawPath(p, stroke(INK, 0.07))
    if twitch > 0:
        cv.drawPath(path([(ex - 0.17, ey - 0.08 + twitch * 0.06), (ex + 0.17, ey - 0.02 + twitch * 0.07)]),
                    stroke(INK, 0.06))


def _face(cv, spec, pose, hy):
    ey = hy + 0.05
    _eye(cv, -0.33, ey, pose.eyes, pose.blink, pose.look)
    _eye(cv, 0.33, ey, pose.eyes, pose.blink, pose.look, pose.twitch)
    b = pose.brow
    if spec["brows"] == "bushy":
        for sx in (-1, 1):
            p = path([(sx * 0.15, ey - 0.25 - b * 0.08 - (0.05 if sx > 0 else 0) * b),
                      (sx * 0.33, ey - 0.33 - b * 0.12),
                      (sx * 0.52, ey - 0.27 - b * 0.05)], smooth=True)
            cv.drawPath(p, stroke((235, 235, 235), 0.14))
            cv.drawPath(p, stroke(INK, 0.03))
    else:
        w = {"thin": 0.04, "sly": 0.06, "thick": 0.08}.get(spec["brows"], 0.05)
        for sx in (-1, 1):
            inner = ey - 0.24 - b * 0.1 + (0.05 if spec["brows"] == "sly" and sx < 0 else 0)
            outer = ey - 0.3 - b * 0.05
            cv.drawPath(path([(sx * 0.18, inner), (sx * 0.47, outer)]), stroke(INK, w))
    if spec.get("glasses"):
        for sx in (-0.33, 0.33):
            cv.drawCircle(sx, ey, 0.24, stroke((90, 80, 70), 0.035))
            cv.drawCircle(sx, ey, 0.24, fill((200, 230, 255), 40))
        cv.drawPath(path([(-0.09, ey), (0.09, ey)]), stroke((90, 80, 70), 0.035))
    my = hy + 0.45
    if spec.get("beard"):
        beard = skia.Path()
        pts = []
        for i in range(13):
            a = math.pi * (0.05 + 0.9 * i / 12)
            rr = 0.95 + (0.12 if i % 2 else 0)
            pts.append((math.cos(a) * rr * 0.98, hy + 0.2 + math.sin(a) * rr * 0.95))
        beard.moveTo(-0.92, hy + 0.15)
        for q in pts[::-1]:
            beard.lineTo(*q)
        beard.lineTo(0.92, hy + 0.15)
        beard.quadTo(0.5, hy + 0.32, 0, hy + 0.3)
        beard.quadTo(-0.5, hy + 0.32, -0.92, hy + 0.15)
        beard.close()
        cv.drawPath(beard, fill((240, 240, 238)))
        cv.drawPath(beard, stroke(INK, 0.06))
        # moustache
        for sx in (-1, 1):
            p = skia.Path()
            p.moveTo(0, hy + 0.32)
            p.quadTo(sx * 0.25, hy + 0.2, sx * 0.45, hy + 0.36)
            cv.drawPath(p, stroke((215, 215, 212), 0.12))
        my = hy + 0.55
    if spec.get("stubble"):
        for i in range(18):
            a = math.pi * (0.2 + 0.6 * i / 17)
            cv.drawCircle(math.cos(a) * 0.7, hy + 0.15 + math.sin(a) * 0.62, 0.025, fill((140, 140, 140)))
    if spec.get("moustache") == "thin":
        for sx in (-1, 1):
            p = skia.Path()
            p.moveTo(0, hy + 0.36)
            p.quadTo(sx * 0.2, hy + 0.3, sx * 0.33, hy + 0.36 - (0.06 if pose.mouth in ("grin", "smile") else 0))
            cv.drawPath(p, stroke(INK, 0.06))
    m = pose.mouth
    if m == "flat":
        cv.drawPath(path([(-0.1, my), (0.1, my)]), stroke(INK, 0.06))
    elif m == "smile":
        p = skia.Path(); p.moveTo(-0.18, my - 0.03); p.quadTo(0, my + 0.13, 0.18, my - 0.03)
        cv.drawPath(p, stroke(INK, 0.06))
    elif m == "smirk":
        p = skia.Path(); p.moveTo(-0.15, my); p.quadTo(0.05, my + 0.06, 0.2, my - 0.08)
        cv.drawPath(p, stroke(INK, 0.06))
    elif m == "grin":
        p = skia.Path(); p.moveTo(-0.3, my - 0.06); p.quadTo(0, my - 0.02, 0.3, my - 0.06)
        p.quadTo(0, my + 0.38, -0.3, my - 0.06); p.close()
        cv.drawPath(p, fill((90, 30, 30)));
        cv.save(); cv.clipPath(p, doAntiAlias=True)
        cv.drawRect(skia.Rect.MakeLTRB(-0.4, my - 0.1, 0.4, my + 0.06), fill((255, 255, 255)))
        cv.restore()
        cv.drawPath(p, stroke(INK, 0.05))
    elif m == "open":
        cv.drawOval(skia.Rect.MakeLTRB(-0.14, my - 0.08, 0.14, my + 0.22), fill((90, 30, 30)))
        cv.drawOval(skia.Rect.MakeLTRB(-0.14, my - 0.08, 0.14, my + 0.22), stroke(INK, 0.05))
    elif m == "creepy":
        g = pose.grin
        w = 0.35 + 0.55 * g
        top = my - 0.12 - 0.18 * g
        p = skia.Path(); p.moveTo(-w, top - 0.12 * g)
        p.quadTo(0, top + 0.08, w, top - 0.12 * g)
        p.quadTo(w * 0.55, my + 0.5 * g, 0, my + 0.55 * g)
        p.quadTo(-w * 0.55, my + 0.5 * g, -w, top - 0.12 * g); p.close()
        cv.drawPath(p, fill((70, 10, 14)))
        cv.save(); cv.clipPath(p, doAntiAlias=True)
        cv.drawRect(skia.Rect.MakeLTRB(-1, top - 0.3, 1, top + 0.13 + 0.05 * g), fill((245, 240, 220)))
        cv.drawRect(skia.Rect.MakeLTRB(-1, my + 0.38 * g, 1, my + 0.8), fill((235, 230, 205)))
        n = 14
        for i in range(n + 1):
            x = -w + 2 * w * i / n
            cv.drawPath(path([(x, top - 0.3), (x, top + 0.2)]), stroke(INK, 0.025))
            cv.drawPath(path([(x, my + 0.3 * g), (x, my + 0.8)]), stroke(INK, 0.025))
        cv.restore()
        cv.drawPath(p, stroke(INK, 0.06))
        for sx in (-1, 1):   # cheek creases
            cv.drawPath(path([(sx * (w + 0.02), top - 0.2 * g), (sx * (w + 0.12), top + 0.05)]), stroke(INK, 0.04))
    elif m == "frown":
        p = skia.Path(); p.moveTo(-0.15, my + 0.06); p.quadTo(0, my - 0.08, 0.15, my + 0.06)
        cv.drawPath(p, stroke(INK, 0.06))
    if pose.sweat > 0:
        sx, sy = 0.62, hy - 0.45 + pose.sweat * 0.5
        p = skia.Path(); p.moveTo(sx, sy - 0.18); p.quadTo(sx + 0.12, sy, sx, sy + 0.06)
        p.quadTo(sx - 0.12, sy, sx, sy - 0.18); p.close()
        cv.drawPath(p, fill((140, 200, 255))); cv.drawPath(p, stroke(INK, 0.03))


def _hair(cv, kind, hy, pose):
    rgb = HAIR_RGB.get(kind, (60, 40, 30))
    if pose.back:
        # back of the head: hair covers the top two-thirds, spiky edge, skin + neck below
        p = skia.Path()
        p.moveTo(-1.0, hy + 0.15)
        p.cubicTo(-1.12, hy - 1.3, 1.12, hy - 1.3, 1.0, hy + 0.15)
        tips = [(0.8, hy + 0.32), (0.62, hy + 0.12), (0.42, hy + 0.36), (0.2, hy + 0.14), (0.0, hy + 0.4),
                (-0.2, hy + 0.14), (-0.42, hy + 0.36), (-0.62, hy + 0.12), (-0.8, hy + 0.32)]
        for q in tips:
            p.lineTo(*q)
        p.close()
        outlined(cv, p, rgb, 0.08)
        dark = tuple(int(c * 0.72) for c in rgb)
        for xx in (-0.55, -0.2, 0.15, 0.5):
            q = skia.Path(); q.moveTo(xx * 0.6, hy - 0.85); q.quadTo(xx * 1.05, hy - 0.3, xx * 1.1, hy + 0.15)
            cv.drawPath(q, stroke(dark, 0.05))
        cv.drawCircle(0.05, hy - 0.55, 0.06, stroke(dark, 0.04))   # crown whorl
        if kind == "bun":
            cv.drawCircle(0, hy - 1.05, 0.38, fill(rgb)); cv.drawCircle(0, hy - 1.05, 0.38, stroke(INK, 0.07))
        return
    if kind == "messy":
        p = skia.Path()
        p.moveTo(-1.0, hy - 0.05)
        spikes = [(-0.95, hy - 0.65), (-0.7, hy - 0.55), (-0.6, hy - 1.05), (-0.3, hy - 0.8), (-0.1, hy - 1.15),
                  (0.15, hy - 0.85), (0.4, hy - 1.1), (0.55, hy - 0.75), (0.85, hy - 0.9), (0.8, hy - 0.55),
                  (1.02, hy - 0.4)]
        for q in spikes:
            p.lineTo(*q)
        p.lineTo(1.0, hy - 0.05)
        p.quadTo(0.85, hy - 0.45, 0.4, hy - 0.42)
        p.quadTo(0.0, hy - 0.3, -0.3, hy - 0.5)
        p.quadTo(-0.7, hy - 0.4, -1.0, hy - 0.05)
        p.close()
        outlined(cv, p, rgb, 0.08)
    elif kind == "bun":
        cv.drawCircle(0.15, hy - 1.05, 0.42, fill(rgb)); cv.drawCircle(0.15, hy - 1.05, 0.42, stroke(INK, 0.07))
        p = skia.Path()
        p.moveTo(-1.02, hy + 0.15)
        p.cubicTo(-1.15, hy - 1.3, 1.15, hy - 1.3, 1.02, hy + 0.15)
        p.quadTo(0.85, hy - 0.5, 0.2, hy - 0.55)
        p.quadTo(-0.6, hy - 0.5, -1.02, hy + 0.15)
        p.close()
        outlined(cv, p, rgb, 0.08)
        for xx in (-0.95, 0.95):
            cv.drawCircle(xx, hy + 0.05, 0.16, fill(rgb)); cv.drawCircle(xx, hy + 0.05, 0.16, stroke(INK, 0.05))
    elif kind == "slick":
        p = skia.Path()
        p.moveTo(-0.98, hy - 0.2); p.cubicTo(-0.9, hy - 1.2, 0.9, hy - 1.2, 0.98, hy - 0.2)
        p.quadTo(0.3, hy - 0.75, -0.98, hy - 0.2); p.close()
        outlined(cv, p, rgb, 0.07)


def _hat(cv, kind, hy, pose):
    top = hy - 0.62
    d = pose.hat_droop
    if kind == "souwester":
        brim = skia.Path()
        brim.moveTo(-1.35, top + 0.35 + d * 0.3)
        brim.quadTo(-1.2, top + 0.05, 0, top + 0.02)
        brim.quadTo(1.2, top + 0.05, 1.45, top + 0.5 + d * 0.35)
        brim.quadTo(0.9, top + 0.3, 0, top + 0.28)
        brim.quadTo(-0.9, top + 0.3, -1.35, top + 0.35 + d * 0.3)
        brim.close()
        crown = skia.Path()
        crown.moveTo(-0.85, top + 0.1)
        crown.cubicTo(-0.85, top - 0.75, 0.85, top - 0.75, 0.85, top + 0.1)
        crown.close()
        outlined(cv, crown, (242, 194, 48), 0.085)
        outlined(cv, brim, (236, 182, 30), 0.085)
        cv.drawPath(path([(-0.75, top - 0.12), (0.75, top - 0.12)]), stroke((200, 150, 20), 0.04))
        if pose.wet:
            for i in range(3):
                yy = top + 0.5 + ((i * 0.4 + pose.wet * 3) % 1.2)
                cv.drawCircle(1.4, yy, 0.06, fill((140, 200, 255), 220))
    elif kind == "bowler":
        crown = skia.Path()
        crown.moveTo(-0.72, top + 0.12)
        crown.cubicTo(-0.75, top - 0.75, 0.75, top - 0.75, 0.72, top + 0.12)
        crown.close()
        outlined(cv, crown, (32, 30, 34), 0.07)
        brim = skia.Rect.MakeLTRB(-1.0, top + 0.02, 1.0, top + 0.24)
        cv.drawRoundRect(brim, 0.1, 0.1, fill((32, 30, 34)))
        cv.drawRoundRect(brim, 0.1, 0.1, stroke(INK, 0.06))
        cv.drawPath(path([(-0.7, top - 0.02), (0.7, top - 0.02)]), stroke((120, 110, 100), 0.06))
    elif kind == "beanie":
        crown = skia.Path()
        crown.moveTo(-0.95, top + 0.35)
        crown.cubicTo(-0.95, top - 0.75, 0.95, top - 0.75, 0.95, top + 0.35)
        crown.close()
        outlined(cv, crown, (205, 40, 45), 0.085)
        for xx in (-0.6, -0.3, 0, 0.3, 0.6):
            cv.drawPath(path([(xx, top - 0.35 + abs(xx) * 0.2), (xx * 1.05, top + 0.1)]),
                        stroke((160, 25, 30), 0.04))
        band = skia.Rect.MakeLTRB(-1.0, top + 0.08, 1.0, top + 0.42)
        cv.drawRoundRect(band, 0.12, 0.12, fill((180, 30, 36)))
        cv.drawRoundRect(band, 0.12, 0.12, stroke(INK, 0.07))
    elif kind == "captain":
        crown = skia.Path()
        crown.moveTo(-0.85, top + 0.15)
        crown.lineTo(-1.0, top - 0.3)
        crown.quadTo(0, top - 0.55, 1.0, top - 0.3)
        crown.lineTo(0.85, top + 0.15)
        crown.close()
        outlined(cv, crown, (245, 245, 245), 0.07)
        band = skia.Rect.MakeLTRB(-0.86, top - 0.02, 0.86, top + 0.18)
        cv.drawRect(band, fill((25, 25, 35)))
        vis = skia.Path(); vis.moveTo(-0.85, top + 0.15); vis.quadTo(0, top + 0.5, 0.85, top + 0.15); vis.close()
        outlined(cv, vis, (20, 20, 28), 0.05)
        cv.drawCircle(0, top - 0.2, 0.12, fill((214, 170, 60)))
        cv.drawCircle(0, top - 0.2, 0.12, stroke(INK, 0.03))


# ----------------------------------------------------------------------------
# Props
# ----------------------------------------------------------------------------
def fog_machine(cv, x, y, s, on=0.0, t=0.0):
    """Battered black stage fog machine, feet at (x,y), s = width px."""
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    soft_shadow(cv, 0, 0, 0.6, 0.1, 120)
    body = skia.Rect.MakeLTRB(-0.5, -0.55, 0.5, -0.05)
    cv.drawRoundRect(body, 0.06, 0.06, lin((0, -0.55), (0, -0.05), [(70, 70, 76), (28, 28, 32)]))
    cv.drawRoundRect(body, 0.06, 0.06, stroke(INK, 0.025))
    # dents & rivets
    for xx in (-0.42, 0.42):
        for yy in (-0.48, -0.12):
            cv.drawCircle(xx, yy, 0.018, fill((150, 150, 150)))
    cv.drawPath(path([(-0.2, -0.4), (-0.05, -0.35)]), stroke((100, 100, 106), 0.015))
    # dial
    cv.drawCircle(-0.22, -0.3, 0.09, fill((235, 225, 200)))
    cv.drawCircle(-0.22, -0.3, 0.09, stroke(INK, 0.02))
    ang = -2.2 + on * 3.0
    cv.drawPath(path([(-0.22, -0.3), (-0.22 + math.cos(ang) * 0.07, -0.3 + math.sin(ang) * 0.07)]),
                stroke((200, 30, 30), 0.015))
    # switch
    cv.drawRoundRect(skia.Rect.MakeLTRB(0.05, -0.38, 0.2, -0.22), 0.02, 0.02, fill((30, 30, 30)))
    sw = -0.36 if on < 0.5 else -0.26
    cv.drawRoundRect(skia.Rect.MakeLTRB(0.09, sw, 0.16, sw + 0.08), 0.02, 0.02, fill((210, 40, 40)))
    # lamp
    cv.drawCircle(0.33, -0.3, 0.04, fill((80, 255, 120) if on > 0.5 else (40, 70, 50)))
    if on > 0.5:
        glow(cv, 0.33, -0.3, 0.15, (80, 255, 120), 140)
    # nozzle
    cv.drawRoundRect(skia.Rect.MakeLTRB(0.5, -0.4, 0.68, -0.26), 0.03, 0.03, fill((50, 50, 55)))
    cv.drawRoundRect(skia.Rect.MakeLTRB(0.5, -0.4, 0.68, -0.26), 0.03, 0.03, stroke(INK, 0.02))
    # handle
    cv.drawPath(path([(-0.3, -0.55), (-0.3, -0.68), (0.3, -0.68), (0.3, -0.55)]), stroke((40, 40, 44), 0.04))
    cv.restore()


def fog_jet(cv, x, y, s, amount, t, seed=7, dirx=1.0):
    """Fog billowing out of a nozzle at (x,y)."""
    rnd = random.Random(seed)
    n = int(40 * amount)
    for i in range(n):
        age = ((t * 0.9 + rnd.random()) % 1.0) * amount
        dist = age * s * 3.2
        spread = age * s * 0.9
        px = x + dirx * dist + rnd.uniform(-1, 1) * spread
        py = y - age * s * 0.6 + rnd.uniform(-1, 1) * spread * 0.6
        puff(cv, px, py, s * (0.12 + age * 1.1), 150 * (1 - age * 0.6))


def lantern(cv, x, y, s, lit=1.0):
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    if lit:
        glow(cv, 0, -0.5, 1.6, (255, 190, 90), 120 * lit)
    cv.drawPath(path([(-0.15, -1.15), (0, -1.35), (0.15, -1.15)]), stroke(INK, 0.06))
    cv.drawRoundRect(skia.Rect.MakeLTRB(-0.35, -1.15, 0.35, -1.0), 0.05, 0.05, fill((170, 120, 50)))
    cv.drawRoundRect(skia.Rect.MakeLTRB(-0.3, -1.0, 0.3, -0.15), 0.1, 0.1, fill((255, 220, 140) if lit else (120, 110, 90)))
    for xx in (-0.3, 0, 0.3):
        cv.drawPath(path([(xx, -1.0), (xx, -0.15)]), stroke((150, 100, 40), 0.06))
    cv.drawRoundRect(skia.Rect.MakeLTRB(-0.38, -0.15, 0.38, 0), 0.05, 0.05, fill((170, 120, 50)))
    cv.drawRoundRect(skia.Rect.MakeLTRB(-0.3, -1.0, 0.3, -0.15), 0.1, 0.1, stroke(INK, 0.05))
    cv.restore()


def lighthouse(cv, x, y, h, lamp=1.0, stripes=((210, 40, 40), (245, 245, 240)), new=False):
    """Striped lighthouse, base centre at (x,y), height h px. Returns lamp position."""
    w0, w1 = h * 0.2, h * 0.13
    top = y - h
    body = path([(x - w0 / 2, y), (x - w1 / 2, top + h * 0.12), (x + w1 / 2, top + h * 0.12), (x + w0 / 2, y)], close=True)
    cv.save(); cv.clipPath(body, doAntiAlias=True)
    n = 5
    for i in range(n):
        y0 = y - (h * 0.88) * i / n
        y1 = y - (h * 0.88) * (i + 1) / n
        cv.drawRect(skia.Rect.MakeLTRB(x - w0, y1, x + w0, y0), fill(stripes[i % 2]))
    cv.drawRect(skia.Rect.MakeLTRB(x - w0, top, x + w0, y), lin((x - w0 / 2, 0), (x + w0 / 2, 0),
                [((0, 0, 0), 0), ((0, 0, 0), 0), ((0, 0, 0), 80)], [0, 0.45, 1]))
    if new:
        cv.drawRect(skia.Rect.MakeLTRB(x - w0 / 2 + w0 * 0.12, top, x - w0 / 2 + w0 * 0.2, y), fill((255, 255, 255), 90))
    cv.restore()
    cv.drawPath(body, stroke(INK, max(2, h * 0.008)))
    # gallery + lamp room
    gy = top + h * 0.12
    cv.drawRect(skia.Rect.MakeLTRB(x - w1 * 0.75, gy - h * 0.015, x + w1 * 0.75, gy + h * 0.01), fill((40, 40, 40)))
    lr = skia.Rect.MakeLTRB(x - w1 * 0.38, top + h * 0.035, x + w1 * 0.38, gy - h * 0.015)
    cv.drawRect(lr, fill((255, 236, 170) if lamp > 0.3 else (90, 110, 120)))
    cv.drawRect(lr, stroke(INK, max(1.5, h * 0.006)))
    roof = path([(x - w1 * 0.5, top + h * 0.035), (x, top - h * 0.02), (x + w1 * 0.5, top + h * 0.035)], close=True)
    outlined(cv, roof, (30, 30, 34) if not new else (40, 90, 170), max(1.5, h * 0.006))
    lp = (x, (top + h * 0.035 + gy) / 2)
    if lamp > 0.3:
        glow(cv, lp[0], lp[1], h * 0.12, (255, 230, 150), 200 * lamp)
    return lp


def beam(cv, origin, angle, length, width, a=120, rgb=(255, 236, 170)):
    """Sweeping lighthouse beam; angle in radians, cos(angle) controls apparent width."""
    ox, oy = origin
    fac = abs(math.cos(angle))
    side = 1 if math.cos(angle) >= 0 else -1
    reach = length * (0.35 + 0.65 * fac)
    wid = width * (0.25 + 0.75 * (1 - fac * 0.5))
    ex = ox + side * reach
    tip_y = oy + math.sin(angle) * width * 0.2
    p = path([(ox, oy - 4), (ex, tip_y - wid), (ex, tip_y + wid), (ox, oy + 4)], close=True)
    paint = lin((ox, oy), (ex, tip_y), [(rgb, a), (rgb, a * 0.5), (rgb, 0)], [0, 0.5, 1])
    paint.setBlendMode(skia.BlendMode.kPlus)
    cv.drawPath(p, paint)


def rowboat(cv, x, y, s, rock=0.0):
    cv.save(); cv.translate(x, y); cv.rotate(rock); cv.scale(s, s)
    hull = skia.Path()
    hull.moveTo(-1.0, -0.25); hull.lineTo(1.0, -0.25)
    hull.quadTo(0.9, 0.2, 0.55, 0.25); hull.lineTo(-0.55, 0.25); hull.quadTo(-0.95, 0.2, -1.0, -0.25)
    hull.close()
    outlined(cv, hull, (150, 95, 55), 0.03)
    for yy in (-0.1, 0.05):
        cv.drawPath(path([(-0.95, yy), (0.92, yy)]), stroke((110, 65, 35), 0.02))
    cv.drawRect(skia.Rect.MakeLTRB(-1.02, -0.3, 1.02, -0.24), fill((120, 75, 40)))
    cv.restore()


def cash_stack(cv, x, y, s, n):
    for i in range(n):
        r = skia.Rect.MakeXYWH(x - s / 2 + (i % 3 - 1) * 2, y - i * s * 0.06 - s * 0.06, s, s * 0.06)
        cv.drawRect(r, fill((110, 170, 100)))
        cv.drawRect(r, stroke((50, 90, 50), 1))


def bill(cv, x, y, s, rot=0.0):
    cv.save(); cv.translate(x, y); cv.rotate(rot)
    r = skia.Rect.MakeXYWH(-s / 2, -s * 0.22, s, s * 0.44)
    cv.drawRect(r, fill((130, 190, 115)))
    cv.drawRect(r, stroke((50, 90, 50), max(1, s * 0.03)))
    cv.drawCircle(0, 0, s * 0.13, stroke((60, 110, 60), max(1, s * 0.03)))
    cv.restore()


# ----------------------------------------------------------------------------
# Text (phone UI, choice cards)
# ----------------------------------------------------------------------------
_TF = {}


def font(size, weight="bold"):
    key = (weight, size)
    if key not in _TF:
        fam = {"bold": "Inter Display Bold", "semi": "Inter SemiBold", "reg": "Inter", "black": "Inter Display Black"}[weight]
        tf = skia.Typeface(fam) or skia.Typeface("Inter")
        _TF[key] = skia.Font(tf, size)
    return _TF[key]


def wrap(txt, f, width):
    lines = []
    for para in txt.split("\n"):
        cur = ""
        for w in para.split(" "):
            t = (cur + " " + w).strip()
            if f.measureText(t) > width and cur:
                lines.append(cur); cur = w
            else:
                cur = t
        lines.append(cur)
    return lines


def text(cv, s, x, y, size, rgb=(255, 255, 255), a=255, weight="bold", align="left"):
    f = font(size, weight)
    w = f.measureText(s)
    if align == "center":
        x -= w / 2
    elif align == "right":
        x -= w
    cv.drawString(s, x, y, f, fill(rgb, a))
    return w
