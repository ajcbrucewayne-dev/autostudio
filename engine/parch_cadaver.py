"""Inkbound History #4 (parchment): The Cadaver Synod, Rome, 897.

python3 engine/parch_cadaver.py out.mp4 | out_dir --stills t ...
Facts (checked, hedged): Jan 897, Pope Stephen VI had his predecessor Pope Formosus (died 896) exhumed and tried in the Lateran basilica;
the corpse was dressed in papal vestments and set on a throne, a deacon answered for it; found guilty, stripped of vestments, the
fingers of blessing reportedly cut off, and thrown into the Tiber; factional politics (Formosus had crowned Arnulf; Stephen's faction
backed Spoleto); Stephen was deposed, imprisoned and strangled later in 897; Theodore II annulled the synod; John IX later prohibited
trials of the dead.
"""
import math, os, sys, subprocess
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parchment as pm
import parch_dancing as pd
from parchment import (W, H, FPS, SR, INK, RED, SEPIA, clamp, ease, ease_out, Ink, figure, dance_pose, STAND)
pm.EXPR["angry"] = dict(open=0.95, pupil=0.4, brow=-1.0, curve=-0.55, mopen=0.65, bags=0, sweat=0.3)   # shouting
GOLD = (0.78, 0.6, 0.18); STONE = (0.55, 0.5, 0.42); WATER = (0.25, 0.35, 0.42)

VOICE, SPEED = "bm_george", 1.0
BEATS = [
    ("cold", "A pope dug up a dead man, dressed him in robes... and put the corpse on trial.", 0.2),
    ("rewind", "And the dead man lost.", 0.2),
    ("start", "Rome, eight ninety-seven. Pope Formosus had been dead for about nine months, when his successor, Stephen the Sixth, had him dug up.", 0.0),
    ("throne", "The rotting body was dressed in papal robes, and propped up on a throne.", 0.3),
    ("trial", "Stephen screamed accusations at it. A terrified deacon had to answer for the corpse.", 0.3),
    ("verdict", "Guilty. The body was stripped, the fingers he blessed with were reportedly cut off, and it was thrown into the river Tiber.", 0.4),
    ("why", "Why? Rome was torn between rival factions, and Formosus had backed the other side.", 0.2),
    ("twist", "But Rome turned on Stephen. Within months, he was thrown in prison... and strangled.", 0.5),
    ("impact", "Its impact? Later popes cancelled the trial, and banned putting the dead on trial ever again.", 0.2),
    ("end", "The dead pope was reburied with honours. Would you have dared to speak for the corpse?", 0.6),
]
STAMPS = {"start": "ROME · JANUARY 897", "throne": "THE ACCUSED", "trial": "THE CADAVER SYNOD", "verdict": "THE VERDICT", "why": "WHY?",
          "twist": "THE TWIST", "impact": "THE IMPACT", "end": "THE CADAVER SYNOD"}
pd.BEATS, pd.VOICE, pd.SPEED = BEATS, VOICE, SPEED
build_timeline, mk_W, cam_at, Ctx = pd.build_timeline, pd.mk_W, pd.cam_at, pd.Ctx
def lerp(a, b, u): return a + (b - a) * u

# ------------------------------------------------------------------ props
def mitre(ink, x, y, s, p, a, col=GOLD):
    pts = [(x - 34 * s, y), (x - 26 * s, y - 70 * s), (x, y - 100 * s), (x + 26 * s, y - 70 * s), (x + 34 * s, y), (x - 34 * s, y)]
    ink.fill(pts, col, .75 * a * p); ink.stroke(pts, 3, p, INK, a, taper=False, dense=False); ink.line((x, y - 4), (x, y - 92 * s), 2, p, RED, a)
def pope(ink, x, y, h, pose, p, a, t, expr="angry", var=0, flip=False):
    figure(ink, x, y, h, pose, p, "man", a, expr=expr, t=t, var=var, flip=flip)
    mitre(ink, x + (0.02 * h if not flip else -0.02 * h), y - 0.93 * h, h / 560, p, a)
def throne(ink, x, y, s, p, a):
    R = pm.Reveal(p, 4); pr = R()
    back = [(x - 120 * s, y), (x - 120 * s, y - 520 * s), (x, y - 600 * s), (x + 120 * s, y - 520 * s), (x + 120 * s, y)]
    ink.fill(back, GOLD, .22 * a * pr); ink.hatch(back, pr, 90, 18, 1.4, INK, .25 * a); ink.stroke(back, 5, pr, INK, a, taper=False, dense=False)
    pr = R(); seat = [(x - 150 * s, y - 220 * s), (x + 150 * s, y - 220 * s), (x + 150 * s, y - 180 * s), (x - 150 * s, y - 180 * s), (x - 150 * s, y - 220 * s)]
    ink.fill(seat, RED, .5 * a * pr); ink.stroke(seat, 4, pr, INK, a, taper=False, dense=False)
    for lx in (-140, 140): ink.line((x + lx * s, y - 180 * s), (x + lx * s, y), 6, pr, INK, a)
def corpse(ink, x, y, h, p, a, t, robe=True, rot=0.0):
    sk = dict(STAND); sk.update(aL=-25, eL=-20, aR=25, eR=-20, head=-18 + 4 * math.sin(t * .7), hL=-80, kL=85, hR=-80, kR=85, lean=-6)
    if robe:
        rb = [(x - .2 * h, y - .62 * h), (x + .2 * h, y - .62 * h), (x + .3 * h, y - .05 * h), (x - .3 * h, y - .05 * h), (x - .2 * h, y - .62 * h)]
        ink.fill(rb, RED, .85 * a * p); ink.hatch(rb, p, 70, 10, 1.6, INK, .35 * a); ink.stroke(rb, 4, p, INK, a, taper=False, dense=False)
        ink.fill([(x - .04 * h, y - .62 * h), (x + .04 * h, y - .62 * h), (x + .05 * h, y - .05 * h), (x - .05 * h, y - .05 * h)], GOLD, .8 * a * p)
    figure(ink, x, y, h, sk, p, "skeleton", a, col=INK, rot=rot)
    hx, hy = x + .01 * h, y - .80 * h
    pm.skull(ink, hx, hy, .085 * h, p, a)                       # a clear, slightly tilted skull
    if robe: mitre(ink, hx, hy - .07 * h, h / 520, p, a)
    for k in range(3):                                   # flies
        an = t * (3 + k) + k * 2; ink.dot(x + math.cos(an) * .25 * h, y - .95 * h + math.sin(an * 1.3) * .1 * h, 4, INK, a * p)
def arches(ink, p, a):
    R = pm.Reveal(p, 5)
    for i, x in enumerate((150, 540, 930)):
        pr = R(); ink.stroke([(x - 150, 1500), (x - 150, 700), (x - 120, 600), (x, 540), (x + 120, 600), (x + 150, 700), (x + 150, 1500)], 4, pr, INK, a * .5, taper=False)
    pr = R(); ink.hatch([(0, 0), (W, 0), (W, 520), (0, 520)], pr, 0, 20, 1.4, INK, .25 * a)
def river(ink, y, p, a, t):
    w = [(60, y)] + [(60 + x, y + 10 * math.sin(x * .02 + t * 2)) for x in range(0, 960, 40)] + [(1020, y), (1020, y + 380), (60, y + 380)]
    ink.fill(w, WATER, .55 * a * p); ink.stroke(w[:-2], 3, p, INK, a)
    for k in range(6): ink.stroke([(100 + k * 160 + 30 * math.sin(t + k), y + 80 + k * 40), (160 + k * 160, y + 70 + k * 40), (220 + k * 160, y + 82 + k * 40)], 2.2, p, INK, a * .5)
def bars(ink, p, a):
    for k in range(8): ink.line((150 + k * 112, 520), (150 + k * 112, 520 + 1000 * p), 12, 1, INK, a)
    ink.line((120, 520), (960, 520), 14, p, INK, a); ink.line((120, 1520), (960, 1520), 14, p, INK, a)

# ------------------------------------------------------------------ cameras
def cams(Wt, B):
    C = {}
    C["cold"] = [(0, 540, 1050, 1.25), (Wt("cold", "corpse") - .3, 600, 980, 1.4), (Wt("cold", "trial") + .4, 560, 1000, 1.3),
                 (B["rewind"]["t0"] + .2, 600, 940, 1.5), (B["rewind"]["t1"], 540, 960, 1.0)]
    C["start"] = [(B["start"]["t0"], 540, 960, 1.0), (Wt("start", "Stephen"), 540, 1000, 1.05), (Wt("start", "dug") + .6, 540, 1100, 1.15)]
    C["throne"] = [(Wt("throne"), 540, 1060, 1.1), (Wt("throne", "throne") + .4, 540, 960, 1.15)]
    C["trial"] = [(Wt("trial"), 540, 1000, 1.0), (Wt("trial", "deacon") - .2, 540, 1040, 1.08)]
    C["verdict"] = [(Wt("verdict"), 540, 980, 1.05), (Wt("verdict", "fingers") - .2, 540, 1000, 1.08), (Wt("verdict", "Tiber") - .4, 540, 1100, 1.0)]
    C["why"] = [(Wt("why"), 540, 980, 1.0)]
    C["twist"] = [(Wt("twist"), 540, 1000, 1.02), (Wt("twist", "strangled") + .4, 540, 1000, 1.1)]
    C["impact"] = [(Wt("impact"), 540, 980, 1.03)]
    C["end"] = [(Wt("end"), 540, 1000, 1.0), (Wt("end", "Would"), 540, 1020, 1.1), (B["end"]["t1"] - .1, 540, 1060, 1.2)]
    return C

# ------------------------------------------------------------------ plates
def tableau(ink, t, p, a):
    """Frame 1: a robed corpse on a golden throne; a furious pope pointing at it; a cowering deacon."""
    arches(ink, p, a); pm.ground(ink, 1420, p, alpha=a, cobbles=False)
    throne(ink, 700, 1420, 1.0, p, a); corpse(ink, 700, 1240, 470, p, a, t)
    pose = dict(STAND); pose.update(aR=95 + 6 * math.sin(t * 7), eR=-5, aL=-20, lean=10 + 3 * math.sin(t * 7))
    pope(ink, 290, 1420, 520, pose, p, a, t, expr="angry", var=2)
    for k in range(3): ink.stroke([(420 + k * 20, 960 - k * 30), (470 + k * 30, 930 - k * 40)], 4, p, RED, a * (.5 + .5 * math.sin(t * 9 + k)))  # shouting lines

def plate_cold(c, Wt): tableau(c.ink, c.t, c.K, c.a)

def plate_start(c, Wt):
    ink, t, a = c.ink, c.t, c.a; t0 = Wt("start"); tn = Wt("start", "nine"); td = Wt("start", "dug")
    pm.ground(ink, 1300, c.P(t0, .8), alpha=a)
    tomb = [(300, 1300), (300, 1150), (780, 1150), (780, 1300)]; ink.fill(tomb, STONE, .5 * a * c.P(t0 + .2, .6)); ink.stroke(tomb + [tomb[0]], 5, c.P(t0 + .2, .6), INK, a, taper=False, dense=False)
    ink.text("FORMOSUS", 540, 1240, 54, INK, a, p=c.P(t0 + .6, .6))
    n = min(9, int(ease(clamp((t - tn + .2) / 1.4)) * 9.99)); ink.text(f"DEAD {n} MONTHS", 540, 520, 96, INK, a, p=c.P(tn - .2, .3))
    if t > td - .5:     # the lid slides open, two diggers
        u = ease(clamp((t - td + .3) / 1.4)); lid = [(300 + 300 * u, 1150), (780 + 300 * u, 1150), (780 + 300 * u, 1120), (300 + 300 * u, 1120)]
        ink.fill(lid, STONE, .7 * a); ink.stroke(lid + [lid[0]], 4, 1, INK, a, taper=False, dense=False)
        for i, x in enumerate((200, 880)):
            pose = dict(STAND); pose.update(aL=-60, aR=-40, lean=20 if i == 0 else -20)
            figure(ink, x, 1300, 300, pose, c.P(td - .4, .5), "man", a, expr="fear", t=t, var=i + 3, flip=i == 1)
        ink.text("STEPHEN VI", 540, 640, 64, RED, a, p=c.P(Wt("start", "Stephen"), .5))

def plate_throne(c, Wt):
    ink, t, a = c.ink, c.t, c.a; t0 = Wt("throne"); tr = Wt("throne", "robes")
    arches(ink, c.P(t0, 1.0), a); pm.ground(ink, 1450, c.K, alpha=a, cobbles=False)
    throne(ink, 540, 1450, 1.15, c.P(t0, .8), a)
    corpse(ink, 540, 1250, 540, c.P(t0 + .2, .8), a, t, robe=t > tr - .2)
    ink.text("THE ACCUSED", 540, 470, 96, RED, a, p=c.P(Wt("throne", "throne"), .5))

def plate_trial(c, Wt):
    ink, t, a = c.ink, c.t, c.a; t0 = Wt("trial"); td = Wt("trial", "deacon")
    tableau(ink, t, 1.0, a)
    pose = dict(STAND); pose.update(aL=-60, eL=-90, aR=60, eR=-90, lean=-8 + 6 * math.sin(t * 11))
    figure(ink, 900, 1420, 300, pose, c.P(td - .3, .5), "man", a, expr="fear", t=t, var=6, flip=True)
    ink.text("THE DEACON", 900, 1530, 44, INK, a, p=c.P(td, .5))
    for k in range(4): ink.stroke([(860 + 15 * k, 1080 - 10 * k), (845 + 15 * k, 1050 - 10 * k)], 3, c.P(td + .2, .3), INK, a * .7)   # sweat

def plate_verdict(c, Wt):
    ink, t, a = c.ink, c.t, c.a; t0 = Wt("verdict"); tf = Wt("verdict", "fingers"); tt = Wt("verdict", "Tiber")
    aA = a * (1 - clamp((t - tt + .6) / .5))
    if aA > .01:
        throne(ink, 540, 1450, 1.15, c.K, aA); corpse(ink, 540, 1250, 540, c.K, aA, t, robe=t < Wt("verdict", "stripped") - .1)
        pm.stamp(ink, "GUILTY", 2.0, 620, 140, aA * clamp((t - t0 - .1) / .2))
        hx, hy = 760, 1080; hp = c.P(tf - .2, .5)                    # a hand raised in blessing, three fingers marked
        for k in range(3): ink.line((hx + k * 22, hy), (hx + k * 22, hy - 80), 10, hp, INK, aA); ink.line((hx - 20 + k * 22, hy - 40), (hx + 20 + k * 22, hy - 40), 4, c.P(tf + .2 + k * .15, .2), RED, aA)
    if t > tt - .8:
        river(ink, 1200, c.P(tt - .8, .6), a, t)
        u = ease(clamp((t - tt + .5) / 1.8)); figure(ink, 300 + 400 * u, 1260 + 20 * math.sin(t * 2), 260, dance_pose(0, 0, 0), c.P(tt - .5, .5), "skeleton", a, col=INK, rot=80)
        ink.text("THE TIBER", 540, 560, 100, INK, a, p=c.P(tt, .5))

def plate_why(c, Wt):
    ink, t, a = c.ink, c.t, c.a; t0 = Wt("why"); tr = Wt("why", "rival"); tb = Wt("why", "backed")
    for i, (x, lab, col) in enumerate([(300, "FACTION A", RED), (780, "FACTION B", INK)]):
        sh = [(x - 120, 820), (x + 120, 820), (x + 120, 1000), (x, 1120), (x - 120, 1000), (x - 120, 820)]
        ink.fill(sh, col, .35 * a * c.P(tr + i * .3, .5)); ink.stroke(sh, 5, c.P(tr + i * .3, .5), INK, a, taper=False, dense=False)
        ink.text(lab, x, 1220, 46, INK, a, p=c.P(tr + .3 + i * .3, .4))
    ink.line((420, 960), (660, 960), 10, c.P(tr + .8, .4), RED, a); ink.text("VS", 540, 940, 70, RED, a, p=c.P(tr + .8, .3))
    pope(ink, 780, 1600, 260, dict(STAND), c.P(tb - .2, .5), a, t, expr="neutral", var=1)
    ink.text("FORMOSUS", 780, 1660, 40, INK, a, p=c.P(tb, .4))
    ink.text("POLITICS", 540, 560, 110, RED, a, p=c.P(Wt("why", "Rome"), .5))

def plate_twist(c, Wt):
    ink, t, a = c.ink, c.t, c.a; t0 = Wt("twist"); tp = Wt("twist", "prison"); ts = Wt("twist", "strangled")
    pope(ink, 540, 1420, 520, dict(STAND, aL=-40, aR=40, head=-10), c.K, a, t, expr="fear" if t > tp else "angry", var=2)
    if t > tp - .3: bars(ink, ease(clamp((t - tp + .3) / .5)), a)
    ink.text("STEPHEN VI", 540, 470, 90, INK, a, p=c.P(t0, .5))
    ink.text("STRANGLED", 540, 600, 104, RED, a, p=c.P(ts, .5))
    if t > ts: ink.stroke([(420, 1080), (540, 1110), (660, 1080)], 8, c.P(ts, .4), RED, a)

def plate_impact(c, Wt):
    ink, t, a = c.ink, c.t, c.a; t0 = Wt("impact"); tc = Wt("impact", "cancelled"); tb = Wt("impact", "banned")
    doc = [(240, 700), (840, 700), (840, 1360), (240, 1360), (240, 700)]; pb = c.P(t0 + .2, .7)
    ink.fill(doc, SEPIA, .2 * a * pb); ink.stroke(doc, 4, pb, INK, a, taper=False, dense=False)
    for i in range(9): ink.stroke([(290, 790 + i * 52), (530 + 30 * (i % 3), 792 + i * 52), (790, 788 + i * 52)], 2.2, c.P(t0 + .4 + i * .08, .3), INK, a * .55)
    ink.line((270, 760), (810, 1300), 12, c.P(tc, .4), RED, a); ink.line((810, 760), (270, 1300), 12, c.P(tc + .2, .4), RED, a)
    ink.circle(700, 1260, 70, 6, c.P(tb, .5), RED, a)
    ink.text("TRIAL ANNULLED", 540, 500, 92, INK, a, p=c.P(tc, .5)); ink.text("NO MORE TRIALS OF THE DEAD", 540, 600, 50, RED, a, p=c.P(tb, .5))

def plate_end(c, Wt):
    ink, t, a = c.ink, c.t, c.a; t0 = Wt("end"); tq = Wt("end", "Would")
    aA = a * (1 - clamp((t - tq + .2) / .5))
    if aA > .01:
        arches(ink, c.K, aA); tomb = [(300, 1300), (300, 1150), (780, 1150), (780, 1300)]
        ink.fill(tomb, STONE, .5 * aA * c.K); ink.stroke(tomb + [tomb[0]], 5, c.K, INK, aA, taper=False, dense=False)
        ink.text("FORMOSUS", 540, 1240, 54, INK, aA, p=c.K); mitre(ink, 540, 1150, 1.3, c.P(t0 + .4, .5), aA)
        ink.text("REBURIED WITH HONOURS", 540, 560, 64, INK, aA, p=c.P(Wt("end", "reburied"), .5))
    if t > tq - .3:
        tableau(ink, t, c.P(tq - .3, .8), a); ink.text("?", 880, 520, 300, RED, a, p=c.P(tq + .3, .3))

PLATES = [("cold", plate_cold), ("start", plate_start), ("throne", plate_throne), ("trial", plate_trial), ("verdict", plate_verdict), ("why", plate_why),
          ("twist", plate_twist), ("impact", plate_impact), ("end", plate_end)]
FADE = 0.45

def draw_frame(ink, t, meta, Wt, B):
    import render
    global CAM
    if "CAM" not in globals(): CAM = cams(Wt, B)
    pm.BOIL[0] = int(t * 8)
    ink.clear()
    tr = Wt("rewind"); tr1 = B["rewind"]["t1"]
    starts = [(Wt(n) if n != "start" else B["start"]["t0"]) for n, _ in PLATES]; starts[0] = -1.0
    for i, (name, fn) in enumerate(PLATES):
        st = starts[i]; nxt = starts[i + 1] if i + 1 < len(PLATES) else 1e9
        if t < st - 0.01 or t > nxt + FADE: continue
        a = 1.0 if t < nxt else 0.0; K = 1.0
        if i + 1 < len(PLATES) and PLATES[i + 1][0] == "start": a = 1 - clamp((t - nxt) / FADE)
        if name == "cold": K = 1 - ease(clamp((t - tr1 + .6) / 1.0)); a = 1 - clamp((t - tr1) / FADE)
        cx, cy, z = cam_at(t, CAM[name])
        c = ink.ctx; c.save(); c.translate(W / 2, H * 0.5); c.scale(z, z); c.translate(-cx, -cy)
        fn(Ctx(ink, t, st, K, a), Wt); c.restore()
    for i, (name, _) in enumerate(PLATES):
        if name in ("cold", "start"): continue
        st = starts[i]
        if st - 0.3 <= t <= st + 0.4:
            r = 1400 * (ease_out((t - st + 0.3) / 0.3) if t < st else 1 - ease((t - st) / 0.4)); pm.blot(ink, 540, 950, r, i)
    hk_end = B["rewind"]["t0"] + 0.4; tn = B["end"]["t1"]
    if t < hk_end + 0.3 or t > tn - 0.5:
        al = 1 - clamp((t - hk_end) / 0.3) if t < hk_end + 0.3 else clamp((t - tn + 0.5) / 0.4)
        pulse = 1 + 0.03 * math.sin(t * 6)
        ink.text("A POPE PUT A CORPSE", W / 2, 205, 70, INK, al); ink.text("ON TRIAL", W / 2, 320, 110 * pulse, RED, al)
    for m in meta:
        s = STAMPS.get(m["name"])
        if not s: continue
        st = m["t0"]; en = m["t1"]
        if m["name"] == "end": en = min(en, B["end"]["t1"] - 0.8)
        if st <= t < en + 0.3: pm.stamp(ink, s, t - st, H * 0.085, 54, 1 - clamp((t - en) / 0.3))
    for m in meta:
        if m["s0"] - 0.05 <= t <= m["s1"] + 0.2:
            for g in render.build_groups([tuple(w) for w in m["words"]]):
                if g[0][1] <= t < g[-1][2] + 0.15: pm.caption(ink, g, t); break

def build_audio(meta, vo, Wt, B):
    n = len(vo); mus = pm.drone(n) * 0.5
    if os.environ.get("MUSIC"):
        from cartoon import music_track
        mp = os.environ["MUSIC"]; mp = mp if os.path.isabs(mp) else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", mp)
        mus = music_track(mp, n) * 0.7
    sfx = np.zeros(n, np.float32)
    for name, _ in PLATES:
        st = B[name]["t0"]; pm.place(sfx, pm.page_whoosh(hash(name) % 99), st - 0.25, 0.5); pm.place(sfx, pm.quill(1.8, hash(name) % 77), st, 0.35)
    pm.place(sfx, pm.thud(50, 1.4), 0.0, 0.9); pm.place(sfx, pm.thud(42, 1.8), Wt("cold", "trial"), 1.0)
    pm.place(sfx, pm.bell(147, 5.0), Wt("start", "dug"), 0.5); pm.place(sfx, pm.thud(40, 2.0), Wt("verdict", "Guilty"), 1.0)
    pm.place(sfx, pm.bell(196, 4.0), Wt("verdict", "Tiber"), 0.5); pm.place(sfx, pm.thud(60, 1.0), Wt("twist", "strangled"), 0.9)
    hop = 480; e = np.sqrt(np.convolve(vo ** 2, np.ones(hop) / hop, "same")); duck = np.convolve(1 - 0.45 * np.clip(e / 0.05, 0, 1), np.ones(4800) / 4800, "same")
    mix = vo * 1.0 + mus * 0.32 * duck + sfx * 0.55
    return (np.tanh(mix * 1.1) * 0.92).astype(np.float32)

def main():
    out = sys.argv[1]; stills = "--stills" in sys.argv
    work = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out", "parch"); os.makedirs(work, exist_ok=True)
    meta, vo = build_timeline(os.path.join(work, "cadaver_vo1"))
    Wt, B = mk_W(meta); total = len(vo) / SR
    paper = pm.make_paper(); glow = pm.glow_map(); ink = Ink()
    ink.clear(); pm.BOIL_AMP = 0; pm.border(ink); paper = pm.bake(paper, ink); pm.BOIL_AMP = 1.3
    if stills:
        from PIL import Image
        os.makedirs(out, exist_ok=True)
        for s in sys.argv[sys.argv.index("--stills") + 1:]:
            t = float(s); draw_frame(ink, t, meta, Wt, B)
            Image.fromarray(pm.composite(paper, glow, ink, t)).resize((540, 960)).save(os.path.join(out, f"t{t:06.2f}.png"))
        print("beats:", [(m["name"], round(m["t0"], 2)) for m in meta], "total", round(total, 1)); return
    import soundfile as sf
    wav = os.path.join(work, "cadaver_mix.wav"); sf.write(wav, build_audio(meta, vo, Wt, B), SR)
    nf = int(total * FPS)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for fi in range(nf):
        t = fi / FPS; draw_frame(ink, t, meta, Wt, B)
        ff.stdin.write(pm.composite(paper, glow, ink, t).tobytes())
        if fi % 150 == 0: print(f"{fi}/{nf}", flush=True)
    ff.stdin.close(); ff.wait(); print("DONE", out, round(total, 1))

if __name__ == "__main__":
    main()
