"""
Shared Blender helpers for toon-shorts 3D sets (run inside Blender: blender -b -P script.py -- args).

The look follows the reference shorts: stylized, chunky 3D environments (flat-ish colour, soft GI,
haze, warm practical lights) that 2D cut-out characters are composited into afterwards.
Characters are NOT modelled in 3D: each set exports, per frame, the screen position + scale of
named anchor empties ("ANC_<name>") so the 2D renderer can stand characters on the 3D floor.
"""
import json
import math
import sys

import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view


def args():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    return a


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.view_settings.view_transform = "AgX" if "AgX" in [i.identifier for i in
        sc.view_settings.bl_rna.properties["view_transform"].enum_items] else "Filmic"
    try:
        sc.view_settings.look = "AgX - Medium High Contrast" if sc.view_settings.view_transform == "AgX" else "Medium High Contrast"
    except TypeError:
        pass
    return sc


def mat(name, rgb, rough=0.7, emit=None, emit_strength=0.0, metal=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*srgb(rgb), 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit is not None:
        key = "Emission Color" if "Emission Color" in b.inputs else "Emission"
        b.inputs[key].default_value = (*srgb(emit), 1)
        b.inputs["Emission Strength"].default_value = emit_strength
    return m


def srgb(rgb):
    """0-255 sRGB -> linear floats."""
    out = []
    for c in rgb:
        c = c / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(out)


def box(name, loc, size, material, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        mod = o.modifiers.new("bev", "BEVEL"); mod.width = bevel; mod.segments = 2
    o.data.materials.append(material)
    return o


def cyl(name, loc, r, h, material, verts=16):
    bpy.ops.mesh.primitive_cylinder_add(location=loc, radius=r, depth=h, vertices=verts)
    o = bpy.context.object; o.name = name; o.data.materials.append(material)
    return o


def anchor(name, loc):
    e = bpy.data.objects.new("ANC_" + name, None)
    e.location = loc
    bpy.context.scene.collection.objects.link(e)
    return e


def world(rgb_top, strength=1.0, haze=0.0, haze_rgb=(200, 210, 220)):
    w = bpy.data.worlds.new("World"); bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    bg.inputs["Color"].default_value = (*srgb(rgb_top), 1)
    bg.inputs["Strength"].default_value = strength
    if haze > 0:
        vol = nt.nodes.new("ShaderNodeVolumePrincipled")
        vol.inputs["Density"].default_value = haze
        vol.inputs["Color"].default_value = (*srgb(haze_rgb), 1)
        vol.inputs["Anisotropy"].default_value = 0.35
        nt.links.new(vol.outputs[0], nt.nodes["World Output"].inputs["Volume"])


def sun(rot_deg, strength, rgb=(255, 244, 230), angle=8):
    d = bpy.data.lights.new("LGT_Sun", "SUN"); d.energy = strength; d.color = srgb(rgb); d.angle = math.radians(angle)
    o = bpy.data.objects.new("LGT_Sun", d); o.rotation_euler = [math.radians(a) for a in rot_deg]
    bpy.context.scene.collection.objects.link(o)
    return o


def point(name, loc, watts, rgb, radius=0.1):
    d = bpy.data.lights.new(name, "POINT"); d.energy = watts; d.color = srgb(rgb); d.shadow_soft_size = radius
    o = bpy.data.objects.new(name, d); o.location = loc
    bpy.context.scene.collection.objects.link(o)
    return o


def area(name, loc, rot_deg, watts, rgb, size=2.0):
    d = bpy.data.lights.new(name, "AREA"); d.energy = watts; d.color = srgb(rgb); d.size = size
    o = bpy.data.objects.new(name, d); o.location = loc; o.rotation_euler = [math.radians(a) for a in rot_deg]
    bpy.context.scene.collection.objects.link(o)
    return o


def camera(keys, lens=35, dof_target=None, fstop=4.0):
    """keys: [(frame, (x,y,z), (rx,ry,rz) degrees)]"""
    c = bpy.data.cameras.new("CAM"); c.lens = lens
    o = bpy.data.objects.new("CAM", c); bpy.context.scene.collection.objects.link(o)
    bpy.context.scene.camera = o
    for f, loc, rot in keys:
        o.location = loc; o.rotation_euler = [math.radians(a) for a in rot]
        o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)
    if o.animation_data:
        for fc in o.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "BEZIER"
    if dof_target is not None:
        c.dof.use_dof = True; c.dof.focus_distance = dof_target; c.dof.aperture_fstop = fstop
    return o


def output(sc, W, H, frames, samples, out_dir, fps=30):
    sc.render.resolution_x, sc.render.resolution_y = W, H
    sc.render.resolution_percentage = 100
    sc.frame_start, sc.frame_end = 1, frames
    sc.render.fps = fps
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.max_bounces = 4
    sc.cycles.diffuse_bounces = 2
    sc.cycles.glossy_bounces = 1
    sc.cycles.transparent_max_bounces = 4
    sc.cycles.volume_bounces = 0
    sc.cycles.volume_step_rate = 4.0
    try:
        sc.cycles.use_denoising = True
        sc.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception:
        pass
    sc.render.use_persistent_data = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = out_dir.rstrip("/") + "/bg_"
    sc.render.film_transparent = False
    depth_output(sc, out_dir)


DEPTH_MAX_M = 300.0


def depth_output(sc, out_dir):
    """Also write a 16-bit depth map per frame (depth_####.png, 0 = camera, 1 = DEPTH_MAX_M metres)
    so 2D characters can be hidden behind nearer 3D objects when composited."""
    sc.view_layers[0].use_pass_z = True
    sc.use_nodes = True
    nt = sc.node_tree
    rl = nt.nodes.get("Render Layers") or nt.nodes.new("CompositorNodeRLayers")
    mr = nt.nodes.new("CompositorNodeMapRange")
    mr.inputs["From Min"].default_value = 0.0
    mr.inputs["From Max"].default_value = DEPTH_MAX_M
    mr.inputs["To Min"].default_value = 0.0
    mr.inputs["To Max"].default_value = 1.0
    mr.use_clamp = True
    nt.links.new(rl.outputs["Depth"], mr.inputs["Value"])
    fo = nt.nodes.new("CompositorNodeOutputFile")
    fo.base_path = out_dir
    fo.format.file_format = "PNG"
    fo.format.color_mode = "BW"
    fo.format.color_depth = "16"
    fo.format.color_management = "OVERRIDE"
    fo.format.view_settings.view_transform = "Standard"
    fo.file_slots[0].path = "depth_"
    nt.links.new(mr.outputs["Value"], fo.inputs[0])


def export_anchors(sc, path, out_fps=30):
    """Per output frame (at out_fps, even if the scene runs at a lower fps): screen x,y (0..1, origin
    top-left), pixels-per-metre and camera depth for every ANC_ empty."""
    cam = sc.camera
    anchors = [o for o in sc.objects if o.name.startswith("ANC_")]
    H = sc.render.resolution_y
    src_fps = sc.render.fps
    n_out = int(round((sc.frame_end - sc.frame_start) / src_fps * out_fps)) + 1
    out = {"W": sc.render.resolution_x, "H": H, "fps": out_fps, "frames": []}
    for k in range(n_out):
        f = sc.frame_start + k * src_fps / out_fps
        sc.frame_set(int(f), subframe=f - int(f))
        fr = {}
        for a in anchors:
            p = a.matrix_world.translation
            v = world_to_camera_view(sc, cam, p)
            v2 = world_to_camera_view(sc, cam, p + Vector((0, 0, 1.0)))
            fr[a.name[4:]] = [round(v.x, 5), round(1 - v.y, 5), round(abs(v2.y - v.y) * H, 3), round(v.z, 3)]
        out["frames"].append(fr)
    with open(path, "w") as f:
        json.dump(out, f)


def move(obj, frames_fps, start, velocity, frames, stop_at=None):
    """Keyframe obj moving at `velocity` (vector m/s) from `start`; optionally ease to a stop at stop_at s."""
    fps = frames_fps
    T = (frames - 1) / fps
    if stop_at is None or stop_at >= T:
        keys = [(0.0, 0.0), (T, T)]
    else:
        brake = 0.8                                      # seconds of braking
        keys = [(0.0, 0.0), (stop_at, stop_at), (stop_at + brake, stop_at + brake / 2), (T, stop_at + brake / 2)]
    for t, dist_t in keys:
        obj.location = tuple(s + v * dist_t for s, v in zip(start, velocity))
        obj.keyframe_insert("location", frame=1 + t * fps)
    for fc in obj.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "BEZIER" if stop_at is not None else "LINEAR"
