"""3D space shot: Earth (oceans, land, clouds, atmosphere), orbiting Moon, ocean tidal bulge that tracks the Moon.
python(bpy) space3d.py timing.json shot_index out_dir [--still F]
moon modes: on (orbiting), vanish (Moon shrinks away, bulge relaxes), off
"""
import bpy, json, math, sys, addon_utils
addon_utils.enable("cycles")
a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
T = json.load(open(a[0])); SH = T["shots"][int(a[1])]; OUT = a[2]
STILL = int(a[a.index("--still") + 1]) if "--still" in a else None
NF = SH["frames"]; MODE = SH.get("moon", "on")

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 10; sc.cycles.use_denoising = True
sc.cycles.max_bounces = 3; sc.render.use_persistent_data = True
sc.render.resolution_x, sc.render.resolution_y = 720, 1280; sc.render.fps = T["fps"]
sc.frame_start, sc.frame_end = 1, NF
sc.view_settings.view_transform = "AgX"

def node(nt, kind, **kw):
    n = nt.nodes.new(kind)
    for k, v in kw.items():
        if k in n.inputs: n.inputs[k].default_value = v
        else: setattr(n, k, v)
    return n

def link(nt, a, b): nt.links.new(a, b)

# ---------- world: stars + faint nebula
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True; nt = w.node_tree
bg = nt.nodes["Background"]
vor = node(nt, "ShaderNodeTexVoronoi", Scale=160.0)
mr = node(nt, "ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.0; mr.inputs["From Max"].default_value = 0.07
mr.inputs["To Min"].default_value = 1.0; mr.inputs["To Max"].default_value = 0.0
pw = node(nt, "ShaderNodeMath", operation="POWER"); pw.inputs[1].default_value = 6.0
nz = node(nt, "ShaderNodeTexNoise", Scale=1.5, Detail=6.0)
neb = node(nt, "ShaderNodeValToRGB"); e = neb.color_ramp.elements
e[0].position = 0.45; e[0].color = (0.002, 0.003, 0.012, 1); e[1].position = 0.8; e[1].color = (0.03, 0.012, 0.06, 1)
add = node(nt, "ShaderNodeMix", data_type="RGBA", blend_type="ADD"); add.inputs["Factor"].default_value = 1.0
link(nt, vor.outputs["Distance"], mr.inputs["Value"]); link(nt, mr.outputs["Result"], pw.inputs[0])
link(nt, nz.outputs["Fac"], neb.inputs["Fac"])
link(nt, neb.outputs["Color"], add.inputs[6]); link(nt, pw.outputs["Value"], add.inputs[7])
link(nt, add.outputs[2], bg.inputs["Color"]); bg.inputs["Strength"].default_value = 1.0

def sphere(name, r, loc=(0, 0, 0), seg=128):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=r, location=loc)
    o = bpy.context.object; o.name = name; bpy.ops.object.shade_smooth(); return o

def new_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; return m, m.node_tree, m.node_tree.nodes["Principled BSDF"]

# ---------- Earth
earth = sphere("Earth", 1.0)
m, nt, b = new_mat("earth")
tc = node(nt, "ShaderNodeTexCoord")
land = node(nt, "ShaderNodeTexNoise", Scale=2.2, Detail=10.0, Roughness=0.6)
link(nt, tc.outputs["Object"], land.inputs["Vector"])
mask = node(nt, "ShaderNodeValToRGB"); mask.color_ramp.elements[0].position = 0.53; mask.color_ramp.elements[1].position = 0.545
link(nt, land.outputs["Fac"], mask.inputs["Fac"])
lc = node(nt, "ShaderNodeValToRGB"); el = lc.color_ramp.elements
el[0].position = 0.5; el[0].color = (0.05, 0.16, 0.04, 1); el[1].position = 0.75; el[1].color = (0.32, 0.24, 0.1, 1)
link(nt, land.outputs["Fac"], lc.inputs["Fac"])
sep = node(nt, "ShaderNodeSeparateXYZ"); link(nt, tc.outputs["Object"], sep.inputs[0])
absz = node(nt, "ShaderNodeMath", operation="ABSOLUTE"); link(nt, sep.outputs["Z"], absz.inputs[0])
ice = node(nt, "ShaderNodeMath", operation="GREATER_THAN"); ice.inputs[1].default_value = 0.88; link(nt, absz.outputs[0], ice.inputs[0])
mixl = node(nt, "ShaderNodeMix", data_type="RGBA"); mixl.inputs[6].default_value = (0.015, 0.09, 0.32, 1)
link(nt, mask.outputs["Color"], mixl.inputs["Factor"]); link(nt, lc.outputs["Color"], mixl.inputs[7])
mixi = node(nt, "ShaderNodeMix", data_type="RGBA"); mixi.inputs[7].default_value = (0.9, 0.93, 0.97, 1)
link(nt, ice.outputs[0], mixi.inputs["Factor"]); link(nt, mixl.outputs[2], mixi.inputs[6])
link(nt, mixi.outputs[2], b.inputs["Base Color"])
rr = node(nt, "ShaderNodeMapRange"); rr.inputs["To Min"].default_value = 0.22; rr.inputs["To Max"].default_value = 0.85
link(nt, mask.outputs["Color"], rr.inputs["Value"]); link(nt, rr.outputs["Result"], b.inputs["Roughness"])
earth.data.materials.append(m)
# clouds
clouds = sphere("Clouds", 1.012); m, nt, b = new_mat("clouds")
cn = node(nt, "ShaderNodeTexNoise", Scale=4.0, Detail=12.0, Roughness=0.65)
cr = node(nt, "ShaderNodeValToRGB"); cr.color_ramp.elements[0].position = 0.52; cr.color_ramp.elements[1].position = 0.72
link(nt, cn.outputs["Fac"], cr.inputs["Fac"])
tr = node(nt, "ShaderNodeBsdfTransparent"); ms = node(nt, "ShaderNodeMixShader")
b.inputs["Base Color"].default_value = (1, 1, 1, 1); b.inputs["Roughness"].default_value = 0.9
link(nt, cr.outputs["Color"], ms.inputs["Fac"]); link(nt, tr.outputs[0], ms.inputs[1]); link(nt, b.outputs[0], ms.inputs[2])
link(nt, ms.outputs[0], nt.nodes["Material Output"].inputs["Surface"]); clouds.data.materials.append(m)
# atmosphere rim glow
atm = sphere("Atmo", 1.07); m, nt, b = new_mat("atmo")
lw = node(nt, "ShaderNodeLayerWeight", Blend=0.35)
ar = node(nt, "ShaderNodeValToRGB"); ar.color_ramp.elements[0].position = 0.25; ar.color_ramp.elements[0].color = (0, 0, 0, 1)
ar.color_ramp.elements[1].color = (1, 1, 1, 1)
emi = node(nt, "ShaderNodeEmission", Strength=2.2); emi.inputs["Color"].default_value = (0.25, 0.55, 1.0, 1)
tr = node(nt, "ShaderNodeBsdfTransparent"); ms = node(nt, "ShaderNodeMixShader")
link(nt, lw.outputs["Facing"], ar.inputs["Fac"]); link(nt, ar.outputs["Color"], ms.inputs["Fac"])
link(nt, tr.outputs[0], ms.inputs[1]); link(nt, emi.outputs[0], ms.inputs[2])
link(nt, ms.outputs[0], nt.nodes["Material Output"].inputs["Surface"]); atm.data.materials.append(m)

# ---------- orbit pivot (tilted so the orbit reads as a tall ellipse in a vertical frame)
pivot = bpy.data.objects.new("Pivot", None); bpy.context.collection.objects.link(pivot)
pivot.rotation_euler = (math.radians(90), math.radians(-12), 0)
spin = bpy.data.objects.new("Spin", None); bpy.context.collection.objects.link(spin); spin.parent = pivot
# tidal bulge: glowing translucent water ellipsoid aligned with the Moon (exaggerated for clarity)
bul = sphere("Bulge", 1.0); bul.parent = spin; bul.scale = (1.0, 0.98, 0.98)
m, nt, b = new_mat("bulge")
lw = node(nt, "ShaderNodeLayerWeight", Blend=0.5)
br = node(nt, "ShaderNodeValToRGB"); br.color_ramp.elements[0].position = 0.15; br.color_ramp.elements[0].color = (0.05, 0.05, 0.05, 1)
br.color_ramp.elements[1].position = 0.75; br.color_ramp.elements[1].color = (1, 1, 1, 1)
emi = node(nt, "ShaderNodeEmission", Strength=1.6); emi.inputs["Color"].default_value = (0.03, 0.3, 1.0, 1)
tr = node(nt, "ShaderNodeBsdfTransparent"); ms = node(nt, "ShaderNodeMixShader")
link(nt, lw.outputs["Facing"], br.inputs["Fac"]); link(nt, br.outputs["Color"], ms.inputs["Fac"])
link(nt, tr.outputs[0], ms.inputs[1]); link(nt, emi.outputs[0], ms.inputs[2])
link(nt, ms.outputs[0], nt.nodes["Material Output"].inputs["Surface"]); bul.data.materials.append(m)
moon = sphere("Moon", 0.27, loc=(2.35, 0, 0), seg=96); moon.parent = spin
m, nt, b = new_mat("moon")
mn = node(nt, "ShaderNodeTexNoise", Scale=6.0, Detail=10.0)
mc = node(nt, "ShaderNodeValToRGB"); mc.color_ramp.elements[0].color = (0.25, 0.25, 0.25, 1); mc.color_ramp.elements[1].color = (0.75, 0.74, 0.72, 1)
link(nt, mn.outputs["Fac"], mc.inputs["Fac"]); link(nt, mc.outputs["Color"], b.inputs["Base Color"])
vr = node(nt, "ShaderNodeTexVoronoi", Scale=9.0); bp = node(nt, "ShaderNodeBump", Strength=0.5)
link(nt, vr.outputs["Distance"], bp.inputs["Height"]); link(nt, bp.outputs["Normal"], b.inputs["Normal"])
b.inputs["Roughness"].default_value = 0.95; moon.data.materials.append(m)

# ---------- animation
start = SH.get("orbit_start", 0.55 if MODE != "vanish" else 1.35)
for f in range(1, NF + 1):
    k = (f - 1) / max(NF - 1, 1)
    spin.rotation_euler.z = start + 0.9 * k * (1 if MODE != "off" else 0)
    spin.keyframe_insert("rotation_euler", index=2, frame=f)
    earth.rotation_euler.z = clouds.rotation_euler.z = 0.6 * k
    earth.keyframe_insert("rotation_euler", index=2, frame=f); clouds.rotation_euler.z = 0.75 * k
    clouds.keyframe_insert("rotation_euler", index=2, frame=f)
    if MODE == "vanish":
        g = max(0.0, min(1.0, (k - 0.15) / 0.25)); s = (1 - g) ** 2
        moon.scale = (max(s, 0.001),) * 3; moon.keyframe_insert("scale", frame=f)
        rb = max(0.0, min(1.0, (k - 0.35) / 0.5)); rb = rb * rb * (3 - 2 * rb)
        bul.scale.x = 1.24 - 0.26 * rb; bul.keyframe_insert("scale", index=0, frame=f)
    elif MODE == "on":
        bul.scale.x = 1.24; bul.keyframe_insert("scale", index=0, frame=f)
    else:
        moon.scale = (0.001,) * 3; moon.keyframe_insert("scale", frame=f); bul.scale.x = 0.98; bul.keyframe_insert("scale", index=0, frame=f)

# ---------- light + camera
sun = bpy.data.lights.new("Sun", "SUN"); sun.energy = 5.5; sun.angle = math.radians(1.5)
so = bpy.data.objects.new("Sun", sun); bpy.context.collection.objects.link(so); so.rotation_euler = (math.radians(70), 0, math.radians(-55))
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); bpy.context.collection.objects.link(cam)
sc.camera = cam; cam_d.lens = 34; cam_d.sensor_fit = "VERTICAL"; cam_d.sensor_height = 24
tgt = bpy.data.objects.new("T", None); bpy.context.collection.objects.link(tgt)
c = cam.constraints.new("TRACK_TO"); c.target = tgt; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
cam.location = (0.4, -7.6, 0.9); cam.keyframe_insert("location", frame=1)
cam.location = (0.1, -6.7, 0.6); cam.keyframe_insert("location", frame=NF)

sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 94
if STILL:
    sc.frame_set(STILL); sc.render.filepath = f"{OUT}/still.jpg"; bpy.ops.render.render(write_still=True)
else:
    sc.render.filepath = f"{OUT}/f_"; bpy.ops.render.render(animation=True)
