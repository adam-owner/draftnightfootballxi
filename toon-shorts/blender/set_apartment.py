"""
Alex's 32nd-floor apartment: stylized room (bevelled furniture), a big window over the 3D skyline.

python set_apartment.py -- OUT_DIR [W H SAMPLES] --cam wide|close|window --lights on|off
Anchors: alex, sister (where the 2D characters stand / sit for that camera).
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bl_common as B   # noqa: E402

a = B.args()
OUT = a[0]
W, H, SAMPLES = (int(a[1]), int(a[2]), int(a[3])) if len(a) > 3 and a[1].isdigit() else (540, 960, 40)
CAM = a[a.index("--cam") + 1] if "--cam" in a else "wide"
LIGHTS = (a[a.index("--lights") + 1] if "--lights" in a else "on") == "on"
os.makedirs(OUT, exist_ok=True)
rnd = random.Random(5)
sc = B.reset()
Z = 100.0                                    # floor height (32nd floor)

# ---------------------------------------------------------------- materials (Kenney-like palette)
FLOOR = B.mat("floor_wood", (156, 112, 78), 0.6)
WALL = B.mat("wall", (226, 214, 196), 0.85)
WALL2 = B.mat("wall_accent", (120, 150, 170), 0.85)
CEIL = B.mat("ceiling", (236, 232, 226), 0.9)
FRAMEM = B.mat("window_frame", (60, 64, 72), 0.5)
COUCH = B.mat("couch", (70, 98, 150), 0.8)
CUSH = B.mat("cushion", (232, 170, 70), 0.8)
RUG = B.mat("rug", (186, 82, 70), 0.95)
WOOD = B.mat("wood_dark", (110, 72, 48), 0.6)
METAL = B.mat("lamp_metal", (40, 42, 46), 0.4, metal=0.5)
SHADE = B.mat("lamp_shade", (250, 236, 200), 0.6, emit=(255, 214, 150), emit_strength=4.0 if LIGHTS else 0.0)
SCREENM = B.mat("tv_screen", (16, 18, 22), 0.2)
POT = B.mat("pot", (200, 110, 80), 0.7)
BOOKS = [B.mat("book%d" % i, c, 0.7) for i, c in enumerate(((190, 60, 60), (60, 120, 180), (230, 190, 80), (90, 160, 110), (140, 100, 170)))]
WIN = B.mat("tower_win", (70, 90, 120), 0.15)
TRIM = B.mat("tower_trim", (190, 196, 206), 0.6)
TOWERS = [B.mat("tw%d" % i, c, 0.65) for i, c in enumerate(B.PAL)]
GROUND = B.mat("city_ground", (120, 122, 128), 0.9)

# ---------------------------------------------------------------- room shell: x -5..5, y 0..8 (window wall at y=8), 3 m high
B.box("floor", (0, 4, Z - 0.05), (10, 8, 0.1), FLOOR)
B.box("ceiling", (0, 4, Z + 3.05), (10, 8, 0.1), CEIL)
B.box("wall_l", (-5.05, 4, Z + 1.5), (0.1, 8, 3), WALL2)
B.box("wall_r", (5.05, 4, Z + 1.5), (0.1, 8, 3), WALL)
B.box("wall_b", (0, -0.05, Z + 1.5), (10, 0.1, 3), WALL)
# window wall with a big opening x -4.2..4.2, z +0.4..+2.8
B.box("win_sill", (0, 8.05, Z + 0.2), (10, 0.1, 0.4), WALL)
B.box("win_head", (0, 8.05, Z + 2.9), (10, 0.1, 0.2), WALL)
B.box("win_l", (-4.6, 8.05, Z + 1.5), (0.8, 0.1, 3), WALL)
B.box("win_r", (4.6, 8.05, Z + 1.5), (0.8, 0.1, 3), WALL)
for x in (-4.2, -1.4, 1.4, 4.2):
    B.box("mullion", (x, 8.05, Z + 1.6), (0.12, 0.16, 2.4), FRAMEM)
B.box("transom", (0, 8.05, Z + 0.42), (8.4, 0.16, 0.08), FRAMEM)
B.box("transom2", (0, 8.05, Z + 2.78), (8.4, 0.16, 0.08), FRAMEM)

# ---------------------------------------------------------------- furniture (bevel = soft stylized edges)
B.box("rug", (-0.6, 4.2, Z + 0.01), (4.2, 3.0, 0.02), RUG, bevel=0.01)
# couch against the left wall, facing +x
cx, cy = -3.9, 4.0
B.box("couch_base", (cx, cy, Z + 0.25), (1.0, 2.6, 0.5), COUCH, bevel=0.08)
B.box("couch_back", (cx - 0.38, cy, Z + 0.7), (0.3, 2.6, 0.9), COUCH, bevel=0.1)
for dy in (-1.35, 1.35):
    B.box("couch_arm", (cx, cy + dy, Z + 0.45), (1.0, 0.25, 0.6), COUCH, bevel=0.08)
for dy in (-0.6, 0.6):
    B.box("cushion", (cx - 0.15, cy + dy, Z + 0.75), (0.25, 0.7, 0.45), CUSH, bevel=0.1)
# coffee table
B.box("table_top", (-1.9, 4.0, Z + 0.42), (1.0, 1.6, 0.08), WOOD, bevel=0.02)
for dx in (-0.4, 0.4):
    for dy in (-0.7, 0.7):
        B.box("table_leg", (-1.9 + dx, 4.0 + dy, Z + 0.2), (0.07, 0.07, 0.4), WOOD)
B.box("mug", (-1.8, 3.7, Z + 0.52), (0.12, 0.12, 0.14), CUSH, bevel=0.03)
# floor lamp
lx, ly = 3.9, 6.8
B.cyl("lamp_pole", (lx, ly, Z + 0.8), 0.03, 1.6, METAL)
B.cyl("lamp_base", (lx, ly, Z + 0.03), 0.22, 0.06, METAL)
B.cyl("lamp_shade", (lx, ly, Z + 1.65), 0.3, 0.4, SHADE, verts=20)
# bookshelf on the back wall
B.box("shelf", (2.6, 0.35, Z + 1.0), (2.2, 0.5, 2.0), WOOD, bevel=0.03)
for r in range(4):
    zz = Z + 0.25 + r * 0.48
    x = 1.65
    while x < 3.5:
        bw = rnd.uniform(0.06, 0.14); bh = rnd.uniform(0.28, 0.4)
        B.box("book", (x, 0.55, zz + bh / 2), (bw, 0.3, bh), rnd.choice(BOOKS))
        x += bw + 0.02
# TV on a low stand against the right wall
B.box("tv_stand", (4.6, 3.6, Z + 0.25), (0.7, 1.9, 0.5), WOOD, bevel=0.03)
B.box("tv", (4.75, 3.6, Z + 1.05), (0.1, 1.6, 0.92), METAL, bevel=0.02)
B.box("tv_screen", (4.69, 3.6, Z + 1.05), (0.02, 1.5, 0.82), SCREENM)
# plant (Kenney tree in a pot)
B.cyl("pot", (-4.3, 7.3, Z + 0.25), 0.28, 0.5, POT)
B.kit(os.path.join(B.KC, "grass-trees-tall.glb"), (-4.3, 7.3, Z + 0.5), scale=1.3)

# ---------------------------------------------------------------- outside: the skyline below the window
B.box("ground", (0, 120, -0.05), (600, 400, 0.1), GROUND)
for i in range(60):
    x = rnd.uniform(-160, 160); y = rnd.uniform(30, 320)
    if abs(x) < 25 and y < 60:
        continue
    h = rnd.uniform(40, 190) if y > 60 else rnd.uniform(40, 95)
    B.tower(x, y, h, rnd.choice(TOWERS), WIN, TRIM, w=rnd.uniform(9, 16), face_y=-1)

# ---------------------------------------------------------------- light
B.hdri_world(1.2)
B.sun((58, 8, 160), 1.4, rgb=(255, 238, 220), angle=10)
B.area("LGT_window_fill", (0, 7.6, Z + 1.6), (-90, 0, 0), 260, (225, 234, 255), size=8)   # daylight bounce through the glass
if LIGHTS:
    B.point("LGT_lamp", (lx, ly, Z + 1.6), 90, (255, 200, 140), radius=0.25)
    B.area("LGT_ceiling", (0, 4, Z + 2.95), (180, 0, 0), 220, (255, 224, 190), size=3)

# ---------------------------------------------------------------- characters' marks + cameras
if CAM == "wide":       # from the back-right corner toward the window: Alex standing, sister on the couch
    B.anchor("alex", (-0.6, 4.6, Z)); B.anchor("sister", (-3.55, 4.4, Z + 0.42))
    keys = [(1, (3.9, 0.45, Z + 1.55), (85, 0, 40))]
elif CAM == "close":    # closer on the couch: sister crying, Alex beside her
    B.anchor("alex", (-2.5, 3.2, Z)); B.anchor("sister", (-3.55, 4.1, Z + 0.42))
    keys = [(1, (0.6, 1.6, Z + 1.25), (84, 0, 55))]
else:                   # window: both from behind, looking out at the skyline
    B.anchor("alex", (-0.4, 6.9, Z)); B.anchor("sister", (0.6, 7.0, Z))
    keys = [(1, (0.0, 2.6, Z + 1.35), (90, 0, 0))]
keys = keys + [(2, keys[0][1], keys[0][2])]
B.camera(keys, lens=20, dof_target=6.0, fstop=5.6)
B.toon_look(sc, line=1.0)
B.output(sc, W, H, 2, SAMPLES, OUT)
sc.cycles.max_bounces = 8; sc.cycles.diffuse_bounces = 4
B.export_anchors(sc, os.path.join(OUT, "anchors.json"))
sc.frame_set(1)
sc.render.filepath = os.path.join(OUT, "still_001.png")
import bpy  # noqa: E402
bpy.ops.render.render(write_still=True)
