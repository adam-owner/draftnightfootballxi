"""
Midtown avenue built from Kenney's stylized kits (assets3d/kenney), lit by a real overcast HDRI,
with toon outlines (Freestyle), glow on emissive lights and camera depth of field.

python set_street_kenney.py -- OUT_DIR FRAMES [W H SAMPLES] [--still N] [--frozen] [--probe]
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
W, H, SAMPLES = (int(a[2]), int(a[3]), int(a[4])) if len(a) > 4 and a[2].isdigit() else (540, 960, 32)
STILL = int(a[a.index("--still") + 1]) if "--still" in a else None
FROZEN = "--frozen" in a
PROBE = "--probe" in a
FPS = int(a[a.index("--fps") + 1]) if "--fps" in a else 30
STOP_AT = float(a[a.index("--stop_at") + 1]) if "--stop_at" in a else None
CAMV = a[a.index("--cam") + 1] if "--cam" in a else "push"
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets3d")
KC, KR = os.path.join(ROOT, "kenney", "city"), os.path.join(ROOT, "kenney", "racing")
os.makedirs(OUT, exist_ok=True)
rnd = random.Random(11)
S = 10.0                      # Kenney tile (1 unit) -> 10 m

sc = B.reset()
_cache = {}


def kenney(path, loc, rot_z=0.0, scale=S, name=None):
    """Instance a Kenney glb (imported once, then linked-duplicated)."""
    if path not in _cache:
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=path)
        new = [o for o in bpy.data.objects if o not in before]
        root = bpy.data.objects.new("SRC_" + os.path.basename(path), None)
        sc.collection.objects.link(root)
        for o in new:
            if o.parent is None:
                o.parent = root
        root.hide_render = True
        for o in new:
            o.hide_render = True
        _cache[path] = new
    inst = bpy.data.objects.new(name or os.path.basename(path), None)
    sc.collection.objects.link(inst)
    for o in _cache[path]:
        if o.type != "MESH":
            continue
        c = bpy.data.objects.new(o.name + "_i", o.data)
        c.matrix_world = o.matrix_world.copy()
        sc.collection.objects.link(c)
        c.parent = inst
    inst.location = loc
    inst.rotation_euler = (0, 0, math.radians(rot_z))
    inst.scale = (scale, scale, scale)
    return inst


# ---------------------------------------------------------------- the avenue (runs along +Y)
# cross-section: road (Kenney tiles, squeezed to 7.5 m) | kerb | 5 m sidewalk | buildings
ROAD_HALF, WALK_W = 3.75, 5.0
BX = ROAD_HALF + WALK_W + S / 2            # building tile centre
CONC = B.mat("sidewalk_concrete", (168, 168, 172), 0.85)
KERB = B.mat("kerb", (128, 130, 136), 0.8)
SEAM = B.mat("seam", (140, 140, 146), 0.9)
LEN_TILES = 22
for k in range(-1, LEN_TILES):
    piece = "road-intersection.glb" if k == 2 else "road-straight-lightposts.glb"
    r = kenney(os.path.join(KC, piece), (0, k * S, 0), rot_z=90 if k != 2 else 0)
    r.scale = (S * 0.75, S, S) if k != 2 else (S, S * 0.75, S)
    for side in (-1, 1):
        if k == 2:
            continue
        b = rnd.choice(["building-small-a.glb", "building-small-b.glb", "building-small-c.glb",
                        "building-small-d.glb", "building-small-b.glb", "building-small-c.glb"])
        kenney(os.path.join(KC, b), (side * BX, k * S, 0.15), rot_z=-90 * side, scale=S * 0.98)
for side in (-1, 1):
    xc = side * (ROAD_HALF + WALK_W / 2)
    B.box("walk", (xc, LEN_TILES * S / 2 - 5, 0.075), (WALK_W, LEN_TILES * S + 10, 0.15), CONC)
    B.box("kerb", (side * (ROAD_HALF + 0.12), LEN_TILES * S / 2 - 5, 0.09), (0.24, LEN_TILES * S + 10, 0.18), KERB)
    for j in range(-5, int(LEN_TILES * S), 2):                       # paving seams every 2 m
        B.box("seam", (xc, j, 0.152), (WALK_W, 0.05, 0.004), SEAM)
    for j in range(4, int(LEN_TILES * S), 13):                       # street trees in planters
        kenney(os.path.join(KC, "grass-trees.glb"), (side * (ROAD_HALF + 1.0), j, 0.15), scale=1.6)

# continuous concrete ground under the tiles so no gaps ever show through
GROUND = B.mat("ground", (150, 152, 158), 0.9)
B.box("ground", (0, LEN_TILES * S / 2, -0.06), (S * 10, LEN_TILES * S + 60, 0.1), GROUND)

# ---------------------------------------------------------------- skyline towers behind (Kenney palette)
PAL = [(124, 168, 128), (140, 122, 196), (226, 152, 110), (122, 132, 150), (210, 190, 150), (110, 150, 190)]
WIN = B.mat("tower_win", (70, 90, 120), 0.15)
TRIM = B.mat("tower_trim", (190, 196, 206), 0.6)
towers = [B.mat("tower%d" % i, c, 0.65) for i, c in enumerate(PAL)]
for side in (-1, 1):
    for k in range(0, LEN_TILES):
        if rnd.random() < 0.75:
            h = rnd.uniform(28, 85)
            x = side * (BX + S + rnd.uniform(0, 4))
            y = k * S + rnd.uniform(-2, 2)
            m = rnd.choice(towers)
            t = B.box("tower", (x, y, h / 2), (8.5, 8.5, h), m, bevel=0.25)
            B.box("cap", (x, y, h + 0.4), (9.2, 9.2, 0.8), TRIM, bevel=0.1)
            # rows of chunky windows on the faces that look onto the avenue
            for z in range(6, int(h) - 2, 4):
                B.box("winrow", (x - side * 4.3, y, z), (0.25, 7.0, 1.6), WIN)
for i in range(16):   # far towers closing the vista
    h = rnd.uniform(70, 170)
    B.box("far", (-55 + i * 7.5, LEN_TILES * S + 35 + rnd.uniform(0, 25), h / 2), (6.5, 6.5, h), rnd.choice(towers), bevel=0.3)

# ---------------------------------------------------------------- traffic: Kenney trucks, animated
cars = []
for k in range(6):
    lane = k % 2                       # 0 toward camera, 1 away
    col = rnd.choice(["vehicle-truck-yellow.glb", "vehicle-truck-yellow.glb", "vehicle-truck-red.glb", "vehicle-truck-green.glb"])
    c = kenney(os.path.join(KR, col), (0, 0, 0), rot_z=180 if lane == 0 else 0, scale=2.6)
    x = -1.6 if lane == 0 else 1.6
    v = (10.0 if lane == 0 else 8.0) * (0 if FROZEN else 1)
    y0 = (48 + k * 20 if lane == 0 else 34 + k * 20) + rnd.uniform(-3, 3)   # oncoming cars never reach the lens
    B.move(c, FPS, (x, y0, 0.02), (0, -v if lane == 0 else v, 0), FRAMES, STOP_AT)


# ---------------------------------------------------------------- pedestrian anchors on the sidewalks
for i in range(16):
    side = -1 if i % 2 else 1
    toward = (i // 2) % 2 == 0
    x = side * rnd.uniform(ROAD_HALF + 1.6, ROAD_HALF + WALK_W - 0.6)
    y0 = rnd.uniform(2.5, 14) if (i < 6 and side < 0) else rnd.uniform(6, 60)   # a few close to camera
    v = (1.3 + 0.3 * rnd.random()) * (0 if FROZEN else 1)
    e = B.anchor("ped%d_%s" % (i, "to" if toward else "away"), (x, y0, 0.15))
    B.move(e, FPS, (x, y0, 0.15), (0, -v if toward else v, 0), FRAMES, STOP_AT)

# ---------------------------------------------------------------- light: real overcast sky + soft sun
w = bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True
env = w.node_tree.nodes.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load(os.path.join(ROOT, "sky_overcast.hdr"))
w.node_tree.links.new(env.outputs[0], w.node_tree.nodes["Background"].inputs[0])
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.15
B.sun((52, 8, 150), 1.6, rgb=(255, 240, 222), angle=10)

# ---------------------------------------------------------------- camera: eye level, slow push, shallow DOF
if CAMV == "push":
    keys = [(1, (-6.6, -7, 2.0), (86, 0, -5)), (FRAMES, (-6.5, -2.0, 2.0), (86.5, 0, -4.5))]
elif CAMV == "aerial":  # the skyline from high above the avenue (title card / silent city)
    keys = [(1, (-14, -40, 75), (68, 0, -12)), (FRAMES, (-14, -40, 75), (68, 0, -12))]
else:  # close: the frozen crowd, nearer and lower
    keys = [(1, (-6.4, -2, 1.9), (86, 0, -8)), (FRAMES, (-6.3, -1.2, 1.9), (86, 0, -8))]
if PROBE:
    keys = [(1, (0, 40, 160), (0, 0, 0)), (FRAMES, (0, 40, 160), (0, 0, 0))]
cam = B.camera(keys, lens=28, dof_target=14.0, fstop=5.6)

# ---------------------------------------------------------------- toon outlines + glow (reference look)
sc.render.use_freestyle = True
sc.render.line_thickness_mode = "ABSOLUTE"
sc.render.line_thickness = 1.1
fs = sc.view_layers[0].freestyle_settings
ls = fs.linesets.active or fs.linesets.new("toon")
if ls.linestyle is None:
    ls.linestyle = bpy.data.linestyles.new("toon")
ls.select_by_visibility = True
ls.select_silhouette = True; ls.select_border = True; ls.select_crease = True
ls.linestyle.color = (0.06, 0.05, 0.05)
ls.linestyle.alpha = 0.85
sc.use_nodes = True
nt = sc.node_tree
rl = nt.nodes["Render Layers"]; comp = nt.nodes["Composite"]
glare = nt.nodes.new("CompositorNodeGlare"); glare.glare_type = "FOG_GLOW"; glare.quality = "MEDIUM"
glare.threshold = 0.9; glare.size = 7
nt.links.new(rl.outputs["Image"], glare.inputs["Image"]); nt.links.new(glare.outputs["Image"], comp.inputs["Image"])

B.output(sc, W, H, FRAMES, SAMPLES, OUT, fps=FPS)
sc.cycles.max_bounces = 6; sc.cycles.diffuse_bounces = 3
B.export_anchors(sc, os.path.join(OUT, "anchors.json"))
if STILL is not None:
    sc.frame_set(STILL)
    sc.render.filepath = os.path.join(OUT, "still_%03d.png" % STILL)
    bpy.ops.render.render(write_still=True)
else:
    bpy.ops.render.render(animation=True)

# bpy can segfault during interpreter teardown after a successful render; files are saved, so exit now
os._exit(0)
