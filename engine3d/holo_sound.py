"""What if sound traveled at walking speed? Hologram-storybook scene (Leo + projecting book).
python(bpy) holo_sound.py timing.json shot_index out_dir [--still FILM_FRAME] [--cues out.json]
beats: intro, why, talk, storm, wind, boom, end
"""
import os
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "holo_base.py")).read())

_fade0, _reveal0 = fade, reveal; DEFER = []
def fade(group, keys): DEFER.append((_fade0, group, list(keys)))
def reveal(group, keys): DEFER.append((_reveal0, group, list(keys)))
i0, i1 = B["intro"]; w0, w1 = B["why"]; k0, k1 = B["talk"]; s0, s1 = B["storm"]; d0, d1 = B["wind"]; o0, o1 = B["boom"]; n0, n1 = B["end"]
W = lambda beat, w, d=0.0: word_t(beat, w) + d
FLIPS = [B[k][0] - 0.35 for k in ("why", "talk", "storm", "wind", "boom", "end")]
t_open = i0 + 0.15; t_close = W("end", "world") + 0.7
beam_on = t_open + 0.9; beam_off = t_close - 0.5
build_room()
build_book("What If\nSound Was\nSlow?", "Chapter 2\nSound", FLIPS, t_open, t_close)
holo_l = build_projector(beam_on, beam_off)
t_title = beam_on + 0.3
build_title("WHAT IF\nSOUND WAS\nSLOW?", t_title, FLIPS[0] - 0.1, dur=0.45)
BUILDS = [t_title]

def hm(group, color, s=3.5, base=0.3, edge=0.7, scan=True): return holo_mat(group, color, s, base, edge, scan=scan)
def label(body, size, loc, group, color=WHITE, t_in=None, parent=None):
    o = text(body, size, loc, hm(group, color, 4.0, 0.75, 0.5), parent=parent, font=SANS)
    if t_in is not None:
        z = loc[2] + (parent.location.z if parent else 0); flicker_in(group, t_in, z - 0.05, z + 0.05, 0.35); BUILDS.append(t_in)
    return o
def person(name, m, loc, parent=None, s=1.0):
    r = empty(name, loc, parent); r.scale = (s, s, s)
    sphere("head", (0, 0, 0.17), 0.03, m, parent=r, seg=16, holo=True)
    rod("torso", (0, 0, 0.135), (0, 0, 0.06), 0.013, m, r)
    for sx in (-1, 1):
        rod("leg", (0, 0, 0.06), (sx * 0.025, 0, 0.0), 0.009, m, r)
        rod("arm", (0, 0, 0.125), (sx * 0.045, 0, 0.07), 0.008, m, r)
    return r
def clock(name, m, loc, parent=None, R=0.035):
    r = empty(name, loc, parent); torus("rim", (0, 0, 0), R, 0.004, m, parent=r, rot=(math.pi / 2, 0, 0))
    rod("hand_m", (0, 0, 0), (0, 0, R * 0.8), 0.003, m, r); hh = empty("hand", parent=r); rod("hand_s", (0, 0, 0), (0, 0, R * 0.6), 0.003, m, hh)
    return r, hh
def spin_hand(hh, t0, t1, turns):
    hh.rotation_euler.y = 0; hh.keyframe_insert("rotation_euler", index=1, frame=F(t0))
    hh.rotation_euler.y = 2 * math.pi * turns; hh.keyframe_insert("rotation_euler", index=1, frame=F(t1)); lin(hh)
def boom_ring(name, m, loc, t, R=0.25, parent=None):  # expanding shock ring
    o = torus(name, loc, R, 0.004, m, parent=parent, rot=(math.pi / 2, 0, 0))
    for tt, s in ((0, 0.02), (t, 0.02), (t + 0.5, 1.0)): o.scale = (s, s, s); o.keyframe_insert("scale", frame=F(tt))
    for tt, h in ((0, True), (t - 0.02, True), (t, False), (t + 0.55, True)): o.hide_render = h; o.keyframe_insert("hide_render", frame=F(tt))
    return o

# ================= page 1: WHY — air molecules knock each other like dominoes; 343 m/s -> 1.4 m/s
t_mol, t_dom, t_343, t_slow, t_walk = W("why", "molecules"), W("why", "dominoes"), W("why", "343"), W("why", "slow"), W("why", "walking")
mm = hm("why", CYAN2, 4.0, 0.55, 0.6); XS = [-0.33 + 0.66 * i / 15 for i in range(16)]; MZ = 0.72
mols = [sphere("mol", (x, 0, MZ), 0.022, mm, seg=20, holo=True) for x in XS]
glow = sphere("pulse", (0, 0, MZ), 0.05, hm("why", (0.7, 0.95, 1.0), 3.0, 0.25, 0.3, scan=False), seg=20, holo=True)
def pulse_x(t):  # pulse position: fast laps, then slows to a crawl after "slow"
    v_fast, v_slow = 2.2, 0.09; ts = t_slow
    if t < ts: dist = (t - w0) * v_fast
    else:
        ramp = min(1.0, (t - ts) / 1.2); dist = (ts - w0) * v_fast + (t - ts) * (v_fast + (v_slow - v_fast) * smooth(ramp) * 0.999)
    return -0.42 + (dist % 0.84)
for f in range(F(w0 - 0.5), F(w1 + 0.4)):
    t = (f - 1) / FPS; xp = pulse_x(t)
    for m_, x in zip(mols, XS):
        m_.location.x = x + 0.028 * math.exp(-((x - xp) / 0.05) ** 2); m_.keyframe_insert("location", index=0, frame=f)
    glow.location.x = xp; glow.keyframe_insert("location", index=0, frame=f)
flicker_in("why", w0 + 0.3, MZ - 0.05, MZ + 0.05, 0.6); BUILDS.append(w0 + 0.3)
label("AIR MOLECULES", 0.045, (0, 0, 0.62), "why_l1", CYAN2, t_mol)
spd = label("343 m/s", 0.095, (0, 0, 1.0), "why_l2", YEL, t_343)
def _spd(t):
    v = 343.0 if t < t_slow else 343.0 + (1.4 - 343.0) * smooth((t - t_slow) / 1.6)
    spd.data.body = f"{v:.0f} m/s" if v >= 9.95 else f"{v:.1f} m/s"
COUNTERS.append(_spd)
label("= WALKING PACE", 0.042, (0.04, 0, 0.91), "why_l3", WHITE, t_walk)
person("walker", hm("why_l3", YEL, 4.0, 0.6, 0.5), (-0.27, 0, 0.86), s=0.45)
for g in ("why", "why_l1", "why_l2", "why_l3"): fade_out(g, FLIPS[1] - 0.1)

# ================= page 2: TALK — words crawl across a room (2 s), then a football field (71 s)
t_friend, t_words, t_late, t_foot, t_min = W("talk", "friend"), W("talk", "words"), W("talk", "late"), W("talk", "football"), W("talk", "minute")
pa = person("A", hm("talk", YEL, 4.0, 0.55, 0.5), (-0.24, 0, 0.55)); pb = person("B", hm("talk", PINK, 4.0, 0.55, 0.5), (0.24, 0, 0.55))
flicker_in("talk", k0 + 0.25, 0.5, 0.78, 0.7); BUILDS.append(k0 + 0.25)
bub = empty("bubble", (-0.18, 0, 0.8)); bm_ = hm("talk_b", WHITE, 4.0, 0.35, 0.6)
cube("bbox", (0, 0, 0), (0.13, 0.01, 0.065), bm_, parent=bub, bevel=0.02).visible_shadow = False
text("HI!", 0.04, (0, -0.008, 0), hm("talk_b", YEL, 5.0, 0.9, 0.3), parent=bub, font=SANS)
for t, x in ((0, -0.18), (t_words, -0.18), (t_words + 2.0, 0.18)): bub.location.x = x; bub.keyframe_insert("location", index=0, frame=F(t))
lin(bub)
flicker_in("talk_b", t_words - 0.1, 0.74, 0.86, 0.3); fade_out("talk_b", t_words + 2.35); BUILDS.append(t_words - 0.1)
label("2 SECONDS LATE", 0.05, (0, 0, 0.98), "talk_l1", YEL, t_late); fade_out("talk_l1", t_foot - 0.15)
ck, ckh = clock("clock1", hm("talk_l1", YEL, 4.0, 0.8, 0.3, scan=False), (0, 0, 0.9)); spin_hand(ckh, t_words, t_words + 2.0, 2)
# football field
fld = empty("field", (0, 0, 0.5)); fm = hm("talk_f", GREEN, 3.0, 0.12, 0.4)
cube("turf", (0, 0, 0), (0.74, 0.3, 0.004), fm, parent=fld).visible_shadow = False
lm_ = hm("talk_f", (0.85, 1.0, 0.85), 3.5, 0.9, 0.2, scan=False)
for i in range(11): cube("yard", (-0.33 + 0.066 * i, 0, 0.004), (0.004, 0.28, 0.003), lm_, parent=fld).visible_shadow = False
flicker_in("talk_f", t_foot - 0.1, 0.45, 0.55, 0.4); BUILDS.append(t_foot - 0.1)
for p_, x1 in ((pa, -0.36), (pb, 0.36)):
    for t, x in ((0, p_.location.x), (t_foot, p_.location.x), (t_foot + 0.6, x1)): p_.location.x = x; p_.keyframe_insert("location", index=0, frame=F(t))
label("100 m", 0.045, (0, 0, 0.62), "talk_l2", WHITE, t_foot + 0.3)
cnt = label("0 SEC", 0.09, (0, 0, 0.98), "talk_l3", YEL, t_foot + 0.45)
t_c0, t_c1 = t_foot + 0.6, t_min + 0.3
def _cnt(t): cnt.data.body = f"{int(round(71 * smooth((t - t_c0) / (t_c1 - t_c0))))} SEC"
COUNTERS.append(_cnt)
bub2 = empty("bubble2", (-0.3, 0, 0.8)); b2m = hm("talk_l3", WHITE, 4.0, 0.35, 0.6)
cube("bbox", (0, 0, 0), (0.14, 0.01, 0.065), b2m, parent=bub2, bevel=0.02).visible_shadow = False
text("HEY!", 0.04, (0, -0.008, 0), hm("talk_l3", YEL, 5.0, 0.9, 0.3), parent=bub2, font=SANS)
for t, x in ((0, -0.3), (t_c0, -0.3), (t_c1, 0.3)): bub2.location.x = x; bub2.keyframe_insert("location", index=0, frame=F(t))
lin(bub2)
for g in ("talk", "talk_f", "talk_l2", "talk_l3"): fade_out(g, FLIPS[2] - 0.1)

# ================= page 3: STORM — lightning, then the thunder ring crawls 2 km: 24 minutes
t_storm, t_km, t_flash = W("storm", "storm"), W("storm", "kilometers"), W("storm", "lightning") + 0.1
T_TH = W("storm", "later") + 0.7  # thunder arrives
gm_ = hm("storm", CYAN, 2.6, 0.08, 0.4)
bpy.ops.mesh.primitive_grid_add(x_subdivisions=16, y_subdivisions=8, size=1, location=(0, 0, 0.5)); gr = bpy.context.object
gr.scale = (0.78, 0.36, 1); bpy.ops.object.transform_apply(location=False, rotation=False, scale=True); finish(gr, None, None, True); wire(gr, gm_, 0.002)
bmat = hm("storm", (0.75, 0.9, 1.0), 3.5, 0.4, 0.6)
TOWN = []
for i, (x, y, h) in enumerate(((0.2, -0.05, 0.07), (0.25, 0.04, 0.11), (0.3, -0.06, 0.05), (0.33, 0.05, 0.09), (0.22, 0.08, 0.05), (0.28, -0.12, 0.06))):
    TOWN.append(cube("bld", (x, y, 0.5 + h / 2), (0.04, 0.04, h), bmat))
for b_ in TOWN: b_.visible_shadow = False
cm2 = hm("storm", (0.7, 0.75, 0.85), 2.8, 0.3, 0.6)
for (x, z, r) in ((-0.3, 0.88, 0.06), (-0.24, 0.9, 0.07), (-0.18, 0.88, 0.055), (-0.27, 0.93, 0.05), (-0.21, 0.94, 0.05), (-0.34, 0.86, 0.04)):
    sphere("cloud", (x, 0, z), r, cm2, seg=20, holo=True)
flicker_in("storm", s0 + 0.25, 0.45, 1.0, 0.9); BUILDS.append(s0 + 0.25)
bolt_m = hm("bolt", (1.0, 0.95, 0.6), 9.0, 1.0, 0.0, scan=False)
pts = [(-0.24, 0.84), (-0.27, 0.76), (-0.22, 0.7), (-0.26, 0.62), (-0.22, 0.55), (-0.25, 0.5)]
for p, q in zip(pts, pts[1:]): rod("bolt", (p[0], 0, p[1]), (q[0], 0, q[1]), 0.005, bolt_m)
fade("bolt", [(0, 0), (t_flash - 0.02, 0), (t_flash, 1.0), (t_flash + 0.08, 0.2), (t_flash + 0.14, 1.0), (t_flash + 0.45, 0)])
for t, e in ((t_flash - 0.02, 9), (t_flash, 70), (t_flash + 0.08, 15), (t_flash + 0.14, 60), (t_flash + 0.5, 9)):
    holo_l.energy = e; holo_l.keyframe_insert("energy", frame=F(t))
km = hm("storm_l1", YEL, 4.0, 0.8, 0.2, scan=False)
for i in range(9): rod("dash", (-0.2 + i * 0.05, 0, 0.53), (-0.2 + i * 0.05 + 0.025, 0, 0.53), 0.0025, km)
label("2 KM", 0.05, (0, 0, 0.58), "storm_l1", YEL, t_km)
ring = torus("ring", (-0.25, 0, 0.505), 0.5, 0.0035, hm("ring", (0.75, 0.95, 1.0), 6.0, 1.0, 0.0, scan=False))
for t, s in ((0, 0.02), (t_flash, 0.02), (T_TH, 1.0)): ring.scale = (s, s, 1); ring.keyframe_insert("scale", frame=F(t))
lin(ring)
fade("ring", [(0, 0), (t_flash, 0), (t_flash + 0.1, 1.0), (T_TH + 0.2, 1.0), (T_TH + 0.6, 0)])
tcl = label("00:00", 0.09, (0, 0, 1.07), "storm_l2", WHITE, t_flash + 0.2)
def _tcl(t):
    m = 24 * 60 * smooth(min(1.0, max(0.0, (t - t_flash) / (T_TH - t_flash)))) ** 0.85 if t > t_flash else 0
    tcl.data.body = f"{int(m // 60):02d}:{int(m % 60):02d}"
COUNTERS.append(_tcl)
label("THUNDER!", 0.07, (0.25, 0, 0.75), "storm_l3", YEL, T_TH)
for b_ in TOWN:  # shake when the thunder hits
    z0 = b_.location.z
    for t, dz in ((0, 0), (T_TH, 0), (T_TH + 0.05, 0.012), (T_TH + 0.1, -0.008), (T_TH + 0.16, 0.006), (T_TH + 0.25, 0)):
        b_.location.z = z0 + dz; b_.keyframe_insert("location", index=2, frame=F(t))
for g in ("storm", "storm_l1", "storm_l2", "storm_l3"): fade_out(g, FLIPS[3] - 0.1)

# ================= page 4: WIND — the breeze outruns sound; rings get swept downwind, upwind hears nothing
t_breeze, t_out, t_up = W("wind", "breeze"), W("wind", "outrun"), W("wind", "upwind")
wm = hm("wind", (0.7, 0.9, 1.0), 4.0, 0.7, 0.3, scan=False)
for i in range(10):  # wind arrows streaming left -> right
    zz = 0.6 + (i % 5) * 0.08; arw = empty("arrow", (-0.4, 0, zz))
    rod("shaft", (-0.05, 0, 0), (0.03, 0, 0), 0.003, wm, arw)
    bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=0.012, radius2=0, depth=0.03, location=(0.045, 0, 0), rotation=(0, math.pi / 2, 0))
    finish(bpy.context.object, wm, arw, True)
    loop_keys(arw, 0, -0.42, 0.42, d0 - 1.6 + (i * 0.37) % 1.6, d1 + 0.5, 1.6)
flicker_in("wind", t_breeze - 0.2, 0.55, 1.0, 0.4); BUILDS.append(t_breeze - 0.2)
sp_ = person("speaker", hm("wind_p", YEL, 4.0, 0.55, 0.5), (0.0, 0, 0.55))
up_ = person("upwind", hm("wind_p", PINK, 4.0, 0.55, 0.5), (-0.3, 0, 0.55)); dn_ = person("downwind", hm("wind_p", GREEN, 4.0, 0.55, 0.5), (0.3, 0, 0.55))
flicker_in("wind_p", d0 + 0.3, 0.52, 0.76, 0.6); BUILDS.append(d0 + 0.3)
rm_ = hm("wind_r", (0.75, 0.95, 1.0), 6.0, 1.0, 0.0, scan=False)
for i in range(6):  # sound rings: grow slowly while the wind carries them right
    te = t_out + i * 0.7; o = torus("sring", (0, 0, 0.66), 0.09, 0.003, rm_, rot=(math.pi / 2, 0, 0))
    for t, s, x in ((0, 0.11, 0), (te, 0.11, 0), (te + 2.6, 1.0, 0.3)):
        o.scale = (s, s, s); o.keyframe_insert("scale", frame=F(t)); o.location.x = x; o.keyframe_insert("location", index=0, frame=F(t))
    for t, h in ((0, True), (te - 0.02, True), (te, False), (te + 2.6, True)): o.hide_render = h; o.keyframe_insert("hide_render", frame=F(t))
    lin(o)
flicker_in("wind_r", t_out - 0.1, 0.5, 0.9, 0.1)
label("CAN'T HEAR YOU", 0.04, (-0.3, 0, 0.82), "wind_l1", (1.0, 0.4, 0.3), t_up)
label("WIND  >  SOUND", 0.06, (0, 0, 1.02), "wind_l2", YEL, t_out)
for g in ("wind", "wind_p", "wind_r", "wind_l1", "wind_l2"): fade_out(g, FLIPS[4] - 0.1)

# ================= page 5: BOOM — a jogger, a bike, a car: each faster than sound -> shock cones + sonic booms
t_jog, t_bar, t_run, t_bike, t_car, t_sonic = (W("boom", w) for w in ("jogs", "barrier", "runners", "bikes", "cars", "sonic"))
rd = hm("boom", CYAN, 2.6, 0.1, 0.4)
cube("road", (0, 0, 0.5), (0.8, 0.14, 0.004), rd).visible_shadow = False
for i in range(8): cube("lane", (-0.35 + i * 0.1, 0, 0.503), (0.04, 0.006, 0.002), hm("boom", WHITE, 3.0, 0.9, 0.1, scan=False)).visible_shadow = False
flicker_in("boom", o0 + 0.25, 0.45, 0.55, 0.4); BUILDS.append(o0 + 0.25)
def mach(parent, g, L=0.2, R=0.11, x0=-0.01):
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=R, radius2=0.0, depth=L, end_fill_type="NOTHING", location=(x0 - L / 2, 0, 0.09), rotation=(0, math.pi / 2, 0))
    c_ = finish(bpy.context.object, hm(g, (1.0, 0.92, 0.6), 2.5, 0.06, 0.35, scan=False), parent, True)
    wire(c_, hm(g, (1.0, 0.95, 0.75), 5.0, 0.9, 0.1, scan=False), 0.0025); return c_
def cross(obj, t0, dur):
    for t, x in ((0, -0.5), (t0, -0.5), (t0 + dur, 0.5)): obj.location.x = x; obj.keyframe_insert("location", index=0, frame=F(t))
    lin(obj)
VEH = [("jogger", t_jog - 0.1, 2.2, YEL), ("runner2", t_run - 0.1, 1.6, YEL), ("bike", t_bike - 0.1, 1.3, GREEN), ("car", t_car - 0.15, 1.0, PINK)]
BOOMS = []
for nm, tc, dur, colr in VEH:
    g = "v_" + nm; vm = hm(g, colr, 4.0, 0.55, 0.5); r = empty(nm, (-0.5, 0, 0.5))
    if nm in ("jogger", "runner2"):
        p_ = person("p", vm, (0, 0, 0), r, 0.6); p_.rotation_euler.y = -0.25
    elif nm == "bike":
        for x in (-0.035, 0.035): torus("wheel", (x, 0, 0.025), 0.022, 0.003, vm, parent=r, rot=(math.pi / 2, 0, 0))
        rod("frame", (-0.035, 0, 0.025), (0.035, 0, 0.025), 0.003, vm, r); person("rider", vm, (0, 0, 0.03), r, 0.45)
    else:
        cube("body", (0, 0, 0.03), (0.11, 0.05, 0.03), vm, parent=r, bevel=0.008).visible_shadow = False
        cube("cab", (-0.01, 0, 0.055), (0.06, 0.045, 0.025), vm, parent=r, bevel=0.008).visible_shadow = False
        for x in (-0.035, 0.035): torus("wheel", (x, 0, 0.013), 0.012, 0.004, vm, parent=r, rot=(math.pi / 2, 0, 0))
    mach(r, g + "_c", L=0.24 if nm != "car" else 0.32, R=0.1 if nm != "car" else 0.14)
    cross(r, tc, dur)
    fade(g, [(0, 0), (tc, 0), (tc + 0.1, 1), (tc + dur - 0.1, 1), (tc + dur, 0)]); fade(g + "_c", [(0, 0), (tc + 0.2, 0), (tc + 0.3, 1), (tc + dur - 0.1, 1), (tc + dur, 0)])
    BOOMS.append(tc + 0.35 if nm != "jogger" else t_bar)
bm2 = hm("booms", (1.0, 0.9, 0.5), 5.0, 1.0, 0.1, scan=False)
for i, (tb_, x, z) in enumerate(((t_bar, -0.05, 0.86), (t_sonic, -0.2, 0.95), (t_sonic + 0.35, 0.18, 1.02), (t_sonic + 0.7, 0.0, 0.8))):
    o = text("BOOM!", 0.06 + 0.012 * i, (x, 0, z), bm2, font=SANS)
    for t, s in ((0, 0.01), (tb_, 0.01), (tb_ + 0.12, 1.25), (tb_ + 0.25, 1.0), (tb_ + 1.0, 1.0), (tb_ + 1.3, 0.01)): o.scale = (s, s, s); o.keyframe_insert("scale", frame=F(t))
    boom_ring("bring", hm("booms", WHITE, 5.0, 1.0, 0.0, scan=False), (x, 0, z), tb_, 0.12)
    BOOMS.append(tb_) if i else None
fade("booms", [(0, 0), (t_bar - 0.05, 0), (t_bar, 1.0), (FLIPS[5] - 0.1, 1.0), (FLIPS[5] + 0.2, 0)])
label("3 m/s  >  1.4 m/s", 0.05, (0, 0, 1.08), "boom_l1", YEL, t_bar - 0.3)
for g in ("boom", "boom_l1"): fade_out(g, FLIPS[5] - 0.1)

# ================= page 6: END — an ultracold atom cloud where sound really crawls; snail for scale; the question
t_sci, t_slow2, t_atoms, t_cold, t_surv = W("end", "scientists"), W("end", "slow"), W("end", "atoms"), W("end", "colder"), W("end", "survive")
am = hm("atoms", (0.55, 0.85, 1.0), 4.5, 0.6, 0.5, scan=False); ATOMS = []
for i in range(46):
    u, v_, rr = rnd.uniform(0, 6.283), rnd.uniform(-1, 1), 0.1 * rnd.random() ** 0.5
    p = (rr * math.sqrt(1 - v_ * v_) * math.cos(u), rr * math.sqrt(1 - v_ * v_) * math.sin(u) * 0.5, 0.74 + rr * v_)
    ATOMS.append(sphere("atom", p, rnd.uniform(0.006, 0.01), am, seg=10, holo=True))
for a_ in ATOMS:  # slow shiver
    base = tuple(a_.location)
    for f in range(F(n0 - 0.3), NF + 1, 6):
        a_.location = (base[0] + rnd.uniform(-0.003, 0.003), base[1], base[2] + rnd.uniform(-0.003, 0.003)); a_.keyframe_insert("location", frame=f)
sphere("cloudhalo", (0, 0, 0.74), 0.14, hm("atoms", CYAN, 2.0, 0.0, 0.35, scan=False), seg=32, holo=True)
flicker_in("atoms", t_sci, 0.6, 0.9, 0.6); BUILDS.append(t_sci)
label("SOUND: ~1 mm/s", 0.05, (0, 0, 0.98), "end_l1", YEL, t_slow2)
label("-273 °C", 0.06, (0, 0, 0.57), "end_l2", CYAN2, t_cold)
sn = empty("snail", (0.26, 0, 0.6)); snm = hm("end_l3", (1.0, 0.7, 0.4), 4.0, 0.5, 0.6)
sphere("shell", (0, 0, 0.03), 0.028, snm, parent=sn, seg=20, holo=True); torus("spiral", (0, -0.026, 0.03), 0.014, 0.003, snm, parent=sn, rot=(math.pi / 2, 0, 0))
rod("body", (-0.045, 0, 0.006), (0.04, 0, 0.006), 0.009, snm, sn)
for sx in (0.035, 0.045): rod("eye", (sx, 0, 0.01), (sx + 0.006, 0, 0.035), 0.002, snm, sn)
label("slower than a snail", 0.03, (0.26, 0, 0.53), "end_l3", (1.0, 0.7, 0.4), t_atoms + 0.4)
label("COULD YOU\nSURVIVE?", 0.08, (0, 0, 1.12), "end_l4", (1.0, 0.45, 0.35), t_surv - 0.2)
tc0 = t_close - 0.9
for g in ("atoms", "end_l1", "end_l2", "end_l3", "end_l4"):
    reveal(g, [(tc0, 1.25), (tc0 + 1.1, 0.3)])
    for mult, _ in PAGES[g]: key_sock(mult.outputs[0], F(tc0 + 1.15), 1.0); key_sock(mult.outputs[0], F(tc0 + 1.25), 0.0)

# ================= Leo
build_leo()
animate_leo([(t_title - 0.1, "smile"), (t_title + 0.2, "oh"), (t_title + 1.6, "smile"), (t_flash - 0.3, "smile"), (t_flash, "flat"),
             (T_TH - 0.05, "flat"), (T_TH + 0.1, "oh"), (T_TH + 1.8, "smile"), (t_bar - 0.1, "smile"), (t_bar + 0.1, "oh"), (t_bar + 1.2, "smile"),
             (t_sonic, "oh"), (t_sonic + 1.4, "smile"), (t_cold, "oh"), (t_cold + 1.2, "smile")],
            [(0, 0), (0.6, 0), (beam_on, -0.15), (t_title, -0.38), (FLIPS[2], -0.38), (s0 + 0.5, -0.5), (T_TH, -0.5), (T_TH + 0.4, -0.3), (END - 2.4, -0.3), (END - 1.6, 0)],
            flinches=(T_TH,), turn=(0.2, 1.0))
build_lights()

# ================= camera: front views of each page, a cut to Leo's face when the thunder finally hits
CU0, CU1 = T_TH + 0.05, T_TH + 1.35
keys = [(0.0, (0.75, -1.9, 0.6), (0.2, -0.2, 0.2)), (1.6, (0.15, -2.2, 0.95), (0, 0, 0.72)),
        (w0 + 0.5, (-0.15, -2.0, 0.95), (0, 0, 0.78)), (w1 - 0.5, (0.15, -1.85, 0.92), (0, 0, 0.8)),
        (k0 + 0.5, (-0.12, -2.05, 1.0), (0, 0, 0.74)), (k1 - 0.5, (0.12, -1.95, 0.95), (0, 0, 0.74)),
        (s0 + 0.5, (-0.15, -2.0, 1.05), (0, 0, 0.74)), (CU0 - 1.0 / FPS, (0.05, -1.85, 1.0), (0, 0, 0.74)),
        (CU0, *LEO_CU[0]), (CU1, *LEO_CU[1]), (CU1 + 1.0 / FPS, (0.1, -1.95, 1.0), (0, 0, 0.74)),
        (d0 + 0.5, (-0.12, -2.0, 1.0), (0, 0, 0.74)), (d1 - 0.5, (0.12, -1.9, 0.98), (0, 0, 0.76)),
        (o0 + 0.5, (-0.1, -1.95, 0.95), (0, 0, 0.72)), (o1 - 0.5, (0.12, -1.85, 0.92), (0, 0, 0.76)),
        (n0 + 0.5, (-0.08, -1.75, 0.95), (0, 0, 0.8)), (t_close - 0.6, (0.08, -1.85, 0.9), (0, 0, 0.78)),
        (END, (0.6, -2.0, 0.6), (0.25, -0.35, 0.18))]
build_camera(keys)
for fn_, g_, k_ in DEFER: fn_(g_, k_)

finish_scene({"beam_on": beam_on, "beam_off": beam_off, "open": t_open, "close": t_close, "flips": FLIPS, "builds": sorted(BUILDS),
              "flash": t_flash, "thunder": T_TH, "ticks": [t_flash + 0.2, T_TH], "wind": [t_breeze - 0.3, d1 + 0.3],
              "chirps": [t_words + 2.0, t_c1], "booms": sorted(BOOMS), "whooshes": [tc for _, tc, _, _ in VEH],
              "duck": [[t_flash, T_TH]], "derez": tc0, "cold_src": t_flash - 0.5, "cu": [CU0, CU1]})
