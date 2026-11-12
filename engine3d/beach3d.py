"""3D night beach: real ocean waves (Ocean modifier), moonlit sky, tide climbing the sand.
python(bpy) beach3d.py timing.json shot_index out_dir [--still F]
moon: on (Moon rises, tide climbs high) | off (no Moon, darker, tide barely moves)
"""
import bpy, json, math, random, sys, addon_utils
addon_utils.enable("cycles")
a = sys.argv[1:]
T = json.load(open(a[0])); SH = T["shots"][int(a[1])]; OUT = a[2]
STILL = int(a[a.index("--still") + 1]) if "--still" in a else None
NF = SH["frames"]; ON = SH.get("moon", "on") == "on"

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 10; sc.cycles.use_denoising = True
sc.cycles.max_bounces = 3; sc.render.use_persistent_data = True
sc.render.resolution_x, sc.render.resolution_y = 720, 1280; sc.render.fps = T["fps"]; sc.frame_start, sc.frame_end = 1, NF
sc.view_settings.view_transform = "AgX"

def mat(name, color, rough=0.5, emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rough
    if emit: b.inputs["Emission Color"].default_value = (*color, 1); b.inputs["Emission Strength"].default_value = emit
    return m

def bump(m, scale, strength):
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = strength
    nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])

# ---------- sky: night gradient + stars (brighter blue when the Moon is up)
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True; nt = w.node_tree; bg = nt.nodes["Background"]
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
ramp = nt.nodes.new("ShaderNodeValToRGB"); el = ramp.color_ramp.elements
el[0].position = 0.0; el[1].position = 0.45
el[0].color = (0.05, 0.11, 0.2, 1) if ON else (0.01, 0.02, 0.04, 1); el[1].color = (0.004, 0.008, 0.03, 1)
vor = nt.nodes.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 260
mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Max"].default_value = 0.06; mr.inputs["To Min"].default_value = 1.0; mr.inputs["To Max"].default_value = 0.0
pw = nt.nodes.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 5
add = nt.nodes.new("ShaderNodeMix"); add.data_type = "RGBA"; add.blend_type = "ADD"; add.inputs["Factor"].default_value = 1
nt.links.new(tc.outputs["Generated"], sep.inputs[0]); nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
nt.links.new(vor.outputs["Distance"], mr.inputs["Value"]); nt.links.new(mr.outputs["Result"], pw.inputs[0])
nt.links.new(ramp.outputs["Color"], add.inputs[6]); nt.links.new(pw.outputs["Value"], add.inputs[7]); nt.links.new(add.outputs[2], bg.inputs["Color"])

# ---------- sand slope down into the sea (+Y)
bpy.ops.mesh.primitive_grid_add(x_subdivisions=160, y_subdivisions=160, size=1)
sand = bpy.context.object; sand.scale = (60, 60, 1); bpy.ops.object.transform_apply(scale=True)
for v in sand.data.vertices:
    x, y = v.co.x, v.co.y
    v.co.z = (-0.10 * (y - 1.0) if y > 1.0 else 0.0) + 0.04 * math.sin(x * 0.9 + y * 0.3) - (max(0, abs(x) - 12) * 0.2 if y > 4 else 0)
bpy.ops.object.shade_smooth()
ms = mat("sand", (0.62, 0.5, 0.36), 0.85); bump(ms, 80, 0.12); sand.data.materials.append(ms)

# ---------- ocean with real waves
bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, 0))
sea = bpy.context.object
oc = sea.modifiers.new("ocean", "OCEAN")
oc.geometry_mode = "GENERATE"; oc.resolution = 12; oc.spatial_size = 30; oc.repeat_x = 4; oc.repeat_y = 4
oc.wave_scale = 0.9; oc.choppiness = 1.1; oc.wind_velocity = 9; oc.wave_alignment = 0.3; oc.wave_direction = math.radians(-90)
oc.time = 0; oc.keyframe_insert("time", frame=1); oc.time = NF / T["fps"] * 1.0; oc.keyframe_insert("time", frame=NF)
for fc in sea.animation_data.action.fcurves if sea.animation_data and getattr(sea.animation_data.action, "fcurves", None) else []:
    for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
bpy.ops.object.shade_smooth()
msea = mat("sea", (0.01, 0.07, 0.12), 0.06); b = msea.node_tree.nodes["Principled BSDF"]; b.inputs["Coat Weight"].default_value = 0.4
sea.data.materials.append(msea)
sea.location = (-60, -12, 0)
lo, hi = (-0.85, -0.22) if ON else (-0.66, -0.56)
for f in range(1, NF + 1, 4):
    k = (f - 1) / max(NF - 1, 1)
    z = lo + (hi - lo) * (k * k * (3 - 2 * k)) if ON else (lo + hi) / 2 + (hi - lo) / 2 * math.sin(k * 6)
    sea.location.z = z; sea.keyframe_insert("location", index=2, frame=f)

# ---------- moon (rises while on), rocks, palm
moon = None
if ON:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=4.0, location=(-9, 90, 9)); moon = bpy.context.object
    bpy.ops.object.shade_smooth(); mm = mat("moon", (1.0, 0.95, 0.85), 0.9, emit=0.9); bump(mm, 4, 2.0); moon.data.materials.append(mm)
    moon.keyframe_insert("location", frame=1); moon.location = (-6, 90, 19); moon.keyframe_insert("location", frame=NF)
    ml = bpy.data.lights.new("MoonLight", "SUN"); ml.energy = 1.6; ml.color = (0.75, 0.82, 1.0); ml.angle = math.radians(1)
    mo = bpy.data.objects.new("MoonLight", ml); bpy.context.collection.objects.link(mo); mo.rotation_euler = (math.radians(70), 0, math.radians(165))
amb = bpy.data.lights.new("Amb", "SUN"); amb.energy = 0.35 if ON else 0.18; amb.color = (0.5, 0.6, 1.0)
ao = bpy.data.objects.new("Amb", amb); bpy.context.collection.objects.link(ao); ao.rotation_euler = (math.radians(40), 0, math.radians(30))
mrock = mat("rock", (0.12, 0.11, 0.11), 0.8)
for (x, y, r) in ((-3.0, 3.0, 0.9), (-4.2, 5.5, 1.3), (2.8, 2.2, 0.5), (3.6, 6.5, 1.0)):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=r, location=(x, y, r * 0.1)); rk = bpy.context.object
    rk.scale = (1.3, 1, 0.7); rk.data.materials.append(mrock)
    tx = bpy.data.textures.new("rn", "CLOUDS"); tx.noise_scale = 0.5; md = rk.modifiers.new("d", "DISPLACE"); md.texture = tx; md.strength = r * 0.4
    bpy.ops.object.shade_smooth()

# ---------- camera: low, looking out to sea; slow push
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); bpy.context.collection.objects.link(cam)
sc.camera = cam; cam_d.lens = 22; cam_d.sensor_fit = "VERTICAL"; cam_d.sensor_height = 24
tgt = bpy.data.objects.new("T", None); bpy.context.collection.objects.link(tgt); tgt.location = (0, 12, 1.0)
c = cam.constraints.new("TRACK_TO"); c.target = tgt; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
cam.location = (0.6, -4.5, 2.3); cam.keyframe_insert("location", frame=1); cam.location = (0.3, -3.4, 2.0); cam.keyframe_insert("location", frame=NF)

sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 94
if STILL:
    sc.frame_set(STILL); sc.render.filepath = f"{OUT}/still.jpg"; bpy.ops.render.render(write_still=True)
else:
    sc.render.filepath = f"{OUT}/f_"; bpy.ops.render.render(animation=True)
