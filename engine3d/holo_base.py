"""Shared base for hologram-storybook scenes (exec()ed by each scene script).
Provides: scene setup, hologram materials, helpers, and build_* functions for the room, book, projector, title, Leo, lights, camera and the render/cue tail.
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

YEL = (1.0, 0.85, 0.35); WHITE = (0.85, 0.9, 1.0); GREEN = (0.15, 1.0, 0.25); ORANGE = (1.0, 0.5, 0.15); PINK = (1.0, 0.3, 0.62)
COUNTERS = []  # per-frame text updaters: fn(t)

def build_room():
    w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.003, 0.004, 0.007, 1)
    mdesk = bpy.data.materials.new("desk"); mdesk.use_nodes = True; nt = mdesk.node_tree; b = nt.nodes["Principled BSDF"]
    wave = nt.nodes.new("ShaderNodeTexWave"); wave.inputs["Scale"].default_value = 3; wave.inputs["Distortion"].default_value = 6; wave.inputs["Detail"].default_value = 4
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.09, 0.04, 0.018, 1); cr.color_ramp.elements[1].color = (0.22, 0.11, 0.05, 1)
    nt.links.new(wave.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.35
    bpy.ops.mesh.primitive_plane_add(size=14, location=(0, 0, 0)); bpy.context.object.data.materials.append(mdesk)
    for (x, y, s, c, r) in ((-1.45, 0.9, 0.26, (0.7, 0.12, 0.1), 0.3), (-1.15, 1.35, 0.22, (0.15, 0.35, 0.7), -0.2), (1.55, 1.1, 0.24, (0.85, 0.65, 0.12), 0.5)):
        o = cube("blk", (x, y, s / 2), (s, s, s), mat("blk", c, 0.4), bevel=0.012); o.rotation_euler.z = r

def build_book(cover, chapter, flips, t_open, t_close):
    red = mat("cover", (0.45, 0.04, 0.035), 0.55, bumpscale=120, bumpstr=0.08)
    paper = mat("paper", (0.62, 0.56, 0.44), 0.85, bumpscale=200, bumpstr=0.05)
    gold = mat("gold", (0.85, 0.62, 0.22), 0.3, emit=0.15); ink = mat("ink", (0.08, 0.06, 0.05), 0.6)
    cube("board", (0.51, 0, 0.006), (1.04, 1.46, 0.012), red, bevel=0.004)
    cube("pages", (0.5, 0, 0.062), (1.0, 1.42, 0.1), paper)
    hinge = empty("Hinge", (0, 0, 0.12))
    cube("cover", (0.51, 0, 0.007), (1.04, 1.46, 0.014), red, parent=hinge, bevel=0.004)
    cube("inner", (0.5, 0, -0.002), (1.0, 1.42, 0.004), paper, parent=hinge)
    text(cover, 0.12, (0.5, 0.05, 0.016), gold, parent=hinge, rot=(0, 0, 0), font=SERIF, extrude=0.002, holo=False)
    text("~ a Leo story ~", 0.05, (0.5, -0.5, 0.016), gold, parent=hinge, rot=(0, 0, 0), font=SERIF, extrude=0.002, holo=False)
    text(chapter, 0.08, (0.5, 0.1, -0.0045), ink, parent=hinge, rot=(0, math.pi, 0), font=SERIF, extrude=0.001, holo=False)
    for t, v in ((0, 0), (t_open, 0), (t_open + 1.2, -math.pi), (t_close, -math.pi), (t_close + 1.3, 0)):
        hinge.rotation_euler.y = v; hinge.keyframe_insert("rotation_euler", index=1, frame=F(t))
    for i, tf in enumerate(flips):
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

def build_projector(beam_on, beam_off, light_colors=()):
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
    for t, c in light_colors: holo_l.color = c; holo_l.keyframe_insert("color", frame=F(t))
    return holo_l

def build_title(body, t_in, t_out, size=0.12, dur=1.1):
    tm = holo_mat("title", CYAN2, 4.0, 0.55, 0.6)
    text(body, size, (0, 0, 0.8), tm, font=SANS, extrude=0.008)
    tr_ = torus("tring", (0, 0, 0.5), 0.34, 0.003, holo_mat("title", CYAN, 4.0, 0.9, 0.2, scan=False))
    tr_.keyframe_insert("rotation_euler", index=2, frame=1); tr_.rotation_euler.z = 6.283; tr_.keyframe_insert("rotation_euler", index=2, frame=NF)
    flicker_in("title", t_in, 0.45, 1.05, dur); fade_out("title", t_out)

SMILE, OH, FLAT = (1.3, 0.35, 0.45), (0.8, 0.45, 1.35), (1.0, 0.35, 0.3)
def build_leo():
    global leo, head, mouth, BROWS, EYES, sho
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

def animate_leo(expr, head_keys, flinches=(), turn=(0.9, 1.7), turn_back=None):
    """expr: [(t, 'smile'|'oh'|'flat')] -> mouth + brows; head_keys: [(t, pitch)]; flinches: jump-back times."""
    shp = {"smile": (SMILE, 0), "oh": (OH, 0.008), "flat": (FLAT, -0.003)}
    z0 = [b.location.z for b in BROWS]
    for t, e in [(0, expr[0][1])] + list(expr):
        mouth.scale = shp[e][0]; mouth.keyframe_insert("scale", frame=F(t))
        for b, z in zip(BROWS, z0): b.location.z = z + shp[e][1]; b.keyframe_insert("location", index=2, frame=F(t))
    for e_ in EYES:
        sz = e_.scale.z; e_.keyframe_insert("scale", index=2, frame=1)
        for t in (0.6, 3.2, 6.1, 9.4, 12.8, 15.9, 19.2, 22.6, 27.5, 31.0, 34.8, 38.0, 43.0, 47.5, 52.0, 56.5):
            if t > END - 0.5 or any(abs(t - f) < 1.0 for f in flinches): continue
            for df, k in ((0, 1), (2, 0.1), (4, 1)): e_.scale.z = sz * k; e_.keyframe_insert("scale", index=2, frame=F(t) + df)
    FACE_CAM, FACE_HOLO = math.radians(22), math.radians(-152)
    tb = turn_back if turn_back is not None else END - 2.4
    for t, r in ((0, FACE_CAM), (turn[0], FACE_CAM), (turn[1], FACE_HOLO), (tb, FACE_HOLO), (tb + 0.9, FACE_CAM)):
        leo.rotation_euler.z = r; leo.keyframe_insert("rotation_euler", index=2, frame=F(t))
    for t, hx in head_keys: head.rotation_euler.x = hx; head.keyframe_insert("rotation_euler", index=0, frame=F(t))
    leo.keyframe_insert("rotation_euler", index=0, frame=1)
    for tf in flinches:
        for t, lx in ((tf, 0), (tf + 0.2, 0.12), (tf + 1.0, 0)): leo.rotation_euler.x = lx; leo.keyframe_insert("rotation_euler", index=0, frame=F(t))

def build_lights():
    lamp = bpy.data.lights.new("Lamp", "SPOT"); lamp.energy = 40; lamp.color = (1.0, 0.7, 0.42); lamp.spot_size = math.radians(75); lamp.spot_blend = 0.7; lamp.shadow_soft_size = 0.3
    lo_ = bpy.data.objects.new("Lamp", lamp); col.objects.link(lo_); lo_.location = (-1.5, -1.1, 2.0)
    tgt0 = empty("BookC", (0.3, -0.2, 0.1))
    tk = lo_.constraints.new("TRACK_TO"); tk.target = tgt0; tk.track_axis = "TRACK_NEGATIVE_Z"; tk.up_axis = "UP_Y"
    fill = bpy.data.lights.new("Fill", "AREA"); fill.energy = 10; fill.color = (0.5, 0.6, 1.0); fill.size = 2
    fo = bpy.data.objects.new("Fill", fill); col.objects.link(fo); fo.location = (1.8, -1.6, 1.4)
    tk = fo.constraints.new("TRACK_TO"); tk.target = tgt0; tk.track_axis = "TRACK_NEGATIVE_Z"; tk.up_axis = "UP_Y"
    cfl = bpy.data.lights.new("FaceFill", "AREA"); cfl.energy = 2.5; cfl.color = (0.6, 0.85, 1.0); cfl.size = 0.3
    cfo = bpy.data.objects.new("FaceFill", cfl); col.objects.link(cfo); cfo.location = (0.2, -0.45, 0.55)
    tk = cfo.constraints.new("TRACK_TO"); tk.target = leo; tk.track_axis = "TRACK_NEGATIVE_Z"; tk.up_axis = "UP_Y"

LEO_CU = [((0.25, -0.53, 0.44), (0.43, -0.86, 0.31)), ((0.29, -0.6, 0.41), (0.43, -0.86, 0.31))]  # Leo face close-up (cam, target) start/end
def build_camera(keys):
    """keys: [(t, cam_pos, target)], smooth-eased between keys; two keys 1/FPS apart = hard cut."""
    global cam
    cd = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cd); col.objects.link(cam); sc.camera = cam
    cd.lens = 26; cd.sensor_fit = "VERTICAL"; cd.sensor_height = 24
    tgt = empty("Tgt"); c = cam.constraints.new("TRACK_TO"); c.target = tgt; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
    cd.dof.use_dof = True; cd.dof.focus_object = tgt; cd.dof.aperture_fstop = 2.8
    keys = sorted(keys, key=lambda k: k[0])
    for f in range(1, NF + 1):
        t = (f - 1) / FPS
        for (t0, p0, g0_), (t1, p1, g1_) in zip(keys, keys[1:]):
            if t0 <= t <= t1: k = smooth((t - t0) / max(1e-6, t1 - t0)); break
        else: (t0, p0, g0_), (t1, p1, g1_), k = keys[-2], keys[-1], 1.0
        cam.location = [x + (y - x) * k for x, y in zip(p0, p1)]; cam.keyframe_insert("location", frame=f)
        tgt.location = [x + (y - x) * k for x, y in zip(g0_, g1_)]; tgt.keyframe_insert("location", frame=f)

def finish_scene(cues):
    for sw in SWEEPS:
        for f in range(1, NF + 13, 12): key_sock(sw.outputs[0], f, (f - 1) / FPS * 0.55)
    for wv in RIPPLES:
        for f in range(1, NF + 13, 12): key_sock(wv.inputs["Phase Offset"], f, -(f - 1) / FPS * 5.0)
    def _count(scene, *_):
        t = (scene.frame_current - 1) / FPS
        for fn in COUNTERS: fn(t)
    bpy.app.handlers.frame_change_pre.append(_count)
    if "--cues" in a:  # sound-design cue times (audio timeline)
        sh_ = lambda v: [sh_(x) for x in v] if isinstance(v, list) else v + OFF
        json.dump({"off": OFF, "fps": FPS, "film_frames": NF, "cues": {k: sh_(v) for k, v in cues.items()}}, open(a[a.index("--cues") + 1], "w"), indent=1)
        sys.exit()
    sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 94
    if STILL:
        sc.frame_start = sc.frame_end = STILL; sc.frame_set(STILL); sc.render.filepath = f"{OUT}/still_{STILL}.jpg"; bpy.ops.render.render(write_still=True)
    else:
        sc.frame_start, sc.frame_end = G[SI] + 1, G[SI + 1]; sc.render.filepath = f"{OUT}/f_"; sc.render.use_overwrite = False; bpy.ops.render.render(animation=True)
