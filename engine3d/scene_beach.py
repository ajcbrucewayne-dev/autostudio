"""Step 2 (Blender python): build a stylized 3D beach scene with Blip and render frames.
python(bpy) scene_beach.py <timing.json> <frames_dir> [start end] [--still N]
"""
import bpy, json, math, random, sys, addon_utils
from mathutils import Vector
addon_utils.enable("cycles")
args = sys.argv[1:]
T = json.load(open(args[0])); OUT = args[1]
STILL = int(args[args.index("--still") + 1]) if "--still" in args else None
RES = (540, 960) if "--hi" not in args else (720, 1280)
FPS = T["fps"]; NF = T["frames"]; AMP = T["amp"]
seg_frame = lambda i, k="t0": int(T["segs"][i][k] * FPS)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 12
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 4; sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
sc.render.use_persistent_data = True
sc.render.resolution_x, sc.render.resolution_y = RES; sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, NF
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy" if "AgX - Punchy" in [l.identifier for l in bpy.types.ColorManagedViewSettings.bl_rna.properties["look"].enum_items] else "None"

def mat(name, color, rough=0.5, emit=0.0, sss=0.0, coat=0.0, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if sss: b.inputs["Subsurface Weight"].default_value = sss; b.inputs["Subsurface Radius"].default_value = (0.3, 0.6, 0.6)
    if coat: b.inputs["Coat Weight"].default_value = coat
    if emit: b.inputs["Emission Color"].default_value = (*color, 1); b.inputs["Emission Strength"].default_value = emit
    return m

def add_bump(m, scale, strength, w_keys=None):
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale
    if w_keys:
        nz.noise_dimensions = "4D"
        nz.inputs["W"].default_value = 0; nz.inputs["W"].keyframe_insert("default_value", frame=1)
        nz.inputs["W"].default_value = w_keys; nz.inputs["W"].keyframe_insert("default_value", frame=NF)
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = strength
    nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])

def sphere(name, loc, scale, m, seg=48, parent=None, smooth=True):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, location=loc)
    o = bpy.context.object; o.name = name; o.scale = scale; o.data.materials.append(m)
    if smooth: bpy.ops.object.shade_smooth()
    if parent: o.parent = parent; o.location = loc
    return o

# ---------- world: stylized sunset gradient + stars
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True; nt = w.node_tree
bg = nt.nodes["Background"]; tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = -0.02; mr.inputs["From Max"].default_value = 0.55
ramp = nt.nodes.new("ShaderNodeValToRGB"); el = ramp.color_ramp.elements
el[0].position = 0.0; el[0].color = (1.0, 0.42, 0.15, 1)
el[1].position = 1.0; el[1].color = (0.015, 0.02, 0.09, 1)
e2 = el.new(0.18); e2.color = (0.9, 0.25, 0.35, 1)
e3 = el.new(0.45); e3.color = (0.22, 0.08, 0.35, 1)
nt.links.new(tc.outputs["Generated"], sep.inputs[0]); nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"]); nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
bg.inputs["Strength"].default_value = 0.9

# ---------- sand (slopes into the sea toward +Y)
bpy.ops.mesh.primitive_grid_add(x_subdivisions=120, y_subdivisions=120, size=1, location=(0, 0, 0))
sand = bpy.context.object; sand.name = "Sand"; sand.scale = (40, 60, 1); bpy.ops.object.transform_apply(scale=True)
rnd = random.Random(3)
for v in sand.data.vertices:
    x, y = v.co.x, v.co.y
    v.co.z = (-0.13 * (y - 0.5) if y > 0.5 else 0.0) + 0.03 * math.sin(x * 1.3) * math.cos(y * 0.9)
    v.co.z -= max(0, abs(x) - 9) * 0.25 if y > 3 else 0
bpy.ops.object.shade_smooth()
ms = mat("sand", (0.85, 0.62, 0.38), 0.95); add_bump(ms, 60, 0.15); sand.data.materials.append(ms)

# ---------- ocean (rises = tide)
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 40, -0.75))
sea = bpy.context.object; sea.name = "Sea"; sea.scale = (200, 80, 1)
msea = mat("sea", (0.02, 0.22, 0.42), 0.04, coat=0.3); add_bump(msea, 3.0, 0.25, w_keys=NF / FPS * 0.6)
sea.data.materials.append(msea)
tide_a, tide_b = seg_frame(1), seg_frame(3) + 6
sea.location.z = -0.75; sea.keyframe_insert("location", index=2, frame=tide_a)
sea.location.z = -0.04; sea.keyframe_insert("location", index=2, frame=tide_b)
# shoreline foam ring follows the tide line
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
foam = bpy.context.object; foam.scale = (60, 0.25, 1)
foam.data.materials.append(mat("foam", (0.95, 0.97, 1.0), 0.6, emit=0.15))
for f, z in ((tide_a, -0.75), (tide_b, -0.04)):
    foam.location = (0, 0.5 + (-z) / 0.13, z + 0.012); foam.keyframe_insert("location", frame=f)
for f in range(1, NF + 1, 6):  # gentle lapping
    foam.scale.y = 0.25 + 0.12 * math.sin(f * 0.35); foam.keyframe_insert("scale", index=1, frame=f)

# ---------- moon + stars
mmoon = mat("moon", (1.0, 0.93, 0.75), 0.8, emit=0.7); add_bump(mmoon, 3, 1.5)
moon = sphere("Moon", (-7, 80, 16), (4.5, 4.5, 4.5), mmoon)
mstar = mat("star", (1, 1, 1), 0.5, emit=8)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.12, location=(0, 0, 0)); star = bpy.context.object; star.data.materials.append(mstar)
for i in range(140):
    s = star.copy(); bpy.context.collection.objects.link(s)
    s.location = (rnd.uniform(-60, 60), rnd.uniform(70, 120), rnd.uniform(18, 70)); s.scale = [rnd.uniform(0.6, 1.6)] * 3
bpy.data.objects.remove(star)

# ---------- palm tree + rocks
bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0))
trunk = bpy.context.object; sp = trunk.data.splines[0]
sp.bezier_points[0].co = (1.9, 3.0, 0); sp.bezier_points[0].handle_left = (1.8, 3.0, -1); sp.bezier_points[0].handle_right = (2.0, 3.0, 1.5)
sp.bezier_points[1].co = (2.6, 3.4, 3.4); sp.bezier_points[1].handle_left = (2.1, 3.2, 2.6); sp.bezier_points[1].handle_right = (3.0, 3.6, 4.2)
trunk.data.bevel_depth = 0.16; trunk.data.bevel_resolution = 4
trunk.data.materials.append(mat("bark", (0.35, 0.2, 0.1), 0.9))
mleaf = mat("leaf", (0.12, 0.45, 0.12), 0.5, sss=0.2)
for k in range(7):
    a = k * 2 * math.pi / 7
    bpy.ops.mesh.primitive_cube_add(location=(2.6 + math.cos(a) * 0.9, 3.4 + math.sin(a) * 0.9, 3.3))
    lf = bpy.context.object; lf.scale = (1.0, 0.22, 0.02); lf.rotation_euler = (0, 0.45, a)
    bpy.ops.object.modifier_add(type="SUBSURF"); lf.modifiers[-1].levels = 2; lf.data.materials.append(mleaf)
    bpy.ops.object.shade_smooth()
mrock = mat("rock", (0.3, 0.28, 0.27), 0.8)
for (x, y, r) in ((-1.9, 2.0, 0.5), (-2.4, 3.6, 0.8), (1.4, 1.0, 0.3)):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=r, location=(x, y, r * 0.2))
    rk = bpy.context.object; rk.scale = (1.2, 1, 0.7); rk.data.materials.append(mrock)
    tx = bpy.data.textures.new("rn", "CLOUDS"); tx.noise_scale = 0.4
    m = rk.modifiers.new("d", "DISPLACE"); m.texture = tx; m.strength = r * 0.35
    bpy.ops.object.shade_smooth()

# ---------- Blip: glossy gummy blob character
rig = bpy.data.objects.new("Rig", None); bpy.context.collection.objects.link(rig); rig.location = (0, 0.6, 0)
mbody = mat("blip", (0.1, 0.75, 0.68), 0.28, sss=0.35, coat=0.6)
body = sphere("Body", (0, 0, 0.62), (0.62, 0.55, 0.62), mbody, parent=rig)
body_scale = Vector(body.scale)
mwhite = mat("eye", (1, 1, 1), 0.15, coat=0.8); mblack = mat("pupil", (0.01, 0.01, 0.015), 0.1, coat=1)
mshine = mat("shine", (1, 1, 1), 0.2, emit=6); mmouth = mat("mouth", (0.25, 0.02, 0.04), 0.4)
mcheek = mat("cheek", (1.0, 0.35, 0.45), 0.6, emit=0.3)
head = bpy.data.objects.new("Head", None); bpy.context.collection.objects.link(head); head.parent = rig; head.location = (0, 0, 0.62)
eyes, pupils = [], []
for sx in (-1, 1):
    e = sphere(f"Eye{sx}", (0.2 * sx, -0.43, 0.2), (0.16, 0.1, 0.19), mwhite, parent=head); eyes.append(e)
    p = sphere(f"Pupil{sx}", (0.2 * sx, -0.52, 0.18), (0.085, 0.04, 0.1), mblack, parent=head); pupils.append(p)
    sphere(f"Shine{sx}", (0.2 * sx + 0.035, -0.56, 0.25), (0.025, 0.012, 0.025), mshine, parent=p).location = (0.4, -0.4, 0.7)
    sphere(f"Cheek{sx}", (0.36 * sx, -0.4, -0.05), (0.09, 0.03, 0.05), mcheek, parent=head)
mouth = sphere("Mouth", (0, -0.53, -0.12), (0.12, 0.04, 0.03), mmouth, parent=head)
for p in pupils: p.children[0].location = (0.35, -0.6, 0.6); p.children[0].scale = (0.3, 0.3, 0.3)

# ---------- animate Blip
def act_window(name):
    for i, s in enumerate(T["segs"]):
        if s["act"] == name: return int(s["t0"] * FPS), int(s["t1"] * FPS) + 8
    return (10 ** 9, 10 ** 9)
LOOK = act_window("look_up"); JUMP = act_window("jump"); WAVE = act_window("wave"); POINT = act_window("point")
talking = lambda f: any(s["t0"] * FPS <= f <= s["t1"] * FPS for s in T["segs"])
blinks = set(range(40, NF, 77))
for f in range(1, NF + 1):
    a = AMP[min(f - 1, len(AMP) - 1)]
    sq = 0.03 * math.sin(f * 0.26) + (0.06 * a if talking(f) else 0)
    jz = 0.0
    if JUMP[0] + 4 <= f <= JUMP[0] + 22:
        p = (f - JUMP[0] - 4) / 18; jz = 1.2 * 4 * p * (1 - p); sq = 0.18 * (1 - 2 * abs(p - 0.5)) if 0 < p < 1 else -0.12
    body.scale = (body_scale.x * (1 - sq * 0.6), body_scale.y * (1 - sq * 0.6), body_scale.z * (1 + sq))
    body.keyframe_insert("scale", frame=f)
    rig.location.z = jz; rig.keyframe_insert("location", index=2, frame=f)
    head.location.z = 0.62 * (1 + sq); head.keyframe_insert("location", index=2, frame=f)
    # look toward camera, or up at the moon / out to sea
    up = LOOK[0] <= f <= LOOK[1] + 20 or POINT[0] <= f <= POINT[1]
    rig.rotation_euler.x = math.radians(-12 if up else 0); rig.rotation_euler.z = math.radians(-18 if up else 6 * math.sin(f * 0.05))
    rig.keyframe_insert("rotation_euler", frame=f)
    shock = JUMP[0] <= f <= JUMP[1] + 10
    for e, p in zip(eyes, pupils):
        blink = any(b <= f < b + 3 for b in blinks)
        e.scale.z = 0.02 if blink else (0.24 if shock else 0.19); e.keyframe_insert("scale", index=2, frame=f)
        p.scale.z = 0.01 if blink else (0.07 if shock else 0.1); p.keyframe_insert("scale", index=2, frame=f)
        p.location.z = 0.26 if up else 0.18; p.keyframe_insert("location", index=2, frame=f)
    mo = a if talking(f) else 0
    mouth.scale = (0.12 - 0.03 * mo if not shock else 0.08, 0.04, 0.025 + 0.11 * mo if not shock else 0.12)
    mouth.keyframe_insert("scale", frame=f)

# ---------- lights
def light(kind, rot, energy, color, angle=None):
    l = bpy.data.lights.new(kind, kind); l.energy = energy; l.color = color
    if angle is not None: l.angle = math.radians(angle)
    o = bpy.data.objects.new(kind, l); bpy.context.collection.objects.link(o); o.rotation_euler = [math.radians(r) for r in rot]; return o
light("SUN", (60, 0, -35), 2.6, (1.0, 0.82, 0.68), 6)   # warm key from front-left
light("SUN", (75, 0, 160), 4.0, (1.0, 0.45, 0.25), 3)   # sunset rim from behind
light("SUN", (50, 0, 40), 0.6, (0.5, 0.6, 1.0), 20)     # cool fill

# ---------- camera: slow push-in, shallow depth of field
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); bpy.context.collection.objects.link(cam)
sc.camera = cam; cam_d.lens = 24; cam_d.sensor_fit = "VERTICAL"
tgt = bpy.data.objects.new("Tgt", None); bpy.context.collection.objects.link(tgt); tgt.location = (0, 3.0, 1.2)
c = cam.constraints.new("TRACK_TO"); c.target = tgt; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
cam_d.dof.use_dof = True; cam_d.dof.focus_object = body; cam_d.dof.aperture_fstop = 2.2
cam.location = (0.7, -6.4, 2.4); cam.keyframe_insert("location", frame=1)
cam.location = (0.4, -5.2, 2.1); cam.keyframe_insert("location", frame=NF)

sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 95
if STILL:
    sc.frame_set(STILL); sc.render.filepath = f"{OUT}/still_{STILL}.jpg"; bpy.ops.render.render(write_still=True)
else:
    if len(args) >= 4 and args[2].isdigit(): sc.frame_start, sc.frame_end = int(args[2]), int(args[3])
    sc.render.filepath = f"{OUT}/f_"; bpy.ops.render.render(animation=True)
