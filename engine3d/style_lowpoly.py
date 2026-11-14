"""Style test: low-poly faceted 3D — a fish chasing a glittering sea sapphire over a crystal-like seafloor.
/home/user/bpyenv/bin/python engine3d/style_lowpoly.py out.png [samples]
"""
import bpy, bmesh, math, random, sys, time, addon_utils
addon_utils.enable("cycles")
OUT = sys.argv[1]; SAMPLES = int(sys.argv[2]) if len(sys.argv) > 2 else 64
rnd = random.Random(4)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; col = bpy.context.collection
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 720, 1280
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"

def mat(name, color, rough=0.4, emit=0.0, metal=0.0, trans=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    if trans: b.inputs["Transmission Weight"].default_value = trans
    if emit: b.inputs["Emission Color"].default_value = (*color, 1); b.inputs["Emission Strength"].default_value = emit
    return m

def put(o, m):
    o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = False
    return o

def jitter(o, amt):
    bm = bmesh.new(); bm.from_mesh(o.data)
    for v in bm.verts: v.co.x += rnd.uniform(-amt, amt); v.co.y += rnd.uniform(-amt, amt); v.co.z += rnd.uniform(-amt, amt)
    bm.to_mesh(o.data); bm.free()

# seafloor: subdivided plane with random heights (faceted dunes)
bpy.ops.mesh.primitive_grid_add(x_subdivisions=28, y_subdivisions=28, size=30, location=(0, 8, -2.2)); fl = bpy.context.object
for v in fl.data.vertices: v.co.z += rnd.uniform(-0.25, 0.35) + 0.6 * math.sin(v.co.x * 0.4)
put(fl, mat("sand", (0.75, 0.62, 0.38), 0.8))
for i in range(14):  # faceted rocks + coral
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=rnd.uniform(0.3, 0.9), location=(rnd.uniform(-5, 5), rnd.uniform(1, 12), -2.0))
    o = bpy.context.object; jitter(o, 0.15); put(o, mat(f"rock{i}", rnd.choice([(0.35, 0.3, 0.4), (0.9, 0.35, 0.45), (0.95, 0.55, 0.2)]), 0.7))
for i in range(9):  # kelp: stacked twisted prisms
    x, y = rnd.choice([-3.2, -2.6, 2.8, 3.4]) + rnd.uniform(-0.4, 0.4), rnd.uniform(1, 8)
    for k in range(6):
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.18, radius2=0.12, depth=0.9, location=(x + 0.2 * math.sin(k), y, -1.8 + k * 0.85), rotation=(0, 0.15 * math.sin(k * 1.3), k * 0.6))
        put(bpy.context.object, mat(f"kelp{i}{k}", (0.15, 0.6 + 0.05 * k, 0.35), 0.6))
# the fish: faceted ellipsoid + tail + fins, mouth open
fish = bpy.data.objects.new("Fish", None); col.objects.link(fish); fish.location = (-0.9, 1.0, 0.2); fish.rotation_euler = (0, 0.05, math.radians(-25))
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0); b = bpy.context.object; b.scale = (1.6, 0.75, 1.0); b.parent = fish; put(b, mat("fishbody", (1.0, 0.35, 0.08), 0.45))
bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.9, depth=1.2, location=(-1.9, 0, 0), rotation=(0, math.radians(-90), 0)); t = bpy.context.object; t.scale = (0.3, 1, 1); t.parent = fish; put(t, mat("tail", (0.95, 0.25, 0.05), 0.5))
for sx in (-1, 1):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.22, location=(1.05, sx * 0.55, 0.35)); e = bpy.context.object; e.parent = fish; put(e, mat("eyew", (1, 1, 1), 0.2))
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.11, location=(1.2, sx * 0.68, 0.38)); e = bpy.context.object; e.parent = fish; put(e, mat("pupil", (0.01, 0.01, 0.01), 0.1))
bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=0.5, depth=0.8, location=(0, 0, 1.0)); f = bpy.context.object; f.parent = fish; put(f, mat("fin", (1.0, 0.55, 0.1), 0.5))
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.35, location=(1.55, 0, -0.15)); m_ = bpy.context.object; m_.scale = (0.5, 1, 0.8); m_.parent = fish; put(m_, mat("mouth", (0.2, 0.02, 0.03), 0.6))
# the sea sapphire: a flat faceted gem with rainbow emissive facets
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.45, location=(1.7, -0.2, 1.4)); g = bpy.context.object; g.scale = (1, 0.35, 1.4); g.rotation_euler = (0.3, 0.6, 0.2)
GEMS = [mat(f"gem{i}", c_, 0.05, emit=6, metal=0.3) for i, c_ in enumerate([(0.2, 0.55, 1), (0.6, 0.35, 1), (1, 0.8, 0.2), (0.2, 1, 0.8)])]
for m in GEMS: g.data.materials.append(m)
for p in g.data.polygons: p.material_index = rnd.randrange(4); p.use_smooth = False
lt = bpy.data.lights.new("GemLight", "POINT"); lt.energy = 60; lt.color = (0.6, 0.7, 1); lo = bpy.data.objects.new("GemLight", lt); col.objects.link(lo); lo.location = (1.7, -0.6, 1.4)
for i in range(40):  # bubbles
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=rnd.uniform(0.03, 0.09), location=(rnd.uniform(-2, 3), rnd.uniform(-1, 3), rnd.uniform(-1, 3.5)))
    put(bpy.context.object, mat(f"bub{i}", (0.85, 0.95, 1), 0.05, trans=1.0))
# light from the surface + blue water volume
sun = bpy.data.lights.new("Sun", "SUN"); sun.energy = 5; sun.color = (0.8, 0.95, 1); so = bpy.data.objects.new("Sun", sun); col.objects.link(so); so.rotation_euler = (math.radians(-15), math.radians(20), 0)
w = bpy.data.worlds.new("Sea"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.02, 0.15, 0.3, 1)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 8, 3)); fog = bpy.context.object; fog.scale = (40, 40, 14)
fm = bpy.data.materials.new("water"); fm.use_nodes = True; fn = fm.node_tree.nodes; fn.remove(fn["Principled BSDF"])
pv = fn.new("ShaderNodeVolumePrincipled"); pv.inputs["Density"].default_value = 0.045; pv.inputs["Anisotropy"].default_value = 0.6; pv.inputs["Color"].default_value = (0.4, 0.8, 1, 1)
fm.node_tree.links.new(pv.outputs[0], fn["Material Output"].inputs["Volume"]); fog.data.materials.append(fm)
cd = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cd); col.objects.link(cam); sc.camera = cam
cd.lens = 32; cd.dof.use_dof = True; cd.dof.aperture_fstop = 2.8
cam.location = (0.6, -5.5, 0.6); tgt = bpy.data.objects.new("T", None); col.objects.link(tgt); tgt.location = (0.4, 1.5, 0.9)
tk = cam.constraints.new("TRACK_TO"); tk.target = tgt; tk.track_axis = "TRACK_NEGATIVE_Z"; tk.up_axis = "UP_Y"; cd.dof.focus_object = fish
sc.render.filepath = OUT; t0 = time.time(); bpy.ops.render.render(write_still=True); print(f"RENDERED {OUT} in {time.time() - t0:.1f}s")
