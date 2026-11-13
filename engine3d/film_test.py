"""Film-look 3D test: warm, soft, cinematic 3D (feature-animation feel, original designs).
Leo stands on a snowy rooftop at night, a red scarf in the breeze, looking up in awe at a huge rising Moon;
warm window glow behind him, cool moonlight rim, falling snow, haze and shallow depth of field.

/home/user/bpyenv/bin/python engine3d/film_test.py out.png [samples] [frame]
"""
import bpy, math, random, sys, time, addon_utils
from mathutils import Vector
addon_utils.enable("cycles")
OUT = sys.argv[1]; SAMPLES = int(sys.argv[2]) if len(sys.argv) > 2 else 96; FRAME = int(sys.argv[3]) if len(sys.argv) > 3 else 1
rnd = random.Random(3)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; col = bpy.context.collection
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = True
sc.cycles.max_bounces = 6; sc.cycles.volume_bounces = 1; sc.cycles.volume_step_rate = 4
sc.render.resolution_x, sc.render.resolution_y = 720, 1280; sc.render.fps = 24
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
sc.frame_set(FRAME)

def mat(name, color, rough=0.5, emit=0.0, sss=0.0, coat=0.0, sheen=0.0, bump=0.0, bscale=40.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rough
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss; b.inputs["Subsurface Radius"].default_value = (0.9, 0.35, 0.2); b.inputs["Subsurface Scale"].default_value = 0.04
    if coat: b.inputs["Coat Weight"].default_value = coat
    if sheen: b.inputs["Sheen Weight"].default_value = sheen
    if emit: b.inputs["Emission Color"].default_value = (*color, 1); b.inputs["Emission Strength"].default_value = emit
    if bump:
        nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = bscale; nz.inputs["Detail"].default_value = 10
        bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump
        nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m

def put(o, m, parent=None, smooth=True):
    o.data.materials.append(m)
    if smooth: bpy.ops.object.shade_smooth()
    if parent: o.parent = parent
    return o

def sph(loc, r, m, parent=None, scale=(1, 1, 1), seg=48):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=seg, ring_count=seg // 2); o = bpy.context.object; o.scale = scale
    return put(o, m, parent)

def capsule(p0, p1, r, m, parent=None):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d.length, location=(p0 + p1) / 2, vertices=32)
    o = bpy.context.object; o.rotation_euler = d.to_track_quat("Z", "Y").to_euler(); put(o, m, parent)
    sph(p0, r, m, parent, seg=24); sph(p1, r, m, parent, seg=24)
    return o

def empty(name, loc=(0, 0, 0), parent=None):
    e = bpy.data.objects.new(name, None); col.objects.link(e); e.location = loc
    if parent: e.parent = parent
    return e

# ---------------- materials
SKIN = mat("skin", (0.42, 0.24, 0.14), 0.45, sss=0.35)
HOOD = mat("hoodie", (0.95, 0.62, 0.08), 0.75, sheen=0.6, bump=0.15, bscale=120)
JEANS = mat("jeans", (0.12, 0.2, 0.42), 0.85, sheen=0.3, bump=0.2, bscale=150)
SCARF = mat("scarf", (0.75, 0.06, 0.06), 0.9, sheen=0.8, bump=0.5, bscale=60)
SHOE = mat("shoe", (0.8, 0.12, 0.08), 0.4, coat=0.4); SOLE = mat("sole", (0.95, 0.93, 0.9), 0.5)
HAIR = mat("hair", (0.04, 0.025, 0.015), 0.5, sheen=0.5, bump=0.4, bscale=80)
SCLERA = mat("sclera", (0.92, 0.9, 0.88), 0.15, coat=1.0); IRIS = mat("iris", (0.28, 0.14, 0.05), 0.2, coat=1.0)
PUPIL = mat("pupil", (0.005, 0.005, 0.005), 0.05, coat=1.0); SHINE = mat("shine", (1, 1, 1), 0.1, emit=8)
MOUTH = mat("mouth", (0.18, 0.03, 0.03), 0.5); BLUSH = mat("blush", (0.75, 0.25, 0.22), 0.6, sss=0.3)
SNOW = mat("snow", (0.85, 0.88, 0.95), 0.6, sss=0.2, bump=0.25, bscale=25)
BRICK = mat("brick", (0.25, 0.1, 0.07), 0.85, bump=0.3, bscale=12); ROOF = mat("roof", (0.08, 0.07, 0.09), 0.7)
WINDOW = mat("window", (1.0, 0.55, 0.2), 0.5, emit=5)

# ---------------- Leo (original character): curly hair, brown skin, mustard hoodie, red scarf
leo = empty("Leo", (0, 0, 0)); leo.rotation_euler.z = math.radians(-12)
for sx in (-1, 1):
    capsule((sx * 0.1, 0, 0.1), (sx * 0.095, 0, 0.52), 0.085, JEANS, leo)
    sph((sx * 0.09, -0.05, 0.055), 0.075, SHOE, leo, scale=(0.85, 1.5, 0.7)); sph((sx * 0.09, -0.05, 0.02), 0.078, SOLE, leo, scale=(0.9, 1.55, 0.3))
sph((0, 0, 0.74), 0.24, HOOD, leo, scale=(1.0, 0.78, 1.15))                     # hoodie body
capsule((0, 0, 0.98), (0, 0, 1.12), 0.075, SKIN, leo)                           # neck
bpy.ops.mesh.primitive_torus_add(major_radius=0.2, minor_radius=0.06, location=(0, 0, 0.56)); o = bpy.context.object; o.scale = (1.05, 0.8, 1); put(o, HOOD, leo)  # hoodie hem
sph((0, 0.06, 0.93), 0.17, HOOD, leo, scale=(1.25, 0.8, 0.45))                  # hood folded behind the neck
for sx in (-1, 1):                                                              # arms (one hand raised, pointing to the Moon)
    if sx < 0: capsule((-0.21, 0, 0.9), (-0.25, -0.03, 0.6), 0.065, HOOD, leo); sph((-0.25, -0.03, 0.55), 0.06, SKIN, leo)
    else:
        capsule((0.21, 0, 0.9), (0.36, -0.05, 1.1), 0.065, HOOD, leo); capsule((0.36, -0.05, 1.1), (0.45, 0.05, 1.33), 0.06, HOOD, leo)
        sph((0.47, 0.07, 1.38), 0.058, SKIN, leo)
# scarf: wrapped ring + hanging tail that flutters
bpy.ops.mesh.primitive_torus_add(major_radius=0.13, minor_radius=0.055, location=(0, -0.01, 0.98)); put(bpy.context.object, SCARF, leo)
tail = capsule((0.06, -0.12, 0.96), (0.14, -0.2, 0.7), 0.045, SCARF, leo)
head = empty("Head", (0, 0, 1.25), parent=leo); head.rotation_euler = (math.radians(-18), 0, math.radians(22))
sph((0, 0, 0), 0.24, SKIN, head, scale=(1.0, 0.95, 1.05))
for sx in (-1, 1): sph((sx * 0.235, 0.02, -0.01), 0.055, SKIN, head, scale=(0.5, 0.9, 1.1))   # ears
sph((0, -0.235, -0.04), 0.04, SKIN, head, scale=(1, 0.8, 0.9))                                # nose
for sx in (-1, 1): sph((sx * 0.13, -0.19, -0.07), 0.04, BLUSH, head, scale=(1, 0.4, 0.6))
sph((0, -0.215, -0.13), 0.035, MOUTH, head, scale=(1.0, 0.45, 1.25))                          # small "o" of wonder
look = Vector((0.25, -0.75, 0.62)).normalized()
for sx in (-1, 1):
    ec = Vector((sx * 0.085, -0.17, 0.03)); er = 0.062
    sph(ec, er, SCLERA, head)
    sph(ec + look * er * 0.86, er * 0.55, IRIS, head, scale=(1, 1, 1))
    sph(ec + look * er * 1.0, er * 0.28, PUPIL, head)
    sph(ec + look * er * 1.05 + Vector((-0.012, 0, 0.018)), er * 0.12, SHINE, head, seg=12)
    b = capsule((sx * 0.05, -0.215, 0.115), (sx * 0.125, -0.2, 0.135), 0.014, HAIR, head)     # raised brows (awe)
for i in range(110):                                                                           # curly hair
    th = rnd.uniform(0, 2 * math.pi); ph = rnd.uniform(0.0, 1.25)
    if math.sin(th) < -0.55 and ph > 0.55: continue                                            # keep the face clear
    d = Vector((math.cos(th) * math.sin(ph), math.sin(th) * math.sin(ph), math.cos(ph)))
    sph(d * 0.235 + Vector((0, 0.02, 0.03)), rnd.uniform(0.055, 0.085), HAIR, head, seg=16)

# ---------------- set: snowy rooftop, chimney with a warm window, distant town lights, huge Moon
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 3, -0.15)); o = bpy.context.object; o.scale = (14, 10, 0.3); put(o, SNOW, smooth=False)
bpy.ops.mesh.primitive_cube_add(size=1, location=(-1.6, 1.6, 1.0)); o = bpy.context.object; o.scale = (1.0, 0.9, 2.0); put(o, BRICK, smooth=False)
bpy.ops.mesh.primitive_plane_add(size=1, location=(-1.08, 1.4, 1.1), rotation=(math.pi / 2, 0, math.pi / 2)); o = bpy.context.object; o.scale = (0.6, 0.8, 1); put(o, WINDOW, smooth=False)
wl = bpy.data.lights.new("WindowGlow", "AREA"); wl.energy = 150; wl.color = (1.0, 0.55, 0.22); wl.size = 1.2
wo = bpy.data.objects.new("WindowGlow", wl); col.objects.link(wo); wo.location = (-0.9, 1.3, 1.2); wo.rotation_euler = (0, math.radians(-75), 0)
sph((-1.6, 1.6, 2.05), 0.55, SNOW, scale=(1.9, 1.7, 0.3))                                      # snow cap
for i in range(140):                                                                           # distant town lights -> bokeh
    x = rnd.uniform(-30, 30); y = rnd.uniform(22, 60); z = rnd.uniform(-2.2, 0.2) + (y - 22) * 0.05
    c_ = rnd.choice([(1.0, 0.6, 0.25), (1.0, 0.75, 0.4), (0.6, 0.75, 1.0)])
    sph((x, y, z), rnd.uniform(0.08, 0.2), mat(f"l{i}", c_, 0.5, emit=rnd.uniform(15, 40)), seg=8)
MOON = mat("moon", (0.85, 0.85, 0.82), 0.9, emit=1.4, bump=0.6, bscale=6)
mn = MOON.node_tree; mz = mn.nodes.new("ShaderNodeTexNoise"); mz.inputs["Scale"].default_value = 2.2; mz.inputs["Detail"].default_value = 6
mr = mn.nodes.new("ShaderNodeValToRGB"); mr.color_ramp.elements[0].position = 0.45; mr.color_ramp.elements[0].color = (0.45, 0.47, 0.52, 1)
mr.color_ramp.elements[1].position = 0.6; mr.color_ramp.elements[1].color = (0.92, 0.91, 0.86, 1); mn.links.new(mz.outputs["Fac"], mr.inputs["Fac"])
pb = mn.nodes["Principled BSDF"]; mn.links.new(mr.outputs["Color"], pb.inputs["Base Color"]); mn.links.new(mr.outputs["Color"], pb.inputs["Emission Color"])
sph((9, 70, 24), 9.0, MOON)
ml = bpy.data.lights.new("Moonlight", "SUN"); ml.energy = 2.2; ml.color = (0.65, 0.78, 1.0); ml.angle = math.radians(2)
mo = bpy.data.objects.new("Moonlight", ml); col.objects.link(mo); mo.rotation_euler = (math.radians(-75), math.radians(-8), math.radians(-10))
fl = bpy.data.lights.new("Fill", "AREA"); fl.energy = 18; fl.color = (0.55, 0.65, 1.0); fl.size = 3
fo = bpy.data.objects.new("Fill", fl); col.objects.link(fo); fo.location = (2.2, -3.0, 1.6); fo.rotation_euler = (math.radians(70), 0, math.radians(35))

# falling snow (some flakes close to the lens -> soft bokeh)
FLAKE = mat("flake", (0.9, 0.95, 1.0), 0.3, emit=1.5)
for i in range(260):
    x, y, z = rnd.uniform(-3, 4), rnd.uniform(-2.2, 8), rnd.uniform(0.1, 4.5)
    zz = (z - FRAME * 0.02 * rnd.uniform(0.6, 1.2)) % 4.6
    sph((x + 0.1 * math.sin(FRAME * 0.05 + i), y, zz), rnd.uniform(0.008, 0.022), FLAKE, seg=8)

# night sky with stars + gentle haze
world = bpy.data.worlds.new("Night"); sc.world = world; world.use_nodes = True; nt = world.node_tree; N = nt.nodes; L = nt.links.new
bg = N["Background"]; bg.inputs["Strength"].default_value = 1.0
tc = N.new("ShaderNodeTexCoord"); grad = N.new("ShaderNodeSeparateXYZ"); L(tc.outputs["Generated"], grad.inputs[0])
ramp = N.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].color = (0.035, 0.05, 0.12, 1); ramp.color_ramp.elements[1].color = (0.004, 0.006, 0.02, 1)
L(grad.outputs["Z"], ramp.inputs["Fac"])
vor = N.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 420; L(tc.outputs["Generated"], vor.inputs["Vector"])
st = N.new("ShaderNodeMath"); st.operation = "LESS_THAN"; st.inputs[1].default_value = 0.06; L(vor.outputs["Distance"], st.inputs[0])
add = N.new("ShaderNodeMixRGB"); add.blend_type = "ADD"; add.inputs["Color2"].default_value = (1.5, 1.5, 1.6, 1)
L(st.outputs[0], add.inputs["Fac"]); L(ramp.outputs["Color"], add.inputs["Color1"]); L(add.outputs["Color"], bg.inputs["Color"])
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 10, 5)); fog = bpy.context.object; fog.scale = (30, 30, 12)
fm = bpy.data.materials.new("haze"); fm.use_nodes = True; fn = fm.node_tree.nodes; fn.remove(fn["Principled BSDF"])
pv = fn.new("ShaderNodeVolumePrincipled"); pv.inputs["Density"].default_value = 0.004; pv.inputs["Anisotropy"].default_value = 0.5
pv.inputs["Color"].default_value = (0.8, 0.85, 1.0, 1); fm.node_tree.links.new(pv.outputs[0], fn["Material Output"].inputs["Volume"]); fog.data.materials.append(fm)

# camera: low angle, 3/4 front, shallow depth of field focused on Leo's eyes
cd = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cd); col.objects.link(cam); sc.camera = cam
cd.lens = 42; cd.dof.use_dof = True; cd.dof.aperture_fstop = 2.2
cam.location = (0.75 - FRAME * 0.002, -3.0 + FRAME * 0.004, 0.8)
tgt = empty("Tgt", (0.05, 1.5, 1.65)); tk = cam.constraints.new("TRACK_TO"); tk.target = tgt; tk.track_axis = "TRACK_NEGATIVE_Z"; tk.up_axis = "UP_Y"
foc = empty("Focus", (0.0, -0.2, 1.25)); cd.dof.focus_object = foc

sc.render.filepath = OUT; t0 = time.time()
bpy.ops.render.render(write_still=True)
print(f"RENDERED {OUT} in {time.time() - t0:.1f}s at {SAMPLES} samples")
