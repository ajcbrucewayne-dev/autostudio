"""Holographic storybook: Leo opens a book and the story projects out of it as a sci-fi hologram.
Each page flip swaps the projection. One continuous timeline across all shots (beats).
python(bpy) holo3d.py timing.json shot_index out_dir [--still GLOBAL_FRAME]
beats: intro, earth, beach, vanish, after, life, tilt, end
"""
import bpy, json, math, random, sys, addon_utils
addon_utils.enable("cycles")
a = sys.argv[1:]
T = json.load(open(a[0])); SI = int(a[1]); OUT = a[2]
STILL = int(a[a.index("--still") + 1]) if "--still" in a else None
FPS = T["fps"]; SH = [s_ for s_ in T["shots"] if s_["beat"] not in ("cold", "rewind")]; OFF = SH[0]["t0"]
G = [0]
for s_ in SH: G.append(G[-1] + s_["frames"])
NF = G[-1]; END = NF / FPS
B = {s_["beat"]: (G[i] / FPS, G[i + 1] / FPS) for i, s_ in enumerate(SH)}
F = lambda t: int(round(t * FPS)) + 1
def word_t(beat, w):
    for x in SH[[s_["beat"] for s_ in SH].index(beat)]["words"]:
        if x[0].lower().strip(".,?!'").startswith(w): return x[1] - OFF
    return B[beat][0] + 1
ROOT = "/home/user/autostudio"
rnd = random.Random(7)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 10; sc.cycles.use_denoising = True
sc.cycles.max_bounces = 4; sc.cycles.transparent_max_bounces = 48; sc.render.use_persistent_data = True
sc.render.resolution_x, sc.render.resolution_y = 720, 1280; sc.render.fps = FPS
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
col = bpy.context.collection

def smooth(k): k = max(0.0, min(1.0, k)); return k * k * (3 - 2 * k)

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

# ---------------- hologram material: emissive + transparent, fresnel edges, scanlines, rising "build" line
PAGES = {}; SWEEPS = []
def holo_mat(group, color, strength=3.0, base=0.15, edge=0.8, scan=True, pattern=None, sweep=True):
    m = bpy.data.materials.new(group); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links.new
    for n in list(N): N.remove(n)
    def M(op, *ins, clamp=False):
        n = N.new("ShaderNodeMath"); n.operation = op; n.use_clamp = clamp
        for i, v in enumerate(ins):
            if isinstance(v, (int, float)): n.inputs[i].default_value = v
            else: L(v, n.inputs[i])
        return n.outputs[0]
    out = N.new("ShaderNodeOutputMaterial"); geo = N.new("ShaderNodeNewGeometry"); sep = N.new("ShaderNodeSeparateXYZ")
    L(geo.outputs["Position"], sep.inputs[0]); z = sep.outputs["Z"]
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
    al = M("MULTIPLY_ADD", lw.outputs["Facing"], edge, base)
    if scan: al = M("MULTIPLY", al, M("MULTIPLY_ADD", M("SINE", M("MULTIPLY", z, 520)), 0.3, 0.75))
    if pattern: al = M("MULTIPLY", al, pattern(N, L, z))
    mult = N.new("ShaderNodeValue"); mult.outputs[0].default_value = 0.0
    rev = N.new("ShaderNodeValue"); rev.outputs[0].default_value = 10.0
    sw = N.new("ShaderNodeValue"); sw.name = "Sweep"; SWEEPS.append(sw)
    band = M("MULTIPLY", M("COMPARE", M("FRACT", M("SUBTRACT", M("MULTIPLY", z, 1.3), sw.outputs[0])), 0.5, 0.008), 1.0 if sweep else 0.0)
    al = M("MULTIPLY_ADD", band, 0.15, al)
    al = M("MULTIPLY", M("MULTIPLY", al, mult.outputs[0]), M("LESS_THAN", z, rev.outputs[0]), clamp=True)
    line = M("ADD", M("COMPARE", z, rev.outputs[0], 0.007), M("MULTIPLY", band, 0.4))
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*color, 1)
    L(M("MULTIPLY", M("MULTIPLY_ADD", line, 7.0, 1.0), strength * 0.45), em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
    L(al, mx.inputs[0]); L(tr.outputs[0], mx.inputs[1]); L(em.outputs[0], mx.inputs[2]); L(mx.outputs[0], out.inputs["Surface"])
    PAGES.setdefault(group, []).append((mult, rev))
    return m

SANS = f"{ROOT}/fonts/Inter-ExtraBold.otf"; SERIF = f"{ROOT}/fonts/DejaVuSerif-Bold.ttf"
CYAN = (0.08, 0.55, 1.0); CYAN2 = (0.25, 0.82, 1.0); SANDC = (1.0, 0.72, 0.32); RED = (1.0, 0.36, 0.18); RED2 = (1.0, 0.55, 0.3)
GREEN = (0.15, 1.0, 0.25); WATER = (0.1, 0.42, 1.0); WATER2 = (0.35, 0.72, 1.0); LANDO = (1.0, 0.5, 0.18)
PINK = (1.0, 0.3, 0.62); CRABC = (1.0, 0.38, 0.1); ROCK = (0.85, 0.72, 0.5); YEL = (1.0, 0.85, 0.35); WHITE = (0.85, 0.9, 1.0)
import bmesh
from mathutils import Vector

def MN(N, L, op, *ins, clamp=False):
    n = N.new("ShaderNodeMath"); n.operation = op; n.use_clamp = clamp
    for i, v in enumerate(ins):
        if isinstance(v, (int, float)): n.inputs[i].default_value = v
        else: L(v, n.inputs[i])
    return n.outputs[0]

def land_pattern(ocean=0.0, land=1.7):  # noise continents; ocean/land = alpha multipliers
    def f(N, L, z):
        tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 2.4; nz.inputs["Detail"].default_value = 6
        L(tc.outputs["Object"], nz.inputs["Vector"]); cr = N.new("ShaderNodeValToRGB"); e = cr.color_ramp.elements
        e[0].position, e[1].position = 0.5, 0.54; e[0].color = (ocean,) * 3 + (1,); e[1].color = (land,) * 3 + (1,)
        L(nz.outputs["Fac"], cr.inputs["Fac"]); return cr.outputs["Color"]
    return f

RIPPLES = []
def ripple_pattern(N, L, z):  # moving water rings
    tc = N.new("ShaderNodeTexCoord"); wv = N.new("ShaderNodeTexWave"); wv.wave_type = "RINGS"
    wv.inputs["Scale"].default_value = 7; wv.inputs["Distortion"].default_value = 2.0; wv.inputs["Detail"].default_value = 1
    L(tc.outputs["Object"], wv.inputs["Vector"]); RIPPLES.append(wv)
    cr = N.new("ShaderNodeValToRGB"); e = cr.color_ramp.elements; e[0].position, e[1].position = 0.3, 0.9
    e[0].color = (0.35, 0.35, 0.35, 1); e[1].color = (1.6, 1.6, 1.6, 1); L(wv.outputs["Fac"], cr.inputs["Fac"]); return cr.outputs["Color"]

def crater_pattern(N, L, z):
    tc = N.new("ShaderNodeTexCoord"); v = N.new("ShaderNodeTexVoronoi"); v.inputs["Scale"].default_value = 9
    L(tc.outputs["Object"], v.inputs["Vector"]); cr = N.new("ShaderNodeValToRGB"); e = cr.color_ramp.elements
    e[0].position, e[1].position = 0.15, 0.4; e[0].color = (0.35, 0.35, 0.35, 1); e[1].color = (1.1, 1.1, 1.1, 1)
    L(v.outputs["Distance"], cr.inputs["Fac"]); return cr.outputs["Color"]

def beam_pattern(N, L, z):
    n = N.new("ShaderNodeMath"); n.operation = "MULTIPLY_ADD"; n.use_clamp = True
    L(z, n.inputs[0]); n.inputs[1].default_value = -0.85; n.inputs[2].default_value = 1.1; return n.outputs[0]

def key_sock(sock, f, v): sock.default_value = v; sock.keyframe_insert("default_value", frame=f)
def fade(group, keys):
    for mult, _ in PAGES[group]:
        for t, v in keys: key_sock(mult.outputs[0], F(t), v)
def reveal(group, keys):
    for _, rev in PAGES[group]:
        for t, v in keys: key_sock(rev.outputs[0], F(t), v)
def flicker_in(group, t, z0, z1, dur=1.1):  # materialise bottom-to-top with a flicker
    fade(group, [(0, 0.0), (t, 0.0), (t + 0.08, 0.7), (t + 0.16, 0.25), (t + 0.26, 1.0)])
    reveal(group, [(0, z0 - 0.05), (t, z0 - 0.05), (t + dur, z1 + 0.05)])
def fade_out(group, t, d=0.35, base=1.0): fade(group, [(t, base), (t + d * 0.4, 0.5 * base), (t + d * 0.6, 0.9 * base), (t + d, 0.0)])
def glitch_out(group, t, base=1.0):  # flicker hard then gone
    fl = []; k = t - 0.7
    while k < t + 0.1: fl.append((k, rnd.choice((0.15, 1.3, 0.5, 1.0, 0.0, 1.4)) * base)); k += 2 / FPS
    fade(group, fl + [(t + 0.2, 0.0)])

# ---------------- object helpers
def empty(name, loc=(0, 0, 0), parent=None):
    e = bpy.data.objects.new(name, None); col.objects.link(e); e.location = loc
    if parent: e.parent = parent
    return e

def finish(o, m, parent, holo):
    if m is not None: o.data.materials.append(m)
    if parent: o.parent = parent
    if holo: o.visible_shadow = False
    return o

def cube(name, loc, size, m, parent=None, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel: md = o.modifiers.new("b", "BEVEL"); md.width = bevel; md.segments = 3
    return finish(o, m, parent, False)

def sphere(name, loc, r, m, parent=None, scale=(1, 1, 1), seg=32, holo=False):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=r, location=loc); o = bpy.context.object
    o.name = name; o.scale = scale; bpy.ops.object.shade_smooth(); return finish(o, m, parent, holo)

def rod(name, p0, p1, r, m, parent=None, verts=8):  # cylinder from p0 to p1 (parent-local coords)
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d.length, location=(p0 + p1) / 2)
    o = bpy.context.object; o.name = name; o.rotation_euler = d.to_track_quat("Z", "Y").to_euler(); return finish(o, m, parent, True)

def wire(o, m, thick):
    md = o.modifiers.new("w", "WIREFRAME"); md.thickness = thick; md.use_even_offset = True
    if m is None: md.use_replace = True
    else: md.use_replace = False; o.data.materials.append(m); md.material_offset = 1
    return o

def torus(name, loc, R, r, m, parent=None, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=128, minor_segments=8, location=loc, rotation=rot)
    return finish(bpy.context.object, m, parent, True)

def text(body, size, loc, m, parent=None, rot=(math.pi / 2, 0, 0), font=None, extrude=0.004, holo=True):
    bpy.ops.object.text_add(location=(0, 0, 0)); o = bpy.context.object; o.data.body = body; o.data.size = size
    o.data.align_x = "CENTER"; o.data.align_y = "CENTER"; o.data.extrude = extrude
    if font: o.data.font = bpy.data.fonts.load(font)
    o.data.materials.append(m); o.parent = parent; o.location = loc; o.rotation_euler = rot
    if holo: o.visible_shadow = False
    return o

def fcurves_of(id_):
    ad = id_.animation_data
    if not ad or not ad.action: return []
    from bpy_extras import anim_utils
    cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
    return list(cb.fcurves) if cb else []
def lin(obj, only=None):
    for fc in fcurves_of(obj):
        if only and only not in fc.data_path: continue
        for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
def loop_keys(o, idx, v0, v1, t_from, t_to, P, prop="location"):  # repeat a v0->v1 linear move every P seconds
    t = t_from
    while t < t_to:
        getattr(o, prop)[idx] = v0; o.keyframe_insert(prop, index=idx, frame=max(1, F(t)))
        getattr(o, prop)[idx] = v1; o.keyframe_insert(prop, index=idx, frame=max(1, F(t + P) - 1)); t += P
    lin(o)

# ---------------- room + desk
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.003, 0.004, 0.007, 1)
mdesk = bpy.data.materials.new("desk"); mdesk.use_nodes = True; nt = mdesk.node_tree; b = nt.nodes["Principled BSDF"]
wave = nt.nodes.new("ShaderNodeTexWave"); wave.inputs["Scale"].default_value = 3; wave.inputs["Distortion"].default_value = 6; wave.inputs["Detail"].default_value = 4
cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.09, 0.04, 0.018, 1); cr.color_ramp.elements[1].color = (0.22, 0.11, 0.05, 1)
nt.links.new(wave.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.35
bpy.ops.mesh.primitive_plane_add(size=14, location=(0, 0, 0)); bpy.context.object.data.materials.append(mdesk)
for (x, y, s, c, r) in ((-1.45, 0.9, 0.26, (0.7, 0.12, 0.1), 0.3), (-1.15, 1.35, 0.22, (0.15, 0.35, 0.7), -0.2), (1.55, 1.1, 0.24, (0.85, 0.65, 0.12), 0.5)):
    o = cube("blk", (x, y, s / 2), (s, s, s), mat("blk", c, 0.4), bevel=0.012); o.rotation_euler.z = r

# ---------------- the book (spine at x=0)
red = mat("cover", (0.45, 0.04, 0.035), 0.55, bumpscale=120, bumpstr=0.08)
paper = mat("paper", (0.62, 0.56, 0.44), 0.85, bumpscale=200, bumpstr=0.05)
gold = mat("gold", (0.85, 0.62, 0.22), 0.3, emit=0.15); ink = mat("ink", (0.08, 0.06, 0.05), 0.6)
cube("board", (0.51, 0, 0.006), (1.04, 1.46, 0.012), red, bevel=0.004)
cube("pages", (0.5, 0, 0.062), (1.0, 1.42, 0.1), paper)
hinge = empty("Hinge", (0, 0, 0.12))
cube("cover", (0.51, 0, 0.007), (1.04, 1.46, 0.014), red, parent=hinge, bevel=0.004)
cube("inner", (0.5, 0, -0.002), (1.0, 1.42, 0.004), paper, parent=hinge)
text("What If\nthe Moon\nVanished?", 0.13, (0.5, 0.05, 0.016), gold, parent=hinge, rot=(0, 0, 0), font=SERIF, extrude=0.002, holo=False)
text("~ a Leo story ~", 0.05, (0.5, -0.5, 0.016), gold, parent=hinge, rot=(0, 0, 0), font=SERIF, extrude=0.002, holo=False)
text("Chapter 1\nThe Moon", 0.08, (0.5, 0.1, -0.0045), ink, parent=hinge, rot=(0, math.pi, 0), font=SERIF, extrude=0.001, holo=False)
t_open = B["intro"][0] + 1.5
t_close = B["end"][0] + 1.9
for t, v in ((0, 0), (t_open, 0), (t_open + 1.2, -math.pi), (t_close, -math.pi), (t_close + 1.3, 0)):
    hinge.rotation_euler.y = v; hinge.keyframe_insert("rotation_euler", index=1, frame=F(t))

# loose pages that flip (each page change = a new projection)
FLIPS = [B[k][0] - 0.35 for k in ("earth", "beach", "after", "life", "tilt")]
for i, tf in enumerate(FLIPS):
    zr = 0.1155 - 0.0008 * i; zl = 0.1247 + 0.0008 * i
    ph = empty(f"PageH{i}", (0, 0, zr))
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=30, y_subdivisions=2, size=1, location=(0.5, 0, 0))
    pg = bpy.context.object; pg.scale = (0.99, 1.40, 1); bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    pg.data.materials.append(paper); pg.parent = ph
    bd = pg.modifiers.new("bend", "SIMPLE_DEFORM"); bd.deform_method = "BEND"; bd.deform_axis = "Y"; bd.origin = ph
    for t, rot, z, bend in ((0, 0, zr, 0), (tf, 0, zr, 0), (tf + 0.35, -math.pi * 0.45, zr + 0.01, 0.9), (tf + 0.8, -math.pi, zl, 0),
                            (t_close, -math.pi, zl, 0), (t_close + 1.3, 0, zr, 0)):
        ph.rotation_euler.y = rot; ph.keyframe_insert("rotation_euler", index=1, frame=F(t))
        ph.location.z = z; ph.keyframe_insert("location", index=2, frame=F(t))
        bd.angle = bend; bd.keyframe_insert("angle", frame=F(t))

# ---------------- projector: glowing ring in the gutter + light cone + drifting dust
beam_on = t_open + 0.9; beam_off = t_close - 0.5
pm = holo_mat("beam_core", CYAN2, 8.0, 0.9, 0.3, scan=False, sweep=False)
torus("ring", (0, 0, 0.128), 0.06, 0.006, pm)
bpy.ops.mesh.primitive_circle_add(vertices=48, radius=0.055, fill_type="NGON", location=(0, 0, 0.127)); finish(bpy.context.object, pm, None, True)
bpy.ops.mesh.primitive_cone_add(vertices=96, radius1=0.05, radius2=0.66, depth=1.15, end_fill_type="NOTHING", location=(0, 0, 0.13 + 0.575))
bpy.ops.object.shade_smooth(); finish(bpy.context.object, holo_mat("beam", CYAN, 2.5, 0.022, 0.12, scan=False, pattern=beam_pattern, sweep=False), None, True)
dm = holo_mat("dust", CYAN2, 6.0, 1.0, 0.0, scan=False, sweep=False)
for i in range(46):
    h = rnd.uniform(0.15, 1.0); rr = rnd.uniform(0, 0.05 + 0.5 * (h - 0.13)); an = rnd.uniform(0, 6.283)
    d = sphere("dust", (rr * math.cos(an), rr * math.sin(an), h), rnd.uniform(0.002, 0.004), dm, seg=6, holo=True)
    d.keyframe_insert("location", index=2, frame=1); d.location.z = h + 0.22; d.keyframe_insert("location", index=2, frame=NF); lin(d)
for g in ("beam_core", "beam", "dust"):
    fade(g, [(0, 0), (beam_on, 0), (beam_on + 0.1, 0.8), (beam_on + 0.2, 0.2), (beam_on + 0.35, 1.0), (beam_off, 1.0), (beam_off + 0.12, 0.3), (beam_off + 0.2, 0.8), (beam_off + 0.5, 0)])
holo_l = bpy.data.lights.new("HoloLight", "POINT"); holo_l.shadow_soft_size = 0.3; holo_l.color = CYAN
hl = bpy.data.objects.new("HoloLight", holo_l); col.objects.link(hl); hl.location = (0, 0, 0.75)
for t, e in ((0, 0), (beam_on, 0), (beam_on + 0.4, 9), (beam_off, 9), (beam_off + 0.5, 0)):
    holo_l.energy = e; holo_l.keyframe_insert("energy", frame=F(t))
for t, c in ((B["after"][0] - 0.4, CYAN), (B["after"][0] + 0.4, RED)):
    holo_l.color = c; holo_l.keyframe_insert("color", frame=F(t))

# ---------------- page 0: title
tm = holo_mat("title", CYAN2, 4.0, 0.55, 0.6)
text("WHAT IF\nTHE MOON\nVANISHED?", 0.12, (0, 0, 0.8), tm, font=SANS, extrude=0.008)
tr_ = torus("tring", (0, 0, 0.5), 0.34, 0.003, holo_mat("title", CYAN, 4.0, 0.9, 0.2, scan=False))
tr_.keyframe_insert("rotation_euler", index=2, frame=1); tr_.rotation_euler.z = 6.283; tr_.keyframe_insert("rotation_euler", index=2, frame=NF)
t_title = beam_on + 0.45
flicker_in("title", t_title, 0.45, 1.05)
fade_out("title", FLIPS[0] - 0.1)
# ---------------- earth pages: green land, blue ocean, rippling water bulge
def build_earth(g, land_c, water_c, with_moon, t0, t1, flow=False, z=0.74):
    root = empty(g + "_root", (0, 0, z)); tilt = empty(g + "_tilt", parent=root); tilt.rotation_euler.x = math.radians(23)
    spin = empty(g + "_spin", parent=tilt)
    sphere("land", (0, 0, 0), 0.166, holo_mat(g, land_c, 3.0, 0.05, 0.3, pattern=land_pattern(0.0, 2.6)), parent=spin, seg=64, holo=True)
    sphere("ocean", (0, 0, 0), 0.161, holo_mat(g, water_c, 2.2, 0.08, 0.55, pattern=land_pattern(1.0, 0.1)), parent=spin, seg=64, holo=True)
    wire(sphere("grid", (0, 0, 0), 0.169, holo_mat(g, water_c, 2.2, 0.35, 0.2, scan=False), parent=spin, seg=24, holo=True), None, 0.0025)
    spin.keyframe_insert("rotation_euler", index=2, frame=F(t0)); spin.rotation_euler.z = 2.2; spin.keyframe_insert("rotation_euler", index=2, frame=F(t1)); lin(spin)
    orb = empty(g + "_orbit", parent=root)
    bulge = sphere("bulge", (0, 0, 0), 0.18, holo_mat(g, WATER2, 2.6, 0.07, 0.6, pattern=ripple_pattern), parent=orb, scale=(1.34, 0.97, 0.97), seg=64, holo=True)
    if flow:  # water streams over the surface and piles up under (and opposite) the Moon
        fm = holo_mat(g, (0.6, 0.85, 1.0), 6.0, 1.0, 0.0, scan=False)
        for a_from, a_to in ((90, 18), (90, 162), (-90, -18), (-90, -162)):
            for k in range(3):
                pv = empty("flowp", parent=orb); sphere("flow", (0.176, 0, 0), 0.0075, fm, parent=pv, seg=8, holo=True)
                loop_keys(pv, 2, math.radians(a_from), math.radians(a_to), t0 - 1.5 + k * 0.5, t1, 1.5, "rotation_euler")
    if with_moon:
        mm = holo_mat(g, (0.85, 0.93, 1.0), 3.5, 0.3, 0.7, pattern=crater_pattern)
        sphere("moon", (0.43, 0, 0), 0.05, mm, parent=orb, seg=48, holo=True)
        torus("orbit", (0, 0, 0), 0.43, 0.0035, holo_mat(g, CYAN, 3.0, 0.7, 0.2, scan=False), parent=root)
        dm_ = holo_mat(g, CYAN2, 6.0, 1.0, 0.0, scan=False)
        for i in range(10):  # little packets of pull: ocean -> Moon
            dt = sphere("pull", (0.2, 0, 0), 0.0065, dm_, parent=orb, seg=8, holo=True); dt.location.y = (i // 5 - 0.5) * 0.05
            loop_keys(dt, 0, 0.23, 0.37, t0 - 1.0 + (i % 5) / 5, t1, 1.0)
        orb.keyframe_insert("rotation_euler", index=2, frame=F(t0)); orb.rotation_euler.z = 2 * math.pi * 0.75
        orb.keyframe_insert("rotation_euler", index=2, frame=F(t1)); lin(orb)
    return root, tilt, bulge

e0, e1 = B["earth"]
build_earth("earth", GREEN, WATER, True, e0 - 0.4, e1 + 0.4, flow=True)
lab = holo_mat("earth_lab", WATER2, 3.8, 0.65, 0.5)
text("WATER BULGE", 0.058, (0, 0, 0.47), lab, font=SANS)
flicker_in("earth", e0 + 0.3, 0.5, 1.0); fade_out("earth", FLIPS[1] - 0.1)
tb = word_t("earth", "bulge"); flicker_in("earth_lab", tb, 0.44, 0.5, 0.4); fade_out("earth_lab", FLIPS[1] - 0.1)

# ---------------- beach page: side-on cutaway of the shore, waves roll in, tide climbs the sand
b0, b1 = B["beach"]; v0, v1 = B["vanish"]; BZ = 0.3
broot = empty("beach_root", (0, 0, BZ))
zs = lambda x: max(-0.10, -0.10 + 0.4 * (x + 0.15))
def sand_mask(N, L, z):  # hide water that is under the sand surface (world coords)
    geo = N.new("ShaderNodeNewGeometry"); sp = N.new("ShaderNodeSeparateXYZ"); L(geo.outputs["Position"], sp.inputs[0])
    s = MN(N, L, "MAXIMUM", -0.10 + BZ, MN(N, L, "MULTIPLY_ADD", sp.outputs["X"], 0.4, -0.04 + BZ))
    return MN(N, L, "GREATER_THAN", z, MN(N, L, "SUBTRACT", s, 0.002))
me = bpy.data.meshes.new("sand"); bm = bmesh.new(); cols_ = []
for i in range(49):
    x = -0.4 + 0.8 * i / 48; zt = zs(x)
    cols_.append([bm.verts.new((x, y, z_)) for (y, z_) in ((-0.07, -0.15), (-0.07, zt), (0.07, zt), (0.07, -0.15))])
for c0, c1 in zip(cols_, cols_[1:]):
    for k in range(4): bm.faces.new((c0[k], c1[k], c1[(k + 1) % 4], c0[(k + 1) % 4]))
bm.faces.new(cols_[0][::-1]); bm.faces.new(cols_[-1]); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
shore = bpy.data.objects.new("sand", me); col.objects.link(shore)
finish(shore, holo_mat("beach", SANDC, 2.4, 0.2, 0.4), broot, True); wire(shore, holo_mat("beach", SANDC, 3.0, 0.8, 0.2, scan=False), 0.0022)
tv = word_t("vanish", "vanish") + 0.1  # the Moon blinks out on "vanished"
lo, hi = -0.035, 0.06
t_rise0 = word_t("beach", "sea") - 0.2; t_rise1 = t_rise0 + 3.2
SEAS = []
for nm, solid in (("sea", True), ("foam", False)):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=200, y_subdivisions=3 if solid else 2, size=1); o = bpy.context.object; o.name = nm
    o.scale = (0.8, 0.13, 1); bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o["x0"] = [v.co.x for v in o.data.vertices]
    if solid:
        so = o.modifiers.new("solid", "SOLIDIFY"); so.thickness = 0.3; so.offset = -1
        finish(o, holo_mat("beach", WATER, 2.6, 0.16, 0.65, pattern=sand_mask), broot, True)
    else:
        o.location.z = 0.001; wire(o, None, 0.0035); finish(o, holo_mat("beach", (0.7, 0.92, 1.0), 4.5, 0.9, 0.2, scan=False, pattern=sand_mask), broot, True)
    for t, z_ in ((0, lo), (t_rise0, lo), (t_rise1, hi), (tv + 0.8, hi), (tv + 3.5, lo - 0.01)):
        o.location.z = z_; o.keyframe_insert("location", index=2, frame=F(t))
    SEAS.append(o)
def wave_h(x, t):  # sharp crests rolling toward the shore, bigger near the beach; calm after the Moon is gone
    A = 0.024 - 0.019 * smooth((t - tv - 0.5) / 2.5); A *= 0.7 + 0.6 * min(1, max(0, (x + 0.4) / 0.8))
    return A * (2 * ((math.sin(34.9 * (x - 0.11 * t)) + 1) / 2) ** 2.5 - 0.3)
def _waves(scene, *_):
    t = (scene.frame_current - 1) / FPS
    for o in SEAS:
        co = [0.0] * (3 * len(o.data.vertices)); o.data.vertices.foreach_get("co", co)
        for i, x in enumerate(o["x0"]): co[3 * i + 2] = wave_h(x, t)
        o.data.vertices.foreach_set("co", co); o.data.update()
bpy.app.handlers.frame_change_pre.append(_waves)
# tide gauge on the right
gm = holo_mat("beach", CYAN2, 3.0, 0.8, 0.2, scan=False)
rod("gauge", (0.46, 0, -0.08), (0.46, 0, 0.13), 0.003, gm, broot)
for k in range(6): cube("tick", (0.46, 0, -0.06 + k * 0.035), (0.022, 0.003, 0.003), gm, parent=broot).visible_shadow = False
mk = cube("mark", (0.46, 0, lo), (0.05, 0.012, 0.006), holo_mat("beach", (1, 0.9, 0.4), 6.0, 1.0, 0.0, scan=False), parent=broot); mk.visible_shadow = False
for t, z_ in ((0, lo), (t_rise0, lo), (t_rise1, hi), (tv + 0.8, hi), (tv + 3.5, lo)):
    mk.location.z = z_; mk.keyframe_insert("location", index=2, frame=F(t))
hm = holo_mat("hightide", (1, 0.9, 0.45), 4.0, 0.8, 0.4)
text("HIGH TIDE", 0.055, (0.24, 0, 0.21), hm, parent=broot, font=SANS)
# the Moon (own group so it can glitch away)
MX, MZ = -0.2, 0.6
mroot = empty("bmoon_root", (MX, 0, MZ), parent=broot)
sphere("bmoon", (0, 0, 0), 0.075, holo_mat("bmoon", (0.85, 0.93, 1.0), 3.5, 0.3, 0.7, pattern=crater_pattern), parent=mroot, seg=48, holo=True)
wire(sphere("bmoonw", (0, 0, 0), 0.077, holo_mat("bmoon", CYAN2, 3.0, 0.45, 0.2, scan=False), parent=mroot, seg=20, holo=True), None, 0.0022)
sphere("halo", (0, 0, 0), 0.11, holo_mat("bmoon", CYAN, 2.0, 0.0, 0.3, scan=False), parent=mroot, seg=48, holo=True)
pdm = holo_mat("bmoon", CYAN2, 6.0, 1.0, 0.0, scan=False)
for i in range(12):  # water being tugged up toward the Moon
    dt = sphere("tug", ((i % 3 - 1) * 0.07, 0, 0), 0.0065, pdm, parent=mroot, seg=8, holo=True)
    loop_keys(dt, 2, -0.6, -0.12, b0 - 1.3 + (i // 3) / 4 * 1.3, tv + 0.5, 1.3)
flicker_in("beach", b0 + 0.3, 0.12, 1.0, 1.2); flicker_in("bmoon", b0 + 0.3, 0.12, 1.0, 1.2)
th = t_rise1 - 0.3; flicker_in("hightide", th, 0.46, 0.56, 0.4); fade_out("hightide", tv + 1.2)
fade_out("beach", FLIPS[2] - 0.1)
# glitch + shatter
fl = []; t = tv - 0.9
while t < tv + 0.15: fl.append((t, rnd.choice((0.15, 1.3, 0.5, 1.0, 0.0, 1.4)))); t += 2 / FPS
for mult, _ in PAGES["bmoon"]:
    for t, v in fl + [(tv + 0.25, 0.0)]: key_sock(mult.outputs[0], F(t), v)
for t, dx, s in ((tv - 1.0, 0, 1), (tv - 0.6, 0.012, 1), (tv - 0.5, -0.015, 1.05), (tv - 0.3, 0.02, 0.95), (tv - 0.1, -0.01, 1.2), (tv + 0.1, 0, 1.35), (tv + 0.25, 0, 0.01)):
    mroot.location.x = MX + dx; mroot.keyframe_insert("location", index=0, frame=F(t))
    mroot.scale = (s, s, s); mroot.keyframe_insert("scale", frame=F(t))
shm = holo_mat("shards", CYAN2, 7.0, 1.0, 0.0, scan=False)
for i in range(30):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=rnd.uniform(0.006, 0.014), location=(MX, 0, MZ))
    sh = finish(bpy.context.object, shm, broot, True)
    th_, ph2 = rnd.uniform(0, 6.283), rnd.uniform(-1.2, 1.2); sp = rnd.uniform(0.25, 0.5)
    sh.keyframe_insert("location", frame=F(tv + 0.15))
    sh.location = (MX + sp * math.cos(th_) * math.cos(ph2), sp * math.sin(th_) * math.cos(ph2) * 0.5, MZ + sp * math.sin(ph2))
    sh.keyframe_insert("location", frame=F(tv + 1.6))
    for t, hid in ((0, True), (tv + 0.1, True), (tv + 0.14, False), (tv + 1.65, True)):
        sh.hide_render = hid; sh.keyframe_insert("hide_render", frame=F(t))
fade("shards", [(0, 0), (tv + 0.12, 0), (tv + 0.18, 1.0), (tv + 0.7, 0.8), (tv + 1.6, 0)])
# where the Moon used to be: a flickering dashed outline (= missing)
gom = holo_mat("gone", (1.0, 0.45, 0.35), 4.0, 0.9, 0.0, scan=False)
for k in range(16):
    a_ = k / 16 * 2 * math.pi; a2 = a_ + 2 * math.pi / 16 * 0.55
    rod("dash", (MX + 0.08 * math.cos(a_), -0.02, MZ + 0.08 * math.sin(a_)), (MX + 0.08 * math.cos(a2), -0.02, MZ + 0.08 * math.sin(a2)), 0.0028, gom, broot)
fade("gone", [(0, 0), (tv + 0.35, 0), (tv + 0.45, 1.0), (tv + 0.6, 0.3), (tv + 0.75, 1.0), (tv + 1.0, 0.5), (tv + 1.15, 1.0), (FLIPS[2] - 0.1, 1.0), (FLIPS[2] + 0.2, 0.0)])

# ---------------- "after" page: no Moon, the bulge flattens, tides shrink
a0, a1 = B["after"]; l0, l1 = B["life"]; g0, g1 = B["tilt"]; n0, n1 = B["end"]
root, _, bulge = build_earth("after", LANDO, WATER, False, a0 - 0.4, FLIPS[3] + 0.5)
torus("ghost", (0, 0, 0), 0.43, 0.0018, holo_mat("ghost", RED, 2.0, 0.6, 0.2, scan=False), parent=root)
for t, sx in ((0, 1.34), (a0 + 0.9, 1.34), (word_t("after", "flatten") + 0.8, 1.02)):
    bulge.scale.x = sx; bulge.keyframe_insert("scale", index=0, frame=F(t))
at1 = holo_mat("after_t1", RED2, 4.0, 0.75, 0.5); tide_txt = text("TIDES  -66%", 0.078, (0, 0, 1.07), at1, font=SANS)
flicker_in("after", a0 + 0.3, 0.5, 1.0); flicker_in("ghost", a0 + 0.3, 0.5, 1.0)
for mult, _ in PAGES["ghost"]:
    for t in range(int((a0 + 1.5) * 4), int((FLIPS[3] - 0.2) * 4)): key_sock(mult.outputs[0], F(t / 4), rnd.choice((0.15, 0.5, 0.3, 0.0)))
    key_sock(mult.outputs[0], F(FLIPS[3] - 0.1), 0.0)
t_cnt = word_t("after", "third") - 0.2
flicker_in("after_t1", t_cnt, 1.0, 1.12, 0.4)
for g in ("after", "after_t1"): fade_out(g, FLIPS[3] - 0.1)

# ---------------- "life" page: a tide pool drains and strands a crab; corals lose their full-Moon cue
t_pool = l0 + 0.3; t_drain = word_t("life", "stop") - 0.1; t_strand = word_t("life", "stranded")
t_coral = word_t("life", "corals") - 0.35; t_spawn = word_t("life", "spawn") - 0.2; t_lose = word_t("life", "lose")
PZ = 0.62; proot = empty("pool_root", (0, 0, PZ))
rm = holo_mat("pool", ROCK, 2.6, 0.14, 0.6, pattern=crater_pattern)
for i in range(16):
    an = i / 16 * 2 * math.pi
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=rnd.uniform(0.035, 0.05), location=(0.21 * math.cos(an), 0.21 * math.sin(an), rnd.uniform(-0.01, 0.02)))
    o = bpy.context.object; o.scale = (1.3, 1.0, 0.8); finish(o, rm, proot, True)
bpy.ops.mesh.primitive_circle_add(vertices=48, radius=0.21, fill_type="TRIFAN", location=(0, 0, -0.045)); fl_ = bpy.context.object
finish(fl_, holo_mat("pool", ROCK, 2.2, 0.1, 0.3), proot, True); wire(fl_, holo_mat("pool", ROCK, 2.6, 0.7, 0.2, scan=False), 0.0018)
wl = empty("wlevel", (0, 0, -0.045), parent=proot)
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.195, depth=0.06, location=(0, 0, 0.03)); pw = bpy.context.object
finish(pw, holo_mat("poolw", WATER, 3.0, 0.22, 0.7, pattern=ripple_pattern), wl, True)
for t, s in ((0, 1), (t_drain, 1), (t_drain + 2.0, 0.03)): wl.scale.z = s; wl.keyframe_insert("scale", index=2, frame=F(t))
crab = empty("crab", (0, 0, -0.012), parent=proot); crab.scale = (2, 2, 2); cm_ = holo_mat("crab", CRABC, 3.4, 0.45, 0.7)
sphere("cbody", (0, 0, 0), 0.03, cm_, parent=crab, scale=(1.5, 1.0, 0.55), seg=24, holo=True)
for sx in (-1, 1):
    rod("stalk", (sx * 0.012, -0.02, 0.01), (sx * 0.014, -0.026, 0.03), 0.0022, cm_, crab)
    sphere("ceye", (sx * 0.014, -0.026, 0.032), 0.006, holo_mat("crab", (1, 1, 1), 5.0, 1.0, 0.0, scan=False), parent=crab, seg=10, holo=True)
    for k in range(3):
        y = -0.012 + k * 0.014; rod("leg", (sx * 0.035, y, 0), (sx * 0.06, y + 0.004, 0.012), 0.0026, cm_, crab)
        rod("leg2", (sx * 0.06, y + 0.004, 0.012), (sx * 0.072, y + 0.006, -0.016), 0.0024, cm_, crab)
    rod("arm", (sx * 0.03, -0.022, 0.004), (sx * 0.05, -0.045, 0.012), 0.0035, cm_, crab)
    sphere("claw", (sx * 0.052, -0.052, 0.014), 0.013, cm_, parent=crab, scale=(0.8, 1.2, 0.7), seg=14, holo=True)
xs = [0, -0.05, 0.04, -0.02, 0.05, -0.04, 0.03, -0.05, 0.04, 0]; t = t_pool + 0.6; k = 0
crab.keyframe_insert("location", frame=1)
while t < t_strand - 0.2:  # scuttle sideways, hop-hop
    crab.location.x = xs[k % len(xs)]; crab.location.z = -0.012; crab.keyframe_insert("location", frame=F(t)); k += 1; t += 0.45
crab.location.x = 0; crab.location.z = -0.016; crab.keyframe_insert("location", frame=F(t_strand + 0.2))
for t, r in ((0, 0), (t_strand, 0), (t_strand + 0.3, 0.25), (t_strand + 0.6, -0.25), (t_strand + 0.9, 0)):  # confused look-around
    crab.rotation_euler.z = r; crab.keyframe_insert("rotation_euler", index=2, frame=F(t))
st = holo_mat("strand", RED2, 4.0, 0.75, 0.5); text("STRANDED!", 0.06, (0, 0, 0.92), st, font=SANS)
flicker_in("pool", t_pool, PZ - 0.08, PZ + 0.06); flicker_in("poolw", t_pool, PZ - 0.08, PZ + 0.06); flicker_in("crab", t_pool + 0.4, PZ - 0.06, PZ + 0.03, 0.6)
flicker_in("strand", t_strand, 0.88, 0.97, 0.4)
for g in ("pool", "poolw", "crab", "strand"): fade_out(g, t_coral)
# coral reef
CZ = 0.44; croot = empty("coral_root", (0, 0, CZ)); TIPS = []
sphere("reef", (0, 0, 0), 0.16, holo_mat("coral", ROCK, 2.4, 0.14, 0.6, pattern=crater_pattern), parent=croot, scale=(1.5, 0.9, 0.3), seg=32, holo=True)
com = holo_mat("coral", PINK, 3.2, 0.3, 0.7)
def branch(p, d, ln, depth, r):
    q = p + d * ln; rod("br", p, q, r, com, croot)
    if depth == 0: TIPS.append(q); sphere("polyp", q, r * 1.6, com, parent=croot, seg=10, holo=True); return
    for sgn in (-1, 1):
        nd = (d + Vector((sgn * rnd.uniform(0.45, 0.8), rnd.uniform(-0.3, 0.3), rnd.uniform(-0.1, 0.25)))).normalized()
        branch(q, nd, ln * 0.72, depth - 1, r * 0.75)
for x0, lean in ((-0.13, -0.35), (0.0, 0.05), (0.13, 0.35)):
    branch(Vector((x0, 0, 0.03)), Vector((lean, 0, 1)).normalized(), 0.1 if x0 else 0.12, 2, 0.011)
cmr = empty("cmoon_root", (0, 0.05, 1.1))
sphere("cmoon", (0, 0, 0), 0.06, holo_mat("cmoon", (0.95, 0.97, 1.0), 4.0, 0.4, 0.7, pattern=crater_pattern), parent=cmr, seg=48, holo=True)
sphere("chalo", (0, 0, 0), 0.1, holo_mat("cmoon", (0.8, 0.9, 1.0), 2.4, 0.0, 0.35, scan=False), parent=cmr, seg=32, holo=True)
spm = holo_mat("spawn", (1.0, 0.75, 0.85), 6.0, 1.0, 0.0, scan=False)
for i, tp in enumerate(TIPS * 2):  # spawn drifting up toward the moonlight
    sp_ = sphere("egg", tp, 0.006, spm, parent=croot, seg=8, holo=True); P = 1.8
    loop_keys(sp_, 2, tp.z, tp.z + 0.4, t_spawn - P + (i * 0.37) % P, t_lose + 0.6, P)
flicker_in("coral", t_coral, CZ - 0.06, CZ + 0.42); flicker_in("cmoon", t_coral + 0.3, 1.02, 1.2, 0.5)
fade("spawn", [(0, 0), (t_spawn, 0), (t_spawn + 0.4, 1.0), (t_lose + 0.2, 1.0), (t_lose + 0.8, 0.0)])
glitch_out("cmoon", t_lose + 0.1)
fade("coral", [(t_lose + 0.3, 1.0), (t_lose + 1.0, 0.4)])
lm = holo_mat("lost", RED2, 4.0, 0.75, 0.5); text("CALENDAR: LOST", 0.05, (0, 0, 0.32), lm, font=SANS)
flicker_in("lost", word_t("life", "calendar") - 0.1, 0.28, 0.36, 0.4)
fade_out("coral", FLIPS[4] - 0.1, base=0.4); fade_out("lost", FLIPS[4] - 0.1)

# ---------------- "tilt" page: the axis (a glowing rod) swings left/right, live angle counter
root_t, tilt, bz = build_earth("tilt", LANDO, WATER, False, g0 - 0.4, n1)
bz.scale.x = 1.02; tilt.rotation_euler.x = 0
axm = holo_mat("tilt_ax", YEL, 5.5, 0.95, 0.2, scan=False)
rod("axis", (0, 0, -0.31), (0, 0, 0.31), 0.0042, axm, tilt, 12)
for zz in (-0.31, 0.31): sphere("pole", (0, 0, zz), 0.011, axm, parent=tilt, seg=12, holo=True)
rfm = holo_mat("tilt_ref", WHITE, 2.4, 0.8, 0.0, scan=False)
for k in range(13): rod("ref", (0, 0, -0.33 + k * 0.055), (0, 0, -0.33 + k * 0.055 + 0.025), 0.0016, rfm, root_t)
tilt_txt = text("TILT  23°", 0.078, (0, 0, 1.08), holo_mat("tilt_t1", RED2, 4.0, 0.75, 0.5), font=SANS)
text("SEASONS: SCRAMBLED", 0.048, (0, 0, 0.46), holo_mat("tilt_t2", RED2, 4.0, 0.7, 0.5), font=SANS)
tw_ = word_t("tilt", "wobble") - 0.8
def tilt_deg(t):
    u = t - tw_; amp = smooth(u / 1.8); return 23 + amp * (21 * math.sin(1.5 * u) + 8 * math.sin(3.3 * u + 0.6))
for f in range(max(1, F(g0 - 0.5)), NF + 1):
    tilt.rotation_euler.y = math.radians(tilt_deg((f - 1) / FPS)); tilt.keyframe_insert("rotation_euler", index=1, frame=f)
flicker_in("tilt", g0 + 0.3, 0.5, 1.0); flicker_in("tilt_ax", g0 + 0.5, 0.42, 1.06); flicker_in("tilt_ref", g0 + 0.5, 0.4, 1.08)
flicker_in("tilt_t1", g0 + 0.8, 1.0, 1.13, 0.4); flicker_in("tilt_t2", word_t("tilt", "scrambl") - 0.2, 0.42, 0.5, 0.4)
# finale: the projection collapses back into the book (top-down de-rez)
tc0 = n0 + 0.4
for g in ("tilt", "tilt_ax", "tilt_ref", "tilt_t1", "tilt_t2"):
    reveal(g, [(tc0, 1.25), (tc0 + 1.1, 0.3)])
    for mult, _ in PAGES[g]: key_sock(mult.outputs[0], F(tc0 + 1.15), 1.0); key_sock(mult.outputs[0], F(tc0 + 1.25), 0.0)

# ---------------- Leo vinyl figurine on the desk, watching
leo = empty("Leo", (0.43, -0.86, 0.001)); leo.scale = (1.6, 1.6, 1.6)
skin = mat("skin", (0.62, 0.38, 0.24), 0.4, coat=0.3); hood = mat("hood", (0.95, 0.62, 0.05), 0.45, coat=0.4)
shorts = mat("shorts", (0.3, 0.2, 0.12), 0.6); shoe = mat("shoe", (0.75, 0.08, 0.06), 0.35, coat=0.5)
hair = mat("hair", (0.05, 0.03, 0.02), 0.55); eye = mat("eye", (0.01, 0.01, 0.01), 0.05, coat=1.0); shine = mat("shine", (1, 1, 1), 0.2, emit=5)
for sx in (-1, 1):
    cube("shoe", (sx * 0.016, -0.004, 0.006), (0.022, 0.032, 0.014), shoe, parent=leo, bevel=0.005)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.008, depth=0.05, location=(sx * 0.016, 0, 0.036)); finish(bpy.context.object, skin, leo, False)
cube("shorts", (0, 0, 0.065), (0.058, 0.04, 0.03), shorts, parent=leo, bevel=0.01)
sphere("torso", (0, 0, 0.1), 0.036, hood, parent=leo, scale=(1.05, 0.85, 1.15))
sho = {}
for sx in (-1, 1):
    sho[sx] = empty(f"Sh{sx}", (sx * 0.04, 0, 0.123), parent=leo); sho[sx].rotation_euler.y = sx * 0.25
    sphere("arm", (0, 0, -0.024), 0.012, hood, parent=sho[sx], scale=(1, 1, 2.4))
    sphere("hand", (0, 0, -0.052), 0.0105, skin, parent=sho[sx])
head = empty("Head", (0, 0, 0.14), parent=leo)
sphere("face", (0, 0, 0.05), 0.05, skin, parent=head)
for i in range(16):
    an = i / 16 * 2 * math.pi; rr = 0.046
    sphere("curl", (math.cos(an) * rr * 0.9, math.sin(an) * rr * 0.75 + 0.012, 0.075 + 0.012 * math.sin(an * 3)), 0.02, hair, parent=head, seg=12)
for i in range(6):
    sphere("curl", (rnd.uniform(-0.03, 0.03), rnd.uniform(-0.01, 0.03), 0.095), 0.022, hair, parent=head, seg=12)
for sx in (-1, 1):
    sphere("eye", (sx * 0.018, -0.045, 0.05), 0.011, eye, parent=head, scale=(1, 0.6, 1.25))
    sphere("shine", (sx * 0.018 + 0.004, -0.052, 0.057), 0.003, shine, parent=head, seg=8)
    sphere("cheek", (sx * 0.03, -0.04, 0.035), 0.008, mat("cheek", (0.9, 0.35, 0.35), 0.6), parent=head, scale=(1, 0.4, 0.6), seg=12)
EYES = [o for o in head.children if o.name.startswith("eye")]
mouth = sphere("mouth", (0, -0.0445, 0.026), 0.01, mat("mouth", (0.25, 0.04, 0.04), 0.4), parent=head, scale=(1.3, 0.35, 0.45), seg=16)
BROWS = []
for sx in (-1, 1):
    br = sphere("brow", (sx * 0.019, -0.047, 0.069), 0.0075, hair, parent=head, scale=(1.5, 0.45, 0.42), seg=12); br.rotation_euler.y = sx * 0.2; BROWS.append(br)
SMILE, OH, FLAT = (1.3, 0.35, 0.45), (0.8, 0.45, 1.35), (1.0, 0.35, 0.3)
t_wow = beam_on + 0.3
for t, sh_ in ((0, SMILE), (t_wow, SMILE), (t_wow + 0.25, OH), (t_wow + 2.2, OH), (t_wow + 2.6, SMILE), (tv - 1.2, SMILE), (tv - 0.9, FLAT),
               (tv + 0.05, FLAT), (tv + 0.2, OH), (B["after"][1] - 0.5, OH), (B["after"][1], FLAT), (END - 2.0, FLAT), (END - 1.5, SMILE)):
    mouth.scale = sh_; mouth.keyframe_insert("scale", frame=F(t))
for br in BROWS:
    z0 = br.location.z
    for t, dz in ((0, 0), (t_wow, 0), (t_wow + 0.25, 0.007), (t_wow + 2.2, 0.007), (t_wow + 2.6, 0), (tv - 1.2, 0), (tv - 0.9, -0.003),
                  (tv + 0.05, -0.003), (tv + 0.2, 0.009), (B["after"][1] - 0.5, 0.009), (B["after"][1], 0)):
        br.location.z = z0 + dz; br.keyframe_insert("location", index=2, frame=F(t))
blinks = [t for t in (0.6, 3.2, 6.1, 9.4, 12.8, 15.9, 19.2, 22.6, 27.5, 31.0, 34.8, 38.0) if abs(t - tv) > 1.2 and t < END - 0.5]
for e_ in EYES:
    sz = e_.scale.z; e_.keyframe_insert("scale", index=2, frame=1)
    for t in blinks:
        f = F(t)
        for df, k in ((0, 1), (2, 0.1), (4, 1)): e_.scale.z = sz * k; e_.keyframe_insert("scale", index=2, frame=f + df)
FACE_CAM, FACE_HOLO = math.radians(22), math.radians(-152)
for t, r in ((0, FACE_CAM), (0.9, FACE_CAM), (1.7, FACE_HOLO), (END - 2.4, FACE_HOLO), (END - 1.5, FACE_CAM)):
    leo.rotation_euler.z = r; leo.keyframe_insert("rotation_euler", index=2, frame=F(t))
for t, hx in ((0, 0), (1.2, 0), (beam_on, -0.12), (t_title, -0.38), (b0 + 0.5, -0.38), (v0 + 0.3, -0.55), (tv + 0.4, -0.55), (tv + 0.7, -0.3),
              (END - 2.4, -0.3), (END - 1.6, 0)):
    head.rotation_euler.x = hx; head.keyframe_insert("rotation_euler", index=0, frame=F(t))
# arms at rest; little flinch when the Moon vanishes
R = sho[-1]
for t, rx, ry in ((0, 0, -0.25),):  # arms rest (Leo only watches; the Moon vanishes on its own)
    R.rotation_euler.x = rx; R.rotation_euler.y = ry; R.keyframe_insert("rotation_euler", frame=F(t))
for t, lx in ((0, 0), (tv + 1.25, 0), (tv + 1.45, 0.12), (tv + 2.3, 0)):  # little jump back
    leo.rotation_euler.x = lx; leo.keyframe_insert("rotation_euler", index=0, frame=F(t))

# ---------------- lights: dim warm lamp + cool fill
lamp = bpy.data.lights.new("Lamp", "SPOT"); lamp.energy = 40; lamp.color = (1.0, 0.7, 0.42); lamp.spot_size = math.radians(75); lamp.spot_blend = 0.7; lamp.shadow_soft_size = 0.3
lo_ = bpy.data.objects.new("Lamp", lamp); col.objects.link(lo_); lo_.location = (-1.5, -1.1, 2.0)
tgt0 = empty("BookC", (0.3, -0.2, 0.1))
tk = lo_.constraints.new("TRACK_TO"); tk.target = tgt0; tk.track_axis = "TRACK_NEGATIVE_Z"; tk.up_axis = "UP_Y"
fill = bpy.data.lights.new("Fill", "AREA"); fill.energy = 10; fill.color = (0.5, 0.6, 1.0); fill.size = 2
fo = bpy.data.objects.new("Fill", fill); col.objects.link(fo); fo.location = (1.8, -1.6, 1.4)
tk = fo.constraints.new("TRACK_TO"); tk.target = tgt0; tk.track_axis = "TRACK_NEGATIVE_Z"; tk.up_axis = "UP_Y"

# ---------------- camera
cd = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cd); col.objects.link(cam); sc.camera = cam
cd.lens = 26; cd.sensor_fit = "VERTICAL"; cd.sensor_height = 24
tgt = empty("Tgt"); c = cam.constraints.new("TRACK_TO"); c.target = tgt; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
cd.dof.use_dof = True; cd.dof.focus_object = tgt; cd.dof.aperture_fstop = 2.8
i0, i1 = B["intro"]
keys = [(0.0, (0.95, -1.75, 0.5), (0.3, -0.35, 0.14)), (2.4, (0.75, -1.95, 0.62), (0.15, -0.15, 0.22)),
        (i1 - 0.4, (0.05, -2.3, 1.0), (0, 0, 0.74)),
        (e0 + 0.6, (-0.1, -2.1, 1.08), (0, 0, 0.74)), (e1 - 0.4, (-0.5, -1.85, 1.18), (0, 0, 0.72)),
        (b0 + 0.8, (0.05, -1.95, 0.8), (0.03, 0, 0.52)), (b1 - 0.1, (0.15, -1.8, 0.76), (0.05, 0, 0.52)),
        (v0 + 0.7, (0.55, -1.85, 0.66), (-0.15, 0, 0.84)), (tv + 0.2, (0.5, -1.78, 0.64), (-0.18, 0, 0.88)),
        (tv + 1.2, (0.48, -1.74, 0.63), (-0.18, 0, 0.88)),
        (tv + 1.2 + 1.0 / FPS, (0.25, -0.53, 0.44), (0.43, -0.86, 0.31)), (tv + 2.4, (0.29, -0.6, 0.41), (0.43, -0.86, 0.31)),
        (a0 + 0.7, (-0.2, -2.05, 1.06), (0, 0, 0.74)), (a1 - 0.4, (0.22, -1.9, 1.0), (0, 0, 0.72)),
        (l0 + 0.6, (0.05, -1.3, 1.2), (0, 0, 0.6)), (t_coral - 0.3, (-0.12, -1.25, 1.12), (0, 0, 0.6)),
        (t_coral + 0.6, (0.12, -1.55, 0.88), (0, 0, 0.72)), (l1 - 0.4, (-0.1, -1.5, 0.92), (0, 0, 0.74)),
        (g0 + 0.6, (0.0, -1.75, 0.82), (0, 0, 0.76)), (g1 - 0.4, (0.12, -1.65, 0.8), (0, 0, 0.76)),
        (n0 + 0.7, (0.2, -2.25, 0.95), (0, 0, 0.55)), (END, (0.6, -2.0, 0.6), (0.25, -0.35, 0.18))]
for f in range(1, NF + 1):
    t = (f - 1) / FPS
    for (t0, p0, g0_), (t1, p1, g1_) in zip(keys, keys[1:]):
        if t0 <= t <= t1: k = smooth((t - t0) / (t1 - t0)); break
    else: (t0, p0, g0_), (t1, p1, g1_), k = keys[-2], keys[-1], 1.0
    cam.location = [x + (y - x) * k for x, y in zip(p0, p1)]; cam.keyframe_insert("location", frame=f)
    tgt.location = [x + (y - x) * k for x, y in zip(g0_, g1_)]; tgt.keyframe_insert("location", frame=f)
cfl = bpy.data.lights.new("FaceFill", "AREA"); cfl.energy = 2.5; cfl.color = (0.6, 0.85, 1.0); cfl.size = 0.3
cfo = bpy.data.objects.new("FaceFill", cfl); col.objects.link(cfo); cfo.location = (0.2, -0.45, 0.55)
tk = cfo.constraints.new("TRACK_TO"); tk.target = leo; tk.track_axis = "TRACK_NEGATIVE_Z"; tk.up_axis = "UP_Y"
# scan band rolls up through every hologram; water ripples move
for sw in SWEEPS:
    for f in range(1, NF + 13, 12): key_sock(sw.outputs[0], f, (f - 1) / FPS * 0.55)
for wv in RIPPLES:
    for f in range(1, NF + 13, 12): key_sock(wv.inputs["Phase Offset"], f, -(f - 1) / FPS * 5.0)
# live counters: TIDES -0% -> -66%, TILT angle
def _count(scene, *_):
    t = (scene.frame_current - 1) / FPS
    tide_txt.data.body = f"TIDES  -{int(66 * smooth((t - t_cnt) / 1.2))}%"
    tilt_txt.data.body = f"TILT  {int(round(tilt_deg(t)))}°"
bpy.app.handlers.frame_change_pre.append(_count)
if "--cues" in a:  # sound-design cue times (audio timeline)
    cues = {"beam_on": beam_on, "beam_off": beam_off, "open": t_open, "close": t_close, "flips": FLIPS,
            "builds": [t_title, e0 + 0.3, b0 + 0.3, a0 + 0.3, tb, th, t_cnt, t_pool, t_strand, t_coral, g0 + 0.3, word_t("tilt", "scrambl") - 0.2],
            "glitch": tv - 0.9, "shatter": tv + 0.15, "derez": tc0, "tide": [t_rise0, t_rise1], "cu": [tv + 1.2, tv + 2.4],
            "fizzle": t_lose - 0.6, "drain": [t_drain, t_drain + 2.0], "spawn": t_spawn}
    json.dump({"off": OFF, "fps": FPS, "film_frames": NF,
               "cues": {k: ([x + OFF for x in v] if isinstance(v, list) else v + OFF) for k, v in cues.items()}},
              open(a[a.index("--cues") + 1], "w"), indent=1)
    sys.exit()

sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 94
if "--probe" in a:
    from bpy_extras.object_utils import world_to_camera_view
    sc.frame_set(STILL)
    for o in sc.objects:
        if o.type in ("MESH", "FONT"):
            p_ = world_to_camera_view(sc, cam, o.matrix_world.translation)
            if abs(p_.x - 0.33) < 0.06 and abs(p_.y - 0.67) < 0.06: print("PROBE", o.name, tuple(round(v, 3) for v in o.matrix_world.translation), o.visible_shadow)
    sys.exit()
if STILL:
    sc.frame_start = sc.frame_end = STILL; sc.frame_set(STILL); sc.render.filepath = f"{OUT}/still_{STILL}.jpg"; bpy.ops.render.render(write_still=True)
else:
    sc.frame_start, sc.frame_end = G[SI] + 1, G[SI + 1]; sc.render.filepath = f"{OUT}/f_"; sc.render.use_overwrite = False; bpy.ops.render.render(animation=True)
