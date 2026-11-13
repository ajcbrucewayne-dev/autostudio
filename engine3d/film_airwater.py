"""Film-look 3D test #2: Leo underwater in a flooded street, holding his breath (What if air turned into water?).
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
sc.cycles.max_bounces = 6; sc.cycles.volume_bounces = 1; sc.cycles.volume_step_rate = 6
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
leo = empty("Leo", (0, 0, 0.35)); leo.rotation_euler = (math.radians(6), 0, math.radians(-8))
for sx in (-1, 1):
    capsule((sx * 0.1, 0, 0.1), (sx * 0.095, 0, 0.52), 0.085, JEANS, leo)
    sph((sx * 0.09, -0.05, 0.055), 0.075, SHOE, leo, scale=(0.85, 1.5, 0.7)); sph((sx * 0.09, -0.05, 0.02), 0.078, SOLE, leo, scale=(0.9, 1.55, 0.3))
sph((0, 0, 0.74), 0.24, HOOD, leo, scale=(1.0, 0.78, 1.15))                     # hoodie body
capsule((0, 0, 0.98), (0, 0, 1.12), 0.075, SKIN, leo)                           # neck
bpy.ops.mesh.primitive_torus_add(major_radius=0.2, minor_radius=0.06, location=(0, 0, 0.56)); o = bpy.context.object; o.scale = (1.05, 0.8, 1); put(o, HOOD, leo)  # hoodie hem
sph((0, 0.06, 0.93), 0.17, HOOD, leo, scale=(1.25, 0.8, 0.45))                  # hood folded behind the neck
for sx in (-1, 1):                                                              # arms (one hand raised, pointing to the Moon)
    capsule((sx * 0.21, 0, 0.9), (sx * 0.4, -0.04, 1.0), 0.065, HOOD, leo); capsule((sx * 0.4, -0.04, 1.0), (sx * 0.55, -0.02, 1.2), 0.06, HOOD, leo)  # arms floating out
    sph((sx * 0.58, -0.02, 1.25), 0.058, SKIN, leo)
# scarf: wrapped ring + hanging tail that flutters
bpy.ops.mesh.primitive_torus_add(major_radius=0.13, minor_radius=0.055, location=(0, -0.01, 0.98)); put(bpy.context.object, SCARF, leo)
tail = capsule((0.12, -0.1, 0.96), (0.42, 0.02, 1.12), 0.045, SCARF, leo)   # scarf floats upward
head = empty("Head", (0, 0, 1.25), parent=leo); head.rotation_euler = (math.radians(-6), 0, math.radians(-6))
sph((0, 0, 0), 0.24, SKIN, head, scale=(1.0, 0.95, 1.05))
for sx in (-1, 1): sph((sx * 0.235, 0.02, -0.01), 0.055, SKIN, head, scale=(0.5, 0.9, 1.1))   # ears
sph((0, -0.235, -0.04), 0.04, SKIN, head, scale=(1, 0.8, 0.9))                                # nose
for sx in (-1, 1): sph((sx * 0.12, -0.15, -0.09), 0.095, SKIN, head); sph((sx * 0.13, -0.235, -0.08), 0.045, BLUSH, head, scale=(1, 0.35, 0.7))   # puffed cheeks
sph((0, -0.232, -0.14), 0.03, MOUTH, head, scale=(1.4, 0.4, 0.35))                            # pressed lips
look = Vector((0.0, -0.85, 0.5)).normalized()
for sx in (-1, 1):
    ec = Vector((sx * 0.085, -0.17, 0.03)); er = 0.062
    sph(ec, er, SCLERA, head)
    sph(ec + look * er * 0.86, er * 0.55, IRIS, head, scale=(1, 1, 1))
    sph(ec + look * er * 1.0, er * 0.28, PUPIL, head)
    sph(ec + look * er * 1.05 + Vector((-0.012, 0, 0.018)), er * 0.12, SHINE, head, seg=12)
    b = capsule((sx * 0.05, -0.215, 0.14), (sx * 0.125, -0.2, 0.115), 0.014, HAIR, head)     # raised brows (awe)
for i in range(110):                                                                           # curly hair
    th = rnd.uniform(0, 2 * math.pi); ph = rnd.uniform(0.0, 1.25)
    if math.sin(th) < -0.55 and ph > 0.55: continue                                            # keep the face clear
    d = Vector((math.cos(th) * math.sin(ph), math.sin(th) * math.sin(ph), math.cos(ph)))
    sph(d * 0.235 + Vector((0, 0.02, 0.06)) + Vector((0, 0, 0.04)) * d.z, rnd.uniform(0.055, 0.085), HAIR, head, seg=16)  # hair floats up

# ---------------- set: flooded street underwater
ASPH = mat("asphalt", (0.05, 0.06, 0.08), 0.9, bump=0.3, bscale=30); LINE = mat("lane", (0.9, 0.75, 0.2), 0.6)
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 10, 0)); put(bpy.context.object, ASPH, smooth=False)
for i in range(8):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(-6 + i * 2.2, 2.5, 0.01)); o = bpy.context.object; o.scale = (0.9, 0.12, 1); put(o, LINE, smooth=False)
WALLS = [mat(f"wall{i}", c_, 0.8, bump=0.2, bscale=8) for i, c_ in enumerate([(0.55, 0.35, 0.28), (0.35, 0.42, 0.55), (0.6, 0.55, 0.45)])]
WIN = mat("win", (1.0, 0.75, 0.4), 0.3, emit=3)
for i, (x, w, h) in enumerate([(-5.5, 3, 12), (-2.0, 3.2, 9), (1.6, 3.4, 14), (5.4, 3.2, 10)]):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 8, h / 2)); o = bpy.context.object; o.scale = (w, 2, h); put(o, WALLS[i % 3], smooth=False)
    for k in range(int(h / 1.6)):
        for j in range(int(w / 1.1)):
            if (i + j + k) % 3 == 0: continue
            bpy.ops.mesh.primitive_plane_add(size=1, location=(x - w / 2 + 0.6 + j * 1.05, 6.98, 1.0 + k * 1.6), rotation=(math.pi / 2, 0, 0))
            o = bpy.context.object; o.scale = (0.55, 0.8, 1); put(o, WIN, smooth=False)
# floating car + traffic cone
CARP = mat("carpaint", (0.75, 0.05, 0.04), 0.25, coat=1.0); GLASS = mat("carglass", (0.2, 0.35, 0.45), 0.05, coat=1.0); TYRE = mat("tyre", (0.02, 0.02, 0.02), 0.8)
car = empty("Car", (1.25, 3.2, 2.75)); car.rotation_euler = (math.radians(14), math.radians(-18), math.radians(-30))
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0)); o = bpy.context.object; o.scale = (1.9, 0.9, 0.45); put(o, CARP, car, smooth=False)
bpy.ops.object.modifier_add(type="BEVEL"); o.modifiers[-1].width = 0.12; o.modifiers[-1].segments = 4
bpy.ops.mesh.primitive_cube_add(size=1, location=(-0.1, 0, 0.4)); o = bpy.context.object; o.scale = (1.1, 0.85, 0.42); put(o, GLASS, car, smooth=False)
bpy.ops.object.modifier_add(type="BEVEL"); o.modifiers[-1].width = 0.12; o.modifiers[-1].segments = 4
for wx in (-0.6, 0.6):
    for wy in (-0.45, 0.45):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.22, depth=0.16, location=(wx, wy, -0.22), rotation=(math.pi / 2, 0, 0)); put(bpy.context.object, TYRE, car)
CONE = mat("cone", (1.0, 0.35, 0.02), 0.5)
bpy.ops.mesh.primitive_cone_add(radius1=0.18, radius2=0.03, depth=0.6, location=(-1.3, 1.2, 1.9), rotation=(math.radians(60), 0, math.radians(20))); put(bpy.context.object, CONE)
# bubbles (glassy spheres)
BUB = bpy.data.materials.new("bubble"); BUB.use_nodes = True; bb = BUB.node_tree.nodes["Principled BSDF"]
bb.inputs["Transmission Weight"].default_value = 1.0; bb.inputs["Roughness"].default_value = 0.0; bb.inputs["IOR"].default_value = 0.75
for i in range(90):
    x, y, z = rnd.uniform(-2.5, 3), rnd.uniform(-1.5, 4), rnd.uniform(0.2, 4.5)
    if abs(x) < 0.4 and abs(y) < 0.4 and 1.0 < z < 1.8: continue
    sph((x, y, (z + FRAME * 0.03) % 4.8), rnd.uniform(0.012, 0.05), BUB, seg=16)
for i in range(10):  # little stream from Leo's nose
    sph((0.02 + 0.01 * math.sin(i), -0.32, 1.65 + i * 0.12), 0.012 + 0.003 * i, BUB, seg=12)
# light from the surface: cool sun shafts through the water volume + a soft warm bounce
ml = bpy.data.lights.new("Surface", "SUN"); ml.energy = 4.5; ml.color = (0.75, 0.92, 1.0); ml.angle = math.radians(4)
mo = bpy.data.objects.new("Surface", ml); col.objects.link(mo); mo.rotation_euler = (math.radians(-20), math.radians(12), 0)
fl = bpy.data.lights.new("Fill", "AREA"); fl.energy = 60; fl.color = (1.0, 0.8, 0.6); fl.size = 3
fo = bpy.data.objects.new("Fill", fl); col.objects.link(fo); fo.location = (1.8, -3.0, 1.2); fo.rotation_euler = (math.radians(75), 0, math.radians(30))
rim = bpy.data.lights.new("Rim", "AREA"); rim.energy = 80; rim.color = (0.5, 0.85, 1.0); rim.size = 1.5
ro = bpy.data.objects.new("Rim", rim); col.objects.link(ro); ro.location = (-1.5, 1.8, 2.6); ro.rotation_euler = (math.radians(-50), math.radians(-30), 0)
world = bpy.data.worlds.new("Sea"); sc.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.02, 0.12, 0.22, 1); world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
# water volume: blue absorption + scattering = depth haze and light shafts
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 8, 7)); fog = bpy.context.object; fog.scale = (40, 40, 14.2)
fm = bpy.data.materials.new("water"); fm.use_nodes = True; fn = fm.node_tree.nodes; fn.remove(fn["Principled BSDF"])
pv = fn.new("ShaderNodeVolumePrincipled"); pv.inputs["Density"].default_value = 0.05; pv.inputs["Anisotropy"].default_value = 0.6
pv.inputs["Color"].default_value = (0.45, 0.8, 0.95, 1); pv.inputs["Absorption Color"].default_value = (0.25, 0.65, 0.85, 1)
fm.node_tree.links.new(pv.outputs[0], fn["Material Output"].inputs["Volume"]); fog.data.materials.append(fm)

cd = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cd); col.objects.link(cam); sc.camera = cam
cd.lens = 40; cd.dof.use_dof = True; cd.dof.aperture_fstop = 2.4
cam.location = (0.15 + 0.1 * math.sin(FRAME * 0.03), -3.6, 1.35 + 0.05 * math.sin(FRAME * 0.05))
tgt = empty("Tgt", (0.2, 2.0, 2.0)); tk = cam.constraints.new("TRACK_TO"); tk.target = tgt; tk.track_axis = "TRACK_NEGATIVE_Z"; tk.up_axis = "UP_Y"
foc = empty("Focus", (0.0, -0.25, 1.6)); cd.dof.focus_object = foc


# ---------------- CLAY LOOK (--clay): matte plasticine, thumbprint + tool-mark bumps, miniature tilt-shift lens
if "--clay" in sys.argv:
    for m in list(bpy.data.materials):
        if not m.use_nodes or "Principled BSDF" not in m.node_tree.nodes or m.name in ("bubble", "win", "shine", "flake"): continue
        nt = m.node_tree; b = nt.nodes["Principled BSDF"]
        b.inputs["Roughness"].default_value = 0.62; b.inputs["Coat Weight"].default_value = 0.0
        b.inputs["Subsurface Weight"].default_value = 0.25; b.inputs["Subsurface Scale"].default_value = 0.02
        c0 = b.inputs["Base Color"].default_value; b.inputs["Base Color"].default_value = (min(1, c0[0] * 1.15), min(1, c0[1] * 1.15), min(1, c0[2] * 1.15), 1)
        tc = nt.nodes.new("ShaderNodeTexCoord")
        wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = "RINGS"; wv.inputs["Scale"].default_value = 9; wv.inputs["Distortion"].default_value = 6; wv.inputs["Detail"].default_value = 3
        nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
        vn = nt.nodes.new("ShaderNodeTexNoise"); vn.inputs["Scale"].default_value = 3; vn.inputs["Detail"].default_value = 2
        nt.links.new(tc.outputs["Object"], vn.inputs["Vector"])
        mx = nt.nodes.new("ShaderNodeMath"); mx.operation = "MULTIPLY"; nt.links.new(wv.outputs["Fac"], mx.inputs[0]); nt.links.new(vn.outputs["Fac"], mx.inputs[1])
        bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.35; bp.inputs["Distance"].default_value = 0.02
        nt.links.new(mx.outputs[0], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    for o in bpy.data.objects:  # hand-made imperfection: slightly lumpy surfaces
        if o.type == "MESH" and o.name not in ("Cube",) and len(o.data.vertices) > 200 and "bubble" not in [ms.name for ms in o.data.materials]:
            d = o.modifiers.new("lumps", "DISPLACE"); tx = bpy.data.textures.new("lump" + o.name, "CLOUDS"); tx.noise_scale = 0.35; d.texture = tx; d.strength = 0.012
    cd.dof.aperture_fstop = 1.1                                   # very shallow focus = tabletop miniature
    pv.inputs["Density"].default_value = 0.03
sc.render.filepath = OUT; t0 = time.time()
bpy.ops.render.render(write_still=True)
print(f"RENDERED {OUT} in {time.time() - t0:.1f}s at {SAMPLES} samples")
