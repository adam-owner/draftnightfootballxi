"""
Times Square: a plaza walled in by towers covered in giant screens. Screen *content* is painted in 2D
afterwards onto each screen's projected corners (anchors ANC_scr<i>_c0..c3), so one render serves
ads / EMERGENCY BROADCAST / news / black. The render carries the light the screens cast:
--variant ads (multicolour) or alert (red).

python set_times_square.py -- OUT_DIR [W H SAMPLES] --variant ads|alert
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bl_common as B   # noqa: E402

a = B.args()
OUT = a[0]
W, H, SAMPLES = (int(a[1]), int(a[2]), int(a[3])) if len(a) > 3 and a[1].isdigit() else (540, 960, 32)
VARIANT = a[a.index("--variant") + 1] if "--variant" in a else "ads"
os.makedirs(OUT, exist_ok=True)
rnd = random.Random(21)
sc = B.reset()

# ---------------------------------------------------------------- materials
PLAZA = B.mat("plaza", (150, 148, 150), 0.8)
STEP = B.mat("red_steps", (190, 40, 46), 0.6)
WIN = B.mat("win", (60, 76, 100), 0.15)
TRIM = B.mat("trim", (190, 196, 206), 0.6)
FRAME = B.mat("screen_frame", (24, 24, 28), 0.5)
SCREEN = B.mat("screen", (14, 14, 18), 0.25)          # dark glass; content is drawn in 2D
TOWERS = [B.mat("tw%d" % i, c, 0.65) for i, c in enumerate(B.PAL)]

# ---------------------------------------------------------------- ground + red steps
B.box("plaza", (0, 30, -0.05), (90, 140, 0.1), PLAZA)
for i in range(6):
    B.box("step", (0, 44 + i * 0.9, 0.15 + i * 0.3), (16, 0.9, 0.3 + i * 0.6), STEP)
for k in range(-3, 12):   # crossing road paint
    B.box("stripe", (-30 + k * 5, 2, 0.003), (2.2, 6, 0.01), TRIM)

# ---------------------------------------------------------------- towers + screens
screens = []
# main screen straight ahead (the broadcast screen)
B.tower(0, 66, 140, TOWERS[3], WIN, TRIM, w=40, face_y=-1)
screens.append(B.screen_quad("scr0", (0, 45.8, 30), (34, 19), "y-", SCREEN))
B.box("frame0", (0, 46.0, 30), (36, 0.3, 21), FRAME)
# walls of screens left and right, close enough to fill a vertical frame, screens stacked up the faces
for side, facing in ((-1, "x+"), (1, "x-")):
    for j, y in enumerate((4, 18, 32)):
        h = rnd.uniform(90, 150)
        tw = 12
        B.tower(side * 19, y, h, rnd.choice(TOWERS), WIN, TRIM, w=tw, face_x=-side)
        x_face = side * 19 - side * (tw / 2 + 0.05)
        z = 4.0
        for k in range(3):
            sw, sh = rnd.uniform(8, 11), rnd.uniform(6, 11)
            zc = z + sh / 2
            name = "scr%d" % (len(screens))
            screens.append(B.screen_quad(name, (x_face, y, zc), (sw, sh), facing, SCREEN))
            B.box("fr_" + name, (x_face + side * 0.1, y, zc), (0.3, sw + 1.0, sh + 1.0), FRAME)
            z += sh + rnd.uniform(2.5, 5)
# far background towers
for i in range(10):
    B.tower(-60 + i * 13, 110 + rnd.uniform(0, 30), rnd.uniform(90, 200), rnd.choice(TOWERS), WIN, TRIM, w=10, face_y=-1)
# Kenney buildings at street level between the towers, lightposts on the crossing road
# (no road tiles here: their lamp posts land in front of the lens)

# ---------------------------------------------------------------- crowd anchors (people stand, looking up)
for i in range(48):   # dense near the camera, thinning out toward the big screen
    y = -4.5 + (rnd.random() ** 1.6) * 30
    x = rnd.uniform(-1, 1) * (3.5 + y * 0.35)
    B.anchor("crowd%d" % i, (x, y, 0.0))

# ---------------------------------------------------------------- light: dull overcast + the screens' light
B.hdri_world(0.55)
cols = [(255, 70, 150), (60, 200, 255), (255, 210, 60), (140, 255, 120), (190, 110, 255)]
for i, s in enumerate(screens):
    loc = s.location.copy()
    if i == 0:
        loc.y -= 6
        rot = (90, 0, 0)
    else:
        loc.x += -6 if loc.x > 0 else 6
        rot = (90, 0, 90 if loc.x > 0 else -90)
    col = (255, 40, 40) if VARIANT == "alert" else cols[i % len(cols)]
    watts = (5000 if i == 0 else 1400) * (1.4 if VARIANT == "alert" else 1.0)
    B.area("LGT_scr%d" % i, tuple(loc), rot, watts, col, size=8 if i == 0 else 5)

# ---------------------------------------------------------------- camera: in the crowd, looking up at the big screen
B.camera([(1, (0, -8, 1.7), (106, 0, 0)), (2, (0, -8, 1.7), (106, 0, 0))], lens=17, dof_target=30, fstop=11)
B.toon_look(sc, line=1.0, glow_threshold=0.85)
B.output(sc, W, H, 2, SAMPLES, OUT)
B.export_anchors(sc, os.path.join(OUT, "anchors.json"))
sc.frame_set(1)
sc.render.filepath = os.path.join(OUT, "still_001.png")
import bpy  # noqa: E402
bpy.ops.render.render(write_still=True)

# bpy can segfault during interpreter teardown after a successful render; files are saved, so exit now
os._exit(0)
