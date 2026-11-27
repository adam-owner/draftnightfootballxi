"""
Midtown avenue, grey Monday morning. 3D cabs drive both lanes; 2D pedestrians get moving anchors.

blender -b -P set_street.py -- OUT_DIR FRAMES [W H SAMPLES] [--frozen] [--cam push|low|high] [--still N]
"""
import math
import os
import random
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bl_common as B   # noqa: E402

a = B.args()
OUT, FRAMES = a[0], int(a[1])
W, H, SAMPLES = (int(a[2]), int(a[3]), int(a[4])) if len(a) > 4 and a[2].isdigit() else (540, 960, 24)
FROZEN = "--frozen" in a
CAMMODE = a[a.index("--cam") + 1] if "--cam" in a else "push"
STILL = int(a[a.index("--still") + 1]) if "--still" in a else None
os.makedirs(OUT, exist_ok=True)
rnd = random.Random(7)

sc = B.reset()


def facade_mat(name, wall, glass, lit=0.25, win=(1.6, 2.2), wsize=(1.0, 1.4)):
    """Wall with a grid of windows (brick texture used as a window grid), some lit warm."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; n = nt.nodes; L = nt.links
    bsdf = n["Principled BSDF"]
    tc = n.new("ShaderNodeTexCoord"); sep = n.new("ShaderNodeSeparateXYZ"); comb = n.new("ShaderNodeCombineXYZ")
    add = n.new("ShaderNodeMath"); add.operation = "ADD"
    L.new(tc.outputs["Object"], sep.inputs[0])
    L.new(sep.outputs["X"], add.inputs[0]); L.new(sep.outputs["Y"], add.inputs[1])
    L.new(add.outputs[0], comb.inputs["X"]); L.new(sep.outputs["Z"], comb.inputs["Y"])
    br = n.new("ShaderNodeTexBrick")
    br.offset = 0.0; br.squash = 1.0
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Mortar Size"].default_value = 0.32
    br.inputs["Mortar Smooth"].default_value = 0.02
    br.inputs["Brick Width"].default_value = win[0]
    br.inputs["Row Height"].default_value = win[1]
    br.inputs["Color1"].default_value = (*B.srgb(glass), 1)
    br.inputs["Color2"].default_value = (*B.srgb(tuple(min(255, c + 20) for c in glass)), 1)
    br.inputs["Mortar"].default_value = (*B.srgb(wall), 1)
    L.new(comb.outputs[0], br.inputs["Vector"])
    L.new(br.outputs["Color"], bsdf.inputs["Base Color"])
    # roughness: glass shinier than wall
    inv = n.new("ShaderNodeMath"); inv.operation = "MULTIPLY"; inv.inputs[1].default_value = 0.6
    L.new(br.outputs["Fac"], inv.inputs[0])
    rr = n.new("ShaderNodeMath"); rr.operation = "SUBTRACT"; rr.inputs[0].default_value = 0.85
    L.new(inv.outputs[0], rr.inputs[1]); L.new(rr.outputs[0], bsdf.inputs["Roughness"])
    # random lit windows: cell noise per window, thresholded, masked by "is window" (1 - fac)
    vor = n.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 0.55
    L.new(comb.outputs[0], vor.inputs["Vector"])
    sep2 = n.new("ShaderNodeSeparateColor"); L.new(vor.outputs["Color"], sep2.inputs[0])
    thr = n.new("ShaderNodeMath"); thr.operation = "GREATER_THAN"; thr.inputs[1].default_value = 1 - lit
    L.new(sep2.outputs[0], thr.inputs[0])
    isw = n.new("ShaderNodeMath"); isw.operation = "SUBTRACT"; isw.inputs[0].default_value = 1.0
    L.new(br.outputs["Fac"], isw.inputs[1])
    mul = n.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
    L.new(thr.outputs[0], mul.inputs[0]); L.new(isw.outputs[0], mul.inputs[1])
    key = "Emission Color" if "Emission Color" in bsdf.inputs else "Emission"
    bsdf.inputs[key].default_value = (*B.srgb((255, 214, 150)), 1)
    s = n.new("ShaderNodeMath"); s.operation = "MULTIPLY"; s.inputs[1].default_value = 2.2
    L.new(mul.outputs[0], s.inputs[0]); L.new(s.outputs[0], bsdf.inputs["Emission Strength"])
    return m


# ---------------------------------------------------------------- palette (limited, desaturated bg)
ROAD = B.mat("road", (58, 60, 66), 0.85)
WALK = B.mat("sidewalk", (150, 148, 142), 0.9)
CURB = B.mat("curb", (120, 118, 114), 0.9)
LINE = B.mat("line_yellow", (236, 196, 60), 0.6)
WHITE = B.mat("line_white", (230, 230, 226), 0.6)
POLE = B.mat("pole", (40, 44, 50), 0.4, metal=0.6)
CAB = B.mat("cab_yellow", (250, 196, 30), 0.35)
GLASS = B.mat("cab_glass", (60, 80, 100), 0.08)
TIRE = B.mat("tire", (25, 25, 28), 0.9)
LAMP = B.mat("lamp", (255, 240, 210), 0.3, emit=(255, 240, 210), emit_strength=6)
TAIL = B.mat("tail", (230, 30, 30), 0.3, emit=(255, 40, 30), emit_strength=8)
SIGN_R = B.mat("sig_red", (200, 30, 30), 0.3, emit=(255, 40, 30), emit_strength=0 if not FROZEN else 10)
SIGN_G = B.mat("sig_green", (40, 200, 110), 0.3, emit=(60, 255, 140), emit_strength=10 if not FROZEN else 0)
AWN = [B.mat("awn%d" % i, c, 0.8) for i, c in enumerate(((170, 50, 44), (40, 100, 84), (52, 64, 120)))]

walls = [((150, 140, 128), (54, 66, 80)), ((120, 92, 78), (50, 60, 74)), ((176, 170, 160), (60, 74, 90)),
         ((96, 100, 110), (40, 50, 64)), ((140, 120, 96), (56, 64, 78))]
FACADES = [facade_mat("fac%d" % i, w, g, lit=0.18 + 0.08 * (i % 3)) for i, (w, g) in enumerate(walls)]
SHOP = B.mat("shopglass", (255, 220, 160), 0.2, emit=(255, 214, 150), emit_strength=2.5)

# ---------------------------------------------------------------- ground
LEN = 260
B.box("road", (0, LEN / 2, -0.05), (12, LEN, 0.1), ROAD)
for side in (-1, 1):
    B.box("walk%d" % side, (side * 9, LEN / 2, 0.08), (6, LEN, 0.16), WALK)
    B.box("curb%d" % side, (side * 6.05, LEN / 2, 0.08), (0.2, LEN, 0.18), CURB)
for k in range(0, LEN, 9):            # centre double yellow + lane dashes
    B.box("cl%d" % k, (-0.12, k + 2, 0.005), (0.12, 4.5, 0.01), LINE)
    B.box("cr%d" % k, (0.12, k + 2, 0.005), (0.12, 4.5, 0.01), LINE)
for i in range(9):                    # crosswalk near camera
    B.box("zebra%d" % i, (-5 + i * 1.25, 9, 0.006), (0.6, 3.2, 0.01), WHITE)

# ---------------------------------------------------------------- buildings
for side in (-1, 1):
    y = -10
    while y < LEN:
        w = rnd.uniform(12, 26)
        h = rnd.uniform(22, 70) if y > 30 else rnd.uniform(16, 34)
        d = 18
        m = FACADES[rnd.randrange(len(FACADES))]
        B.box("bld", (side * (12 + d / 2), y + w / 2, h / 2), (d, w - 0.6, h), m)
        # cornice + ground-floor shop band
        B.box("corn", (side * (12 - 0.3), y + w / 2, h - 0.4), (0.8, w - 0.4, 0.8), CURB)
        B.box("shop", (side * 11.95, y + w / 2, 2.0), (0.1, w - 2.5, 2.6), SHOP)
        awn = B.box("awn", (side * 11.2, y + w / 2, 3.6), (1.6, w - 2.0, 0.25), AWN[rnd.randrange(3)])
        awn.rotation_euler = (0, math.radians(-side * 14), 0)
        y += w
# far skyline at the end of the avenue
for i in range(14):
    x = -40 + i * 6.5
    h = rnd.uniform(60, 160)
    B.box("far", (x, LEN + 40 + rnd.uniform(0, 30), h / 2), (rnd.uniform(5, 9), 8, h), FACADES[i % len(FACADES)])

# ---------------------------------------------------------------- street furniture
for side in (-1, 1):
    for y in range(6, LEN, 26):
        B.cyl("pole", (side * 6.6, y, 3.5), 0.09, 7, POLE, 10)
        arm = B.box("arm", (side * 5.9, y, 7.0), (1.6, 0.12, 0.12), POLE)
        B.box("lamp", (side * 5.2, y, 6.92), (0.6, 0.3, 0.12), LAMP)
# traffic light on the near right corner
B.cyl("tl_pole", (6.8, 12, 2.6), 0.1, 5.2, POLE, 10)
tlh = B.box("tl_head", (6.8, 12, 5.6), (0.45, 0.4, 1.2), POLE)
B.box("tl_r", (6.8, 11.78, 5.95), (0.26, 0.05, 0.26), SIGN_R)
B.box("tl_g", (6.8, 11.78, 5.3), (0.26, 0.05, 0.26), SIGN_G)


# ---------------------------------------------------------------- cabs (real 3D, animated)
def make_cab(name):
    parts = [B.box(name + "_body", (0, 0, 0.7), (1.9, 4.4, 0.8), CAB, bevel=0.12),
             B.box(name + "_cabin", (0, -0.2, 1.35), (1.7, 2.3, 0.6), CAB, bevel=0.1),
             B.box(name + "_win", (0, -0.2, 1.36), (1.75, 2.0, 0.42), GLASS),
             B.box(name + "_sign", (0, -0.2, 1.78), (0.7, 0.3, 0.22), LAMP)]
    for sx in (-0.95, 0.95):
        for sy in (-1.4, 1.4):
            t = B.cyl(name + "_tire", (sx, sy, 0.38), 0.38, 0.3, TIRE, 14); t.rotation_euler = (0, math.radians(90), 0)
            parts.append(t)
    for sx in (-0.65, 0.65):
        parts.append(B.box(name + "_hl", (sx, 2.21, 0.75), (0.32, 0.04, 0.18), LAMP))
        parts.append(B.box(name + "_tl", (sx, -2.21, 0.75), (0.32, 0.04, 0.18), TAIL))
    root = bpy.data.objects.new(name, None); sc.collection.objects.link(root)
    for p in parts:
        p.parent = root
    return root


cabs = []
for k in range(7):
    lane = k % 2                      # 0: toward camera (-y), 1: away (+y)
    c = make_cab("CAB%d" % k)
    x = -3.0 if lane == 0 else 3.0
    c.rotation_euler = (0, 0, math.radians(180 if lane == 0 else 0))
    speed = (11.0 if lane == 0 else 9.0) * (0.0 if FROZEN else 1.0)
    y0 = 25 + k * 26 + rnd.uniform(-6, 6)
    for f in (1, FRAMES):
        t = (f - 1) / 30.0
        c.location = (x, y0 + (-speed * t if lane == 0 else speed * t), 0)
        c.keyframe_insert("location", frame=f)
    for fc in c.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"

# ---------------------------------------------------------------- pedestrian anchors (2D characters stand here)
for i in range(12):
    side = -1 if i % 2 else 1
    toward = (i // 2) % 2 == 0
    x = side * rnd.uniform(7.6, 10.6)
    y0 = rnd.uniform(10, 70)
    v = (1.3 + 0.3 * rnd.random()) * (0 if FROZEN else 1)
    e = B.anchor("ped%d_%s" % (i, "to" if toward else "away"), (x, y0, 0.16))
    for f in (1, FRAMES):
        t = (f - 1) / 30.0
        e.location = (x, y0 + (-v * t if toward else v * t), 0.16)
        e.keyframe_insert("location", frame=f)
    for fc in e.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"

# ---------------------------------------------------------------- light + atmosphere (overcast Monday)
B.world((150, 166, 186), strength=1.1, haze=0.004, haze_rgb=(200, 208, 218))
B.sun((48, 12, 140), 2.2, rgb=(255, 236, 214), angle=12)

# ---------------------------------------------------------------- camera
if CAMMODE == "push":
    keys = [(1, (-1.2, -2, 1.6), (88, 0, 0)), (FRAMES, (-1.0, 4.5, 1.6), (88, 0, -1.5))]
elif CAMMODE == "low":
    keys = [(1, (-4.5, 2, 0.6), (84, 0, -6)), (FRAMES, (-4.3, 3.5, 0.65), (84, 0, -3))]
else:  # high: looking down the avenue from a second-floor window
    keys = [(1, (4.0, -4, 6.5), (76, 0, 8)), (FRAMES, (3.6, -2, 6.0), (78, 0, 4))]
B.camera(keys, lens=30)

B.output(sc, W, H, FRAMES, SAMPLES, OUT)
B.export_anchors(sc, os.path.join(OUT, "anchors.json"))
if STILL is not None:
    sc.frame_set(STILL)
    sc.render.filepath = os.path.join(OUT, "still_%03d.png" % STILL)
    bpy.ops.render.render(write_still=True)
else:
    bpy.ops.render.render(animation=True)
