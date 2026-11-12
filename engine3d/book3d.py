"""Pop-up storybook proof: desk + lamp, book opens, beach diorama pops up, Moon on a stick rises, tide rolls in.
python(bpy) book3d.py timing.json 0 out_dir [--still F]
"""
import bpy, json, math, random, sys, addon_utils
addon_utils.enable("cycles")
a = sys.argv[1:]
T = json.load(open(a[0])); SH = T["shots"][int(a[1])]; OUT = a[2]
STILL = int(a[a.index("--still") + 1]) if "--still" in a else None
NF = SH["frames"]; FPS = T["fps"]; F = lambda s: int(s * FPS) + 1
ROOT = "/home/user/autostudio"

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 12; sc.cycles.use_denoising = True
sc.cycles.max_bounces = 4; sc.render.use_persistent_data = True
sc.render.resolution_x, sc.render.resolution_y = 720, 1280; sc.render.fps = FPS; sc.frame_start, sc.frame_end = 1, NF
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
col = bpy.context.collection

def smooth(k): k = max(0.0, min(1.0, k)); return k * k * (3 - 2 * k)
def back(k):
    k = max(0.0, min(1.0, k)); c1 = 1.9; c3 = c1 + 1; return 1 + c3 * (k - 1) ** 3 + c1 * (k - 1) ** 2

def mat(name, color, rough=0.5, emit=0.0, coat=0.0, bumpscale=0.0, bumpstr=0.1):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rough
    if coat: b.inputs["Coat Weight"].default_value = coat
    if emit: b.inputs["Emission Color"].default_value = (*color, 1); b.inputs["Emission Strength"].default_value = emit
    if bumpscale:
        nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = bumpscale; nz.inputs["Detail"].default_value = 8
        bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bumpstr
        nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m

def cube(name, loc, size, m, parent=None, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel: md = o.modifiers.new("b", "BEVEL"); md.width = bevel; md.segments = 3
    o.data.materials.append(m)
    if parent: o.parent = parent
    return o

def sphere(name, loc, r, m, parent=None, scale=(1, 1, 1), seg=32):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=r, location=loc); o = bpy.context.object
    o.name = name; o.scale = scale; bpy.ops.object.shade_smooth(); o.data.materials.append(m)
    if parent: o.parent = parent
    return o

def empty(name, loc=(0, 0, 0), parent=None):
    e = bpy.data.objects.new(name, None); col.objects.link(e); e.location = loc
    if parent: e.parent = parent
    return e

def text(body, size, loc, m, parent=None, rot=(0, 0, 0), font=None):
    bpy.ops.object.text_add(location=(0, 0, 0)); o = bpy.context.object; o.data.body = body; o.data.size = size
    o.data.align_x = "CENTER"; o.data.align_y = "CENTER"; o.data.extrude = 0.002
    if font: o.data.font = bpy.data.fonts.load(font)
    o.data.materials.append(m); o.parent = parent; o.location = loc; o.rotation_euler = rot
    return o

# ---------- world + desk
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.006, 0.004, 0.003, 1)
mdesk = bpy.data.materials.new("desk"); mdesk.use_nodes = True; nt = mdesk.node_tree; b = nt.nodes["Principled BSDF"]
wave = nt.nodes.new("ShaderNodeTexWave"); wave.inputs["Scale"].default_value = 3; wave.inputs["Distortion"].default_value = 6
wave.inputs["Detail"].default_value = 4
cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.09, 0.04, 0.018, 1); cr.color_ramp.elements[1].color = (0.22, 0.11, 0.05, 1)
nt.links.new(wave.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.45
bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, 0)); bpy.context.object.data.materials.append(mdesk)
# toy blocks in the background
for (x, y, s, c, r) in ((-1.35, 1.1, 0.26, (0.7, 0.12, 0.1), 0.3), (-1.0, 1.45, 0.22, (0.15, 0.35, 0.7), -0.2), (1.9, 1.3, 0.24, (0.85, 0.65, 0.12), 0.5)):
    o = cube("blk", (x, y, s / 2), (s, s, s), mat("blk", c, 0.4), bevel=0.012); o.rotation_euler.z = r

# ---------- the book (spine along x=0; right block = pages, cover hinges open to the left)
red = mat("cover", (0.45, 0.04, 0.035), 0.55, bumpscale=120, bumpstr=0.08)
paper = mat("paper", (0.86, 0.8, 0.66), 0.85, bumpscale=200, bumpstr=0.05)
gold = mat("gold", (0.85, 0.62, 0.22), 0.3, emit=0.15)
ink = mat("ink", (0.08, 0.06, 0.05), 0.6)
cube("board", (0.51, 0, 0.006), (1.04, 1.46, 0.012), red, bevel=0.004)
pages = cube("pages", (0.5, 0, 0.06), (1.0, 1.42, 0.096), paper)
hinge = empty("Hinge", (0, 0, 0.108))
cover = cube("cover", (0.51, 0, 0.007), (1.04, 1.46, 0.014), red, parent=hinge, bevel=0.004)
inner = cube("inner", (0.5, 0, -0.002), (1.0, 1.42, 0.004), paper, parent=hinge)
serif = f"{ROOT}/fonts/DejaVuSerif-Bold.ttf"
text("What If\nthe Moon\nVanished?", 0.13, (0.5, 0.05, 0.016), gold, parent=hinge, font=serif)
text("~ a Leo story ~", 0.05, (0.5, -0.5, 0.016), gold, parent=hinge, font=serif)
text("What if the Moon...\nvanished?", 0.075, (0.5, 0.15, -0.0045), ink, parent=hinge, rot=(0, math.pi, 0), font=serif)
hinge.rotation_euler.y = 0; hinge.keyframe_insert("rotation_euler", index=1, frame=F(3.2))
hinge.rotation_euler.y = -math.pi; hinge.keyframe_insert("rotation_euler", index=1, frame=F(4.7))

# ---------- pop-up beach diorama on the right page
pop = empty("Pop", (0.5, 0, 0.108))
pop.scale = (1, 1, 0.01); pop.keyframe_insert("scale", frame=F(4.4))
for f in range(F(4.4), F(5.4) + 1):
    pop.scale.z = max(0.01, back((f - F(4.4)) / (F(5.4) - F(4.4)))); pop.keyframe_insert("scale", index=2, frame=f)
# painted night backdrop with paper stars
bk = bpy.data.materials.new("backdrop"); bk.use_nodes = True; nt = bk.node_tree; b = nt.nodes["Principled BSDF"]
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); rp = nt.nodes.new("ShaderNodeValToRGB")
rp.color_ramp.elements[0].color = (0.06, 0.1, 0.3, 1); rp.color_ramp.elements[1].color = (0.01, 0.015, 0.06, 1)
nt.links.new(tc.outputs["Generated"], sep.inputs[0]); nt.links.new(sep.outputs["Z"], rp.inputs["Fac"]); nt.links.new(rp.outputs["Color"], b.inputs["Base Color"])
b.inputs["Roughness"].default_value = 0.9
cube("backdrop", (0, 0.6, 0.42), (0.96, 0.012, 0.84), bk, parent=pop)
star = mat("star", (1.0, 0.92, 0.6), 0.5, emit=6)
rnd = random.Random(4)
for i in range(26):
    sphere("st", (rnd.uniform(-0.44, 0.44), 0.592, rnd.uniform(0.35, 0.82)), rnd.uniform(0.005, 0.011), star, parent=pop, seg=8)
for sx in (-1, 1):  # paper side walls (diorama box)
    cube("wall", (sx * 0.475, 0.25, 0.1), (0.012, 0.7, 0.2), mat("wall", (0.12, 0.2, 0.32), 0.9, bumpscale=150, bumpstr=0.05), parent=pop)
# sand: slopes up toward the camera
bpy.ops.mesh.primitive_grid_add(x_subdivisions=60, y_subdivisions=60, size=1); sand = bpy.context.object
sand.scale = (0.94, 1.16, 1); bpy.ops.object.transform_apply(scale=True)
for v in sand.data.vertices:
    y = v.co.y; v.co.z = (0.1 - y) * 0.2 + 0.004
    v.co.y += 0.02
bpy.ops.object.shade_smooth(); sand.data.materials.append(mat("sand", (0.78, 0.6, 0.38), 0.9, bumpscale=300, bumpstr=0.15)); sand.parent = pop
# water with real little waves
bpy.ops.mesh.primitive_plane_add(size=1); sea = bpy.context.object
oc = sea.modifiers.new("ocean", "OCEAN"); oc.geometry_mode = "GENERATE"; oc.resolution = 9; oc.spatial_size = 2; oc.repeat_x = 1; oc.repeat_y = 1
oc.wave_scale = 0.012; oc.choppiness = 1.2; oc.wind_velocity = 6; oc.wave_alignment = 0.4; oc.wave_direction = math.radians(-90)
oc.time = 0; oc.keyframe_insert("time", frame=1); oc.time = NF / FPS * 1.4; oc.keyframe_insert("time", frame=NF)
sea.scale = (0.47, 0.55, 1); sea.parent = pop
msea = mat("sea", (0.01, 0.12, 0.2), 0.05, coat=0.6); bpy.ops.object.shade_smooth(); sea.data.materials.append(msea)
lo, hi = 0.0, 0.07
sea.location = (0, 0.06, lo); sea.keyframe_insert("location", frame=F(8.4))
for f in range(F(8.4), F(12.0) + 1, 3):
    sea.location.z = lo + (hi - lo) * smooth((f - F(8.4)) / (F(12.0) - F(8.4))); sea.keyframe_insert("location", index=2, frame=f)
# palm tree + rocks
bpy.ops.curve.primitive_bezier_curve_add(); tr = bpy.context.object; sp = tr.data.splines[0]
sp.bezier_points[0].co = (0.36, 0.3, 0.02); sp.bezier_points[0].handle_left = (0.36, 0.3, -0.05); sp.bezier_points[0].handle_right = (0.36, 0.3, 0.2)
sp.bezier_points[1].co = (0.28, 0.36, 0.5); sp.bezier_points[1].handle_left = (0.33, 0.33, 0.38); sp.bezier_points[1].handle_right = (0.24, 0.38, 0.58)
tr.data.bevel_depth = 0.014; tr.data.materials.append(mat("bark", (0.32, 0.18, 0.08), 0.85)); tr.parent = pop
leaf = mat("leaf", (0.12, 0.42, 0.14), 0.5)
for k in range(7):
    an = k * 2 * math.pi / 7
    o = cube("leaf", (0.28 + math.cos(an) * 0.07, 0.36 + math.sin(an) * 0.07, 0.5), (0.16, 0.04, 0.004), leaf, parent=pop)
    o.rotation_euler = (0, 0.45, an); m2 = o.modifiers.new("s", "SUBSURF"); m2.levels = 2
for (x, y, r) in ((-0.36, -0.1, 0.05), (-0.3, 0.05, 0.035)):
    sphere("rock", (x, y, 0.02), r, mat("rock", (0.22, 0.2, 0.2), 0.8), parent=pop, scale=(1.3, 1, 0.7), seg=16)

# ---------- Moon on a wooden stick, rises from behind the backdrop
stick_e = empty("MoonStick", (0.1, 0.64, 0.0), parent=pop)
bpy.ops.mesh.primitive_cylinder_add(radius=0.006, depth=0.9, location=(0, 0, 0.0)); stk = bpy.context.object
stk.data.materials.append(mat("wood", (0.5, 0.33, 0.18), 0.6)); stk.parent = stick_e
moonm = mat("moon", (1.0, 0.95, 0.8), 0.9, emit=0.8, bumpscale=8, bumpstr=0.9)
mn = sphere("Moon", (0, 0, 0.45), 0.085, moonm, parent=stick_e, seg=48)
ml = bpy.data.lights.new("MoonGlow", "POINT"); ml.energy = 0; ml.color = (0.6, 0.75, 1.0); ml.shadow_soft_size = 0.1
mlo = bpy.data.objects.new("MoonGlow", ml); col.objects.link(mlo); mlo.parent = stick_e; mlo.location = (0, -0.12, 0.45)
stick_e.location.z = -0.05; stick_e.keyframe_insert("location", index=2, frame=F(6.4))
ml.keyframe_insert("energy", frame=F(6.4))
for f in range(F(6.4), F(9.2) + 1, 2):
    k = smooth((f - F(6.4)) / (F(9.2) - F(6.4)))
    stick_e.location.z = -0.05 + 0.44 * k; stick_e.location.x = 0.1 - 0.12 * k; stick_e.keyframe_insert("location", frame=f)
    ml.energy = 6 * k; ml.keyframe_insert("energy", frame=f)

# ---------- Leo figurine (vinyl toy)
leo = empty("Leo", (0.1, -0.33, 0.098), parent=pop)
skin = mat("skin", (0.62, 0.38, 0.24), 0.4, coat=0.3); hood = mat("hood", (0.95, 0.62, 0.05), 0.45, coat=0.4)
shorts = mat("shorts", (0.3, 0.2, 0.12), 0.6); shoe = mat("shoe", (0.75, 0.08, 0.06), 0.35, coat=0.5)
hair = mat("hair", (0.05, 0.03, 0.02), 0.55); eye = mat("eye", (0.01, 0.01, 0.01), 0.05, coat=1.0); shine = mat("shine", (1, 1, 1), 0.2, emit=5)
for sx in (-1, 1):
    cube("shoe", (sx * 0.016, -0.004, 0.006), (0.022, 0.032, 0.014), shoe, parent=leo, bevel=0.005)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.008, depth=0.05, location=(sx * 0.016, 0, 0.036)); lg = bpy.context.object; lg.data.materials.append(skin); lg.parent = leo
cube("shorts", (0, 0, 0.065), (0.058, 0.04, 0.03), shorts, parent=leo, bevel=0.01)
sphere("torso", (0, 0, 0.1), 0.036, hood, parent=leo, scale=(1.05, 0.85, 1.15))
for sx in (-1, 1):
    a_ = sphere("arm", (sx * 0.04, 0, 0.098), 0.012, hood, parent=leo, scale=(1, 1, 2.4))
    a_.rotation_euler.y = sx * 0.25
head = empty("Head", (0, 0, 0.14), parent=leo)
sphere("face", (0, 0, 0.05), 0.05, skin, parent=head)
for i in range(16):
    an = i / 16 * 2 * math.pi; rr = 0.046
    sphere("curl", (math.cos(an) * rr * 0.9, math.sin(an) * rr * 0.75 + 0.012, 0.075 + 0.012 * math.sin(an * 3)), 0.02, hair, parent=head, seg=12)
for i in range(6):
    sphere("curl", (rnd.uniform(-0.03, 0.03), rnd.uniform(-0.01, 0.03), 0.095), 0.022, hair, parent=head, seg=12)
for sx in (-1, 1):
    e_ = sphere("eye", (sx * 0.018, -0.045, 0.05), 0.011, eye, parent=head, scale=(1, 0.6, 1.25))
    sphere("shine", (sx * 0.018 + 0.004, -0.052, 0.057), 0.003, shine, parent=head, seg=8)
    sphere("cheek", (sx * 0.03, -0.04, 0.035), 0.008, mat("cheek", (0.9, 0.35, 0.35), 0.6), parent=head, scale=(1, 0.4, 0.6), seg=12)
head.rotation_euler = (0, 0, 0); head.keyframe_insert("rotation_euler", frame=F(6.8))
head.rotation_euler = (math.radians(-22), 0, math.radians(-12)); head.keyframe_insert("rotation_euler", frame=F(8.0))
leo.rotation_euler.z = math.radians(-15); leo.keyframe_insert("rotation_euler", index=2, frame=F(6.6))
leo.rotation_euler.z = math.radians(-150); leo.keyframe_insert("rotation_euler", index=2, frame=F(7.6))
for f in range(1, NF + 1, 3):
    leo.location.z = 0.075 + 0.004 * abs(math.sin(f * 0.25)); leo.keyframe_insert("location", index=2, frame=f)

# ---------- lights: warm desk lamp + cool fill
lamp = bpy.data.lights.new("Lamp", "SPOT"); lamp.energy = 160; lamp.color = (1.0, 0.72, 0.42); lamp.spot_size = math.radians(70); lamp.spot_blend = 0.6; lamp.shadow_soft_size = 0.25
lo_ = bpy.data.objects.new("Lamp", lamp); col.objects.link(lo_); lo_.location = (-1.2, -0.9, 2.2)
tk = lo_.constraints.new("TRACK_TO"); tk.target = pop; tk.track_axis = "TRACK_NEGATIVE_Z"; tk.up_axis = "UP_Y"
fill = bpy.data.lights.new("Fill", "AREA"); fill.energy = 25; fill.color = (0.5, 0.6, 1.0); fill.size = 2
fo = bpy.data.objects.new("Fill", fill); col.objects.link(fo); fo.location = (1.8, -1.5, 1.5)
tk = fo.constraints.new("TRACK_TO"); tk.target = pop; tk.track_axis = "TRACK_NEGATIVE_Z"; tk.up_axis = "UP_Y"

# ---------- camera: closed cover -> dolly into the diorama
cd = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cd); col.objects.link(cam); sc.camera = cam
cd.lens = 30; cd.sensor_fit = "VERTICAL"; cd.sensor_height = 24
tgt = empty("Tgt")
c = cam.constraints.new("TRACK_TO"); c.target = tgt; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
cd.dof.use_dof = True; cd.dof.focus_object = tgt; cd.dof.aperture_fstop = 2.0
keys = [(0.0, (0.5, -1.15, 2.45), (0.5, 0.0, 0.1)), (3.0, (0.5, -1.0, 2.2), (0.5, 0.0, 0.1)),
        (5.6, (0.6, -1.6, 1.05), (0.5, 0.1, 0.44)), (13.5, (0.52, -1.38, 0.92), (0.5, 0.12, 0.46))]
for f in range(1, NF + 1, 2):
    t = (f - 1) / FPS
    for (t0, p0, g0), (t1, p1, g1) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            k = smooth((t - t0) / (t1 - t0)); break
    else: (t0, p0, g0), (t1, p1, g1), k = keys[-2], keys[-1], 1.0
    cam.location = [x + (y - x) * k for x, y in zip(p0, p1)]; cam.keyframe_insert("location", frame=f)
    tgt.location = [x + (y - x) * k for x, y in zip(g0, g1)]; tgt.keyframe_insert("location", frame=f)

sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 94
if STILL:
    sc.frame_set(STILL); sc.render.filepath = f"{OUT}/still_{STILL}.jpg"; bpy.ops.render.render(write_still=True)
else:
    sc.render.filepath = f"{OUT}/f_"; bpy.ops.render.render(animation=True)
