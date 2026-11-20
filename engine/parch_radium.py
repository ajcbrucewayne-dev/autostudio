"""Inkbound History #3 (parchment): The Radium Girls.

python3 engine/parch_radium.py out.mp4                      full render
python3 engine/parch_radium.py out_dir --stills 1.0 5.2 ... PNG stills
Facts (checked, hedged): from ~1917 the US Radium Corporation in Orange, New Jersey hired young women to paint watch dials with radium
paint; they were taught to point brushes with their lips ("lip, dip, paint") and told it was harmless; some reportedly painted nails and
teeth and glowed in the dark; victims suffered "radium jaw" (bone necrosis) and many died; the company denied responsibility and its
lawyers used delays, apparently hoping the plaintiffs would die; in 1927 five women led by Grace Fryer sued; settled in 1928 ($10,000
each + $600/yr); several died within a few years; the case is credited with improving industrial safety and workers' right to sue.
"""
import math, os, sys, subprocess
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parchment as pm
import parch_dancing as pd
from parchment import (W, H, FPS, SR, INK, RED, SEPIA, clamp, ease, ease_out, Ink, figure, dance_pose, STAND)
GLOW = (0.32, 0.86, 0.38)                               # radium green

VOICE, SPEED = "bm_george", 1.0
BEATS = [
    ("cold", "They painted glowing watches... and were told to lick the poison off their brushes.", 0.2),
    ("rewind", "And their bosses swore it was safe.", 0.1),
    ("start", "New Jersey, nineteen seventeen. Young women were hired to paint watch dials with a glowing new wonder: radium.", 0.0),
    ("lip", "To keep their brushes sharp, they were taught three words. Lip. Dip. Paint.", 0.3),
    ("safe", "Some reportedly painted their nails and teeth for fun... and walking home at night, they glowed.", 0.3),
    ("jaw", "Then their teeth began to fall out. Their jawbones crumbled. Doctors called it radium jaw.", 0.6),
    ("cover", "The company denied everything, and dragged the case out, apparently hoping the women would die first.", 0.2),
    ("trial", "In nineteen twenty-seven, five dying women sued anyway. They won a settlement, but several died within a few years.", 0.3),
    ("impact", "Its impact? Their fight helped workers win the right to sue over poisonous jobs, and pushed new safety rules.", 0.2),
    ("end", "It's said their graves are still radioactive today. Would you have trusted the glow?", 0.6),
]
STAMPS = {"start": "ORANGE, NEW JERSEY · 1917", "lip": "LIP · DIP · PAINT", "safe": "\"HARMLESS\"", "jaw": "RADIUM JAW", "cover": "THE COVER-UP",
          "trial": "1927 · THE LAWSUIT", "impact": "THE IMPACT", "end": "THE RADIUM GIRLS"}
pd.BEATS, pd.VOICE, pd.SPEED = BEATS, VOICE, SPEED
build_timeline, mk_W, cam_at, Ctx = pd.build_timeline, pd.mk_W, pd.cam_at, pd.Ctx

# ------------------------------------------------------------------ props
def halo(ink, x, y, r, a, t=0.0):
    """Soft radium glow: stacked translucent green discs + a few sparks."""
    if a <= 0.01: return
    for k in range(5):
        rr = r * (1 - k * 0.17); n = 28; pts = [(x + math.cos(2 * math.pi * i / n) * rr, y + math.sin(2 * math.pi * i / n) * rr) for i in range(n)]
        ink.fill(pts, GLOW, 0.08 * a * (1 + k * 0.5))
    for i in range(6):
        an = i * 1.05 + t * 1.3; d = r * (0.8 + 0.3 * math.sin(t * 3 + i)); ink.dot(x + math.cos(an) * d, y + math.sin(an) * d, 4, GLOW, 0.8 * a)

def dial(ink, x, y, r, p, a, glow=1.0, t=0.0):
    """Watch dial with glowing numerals."""
    ink.circle(x, y, r, 4, p, INK, a); ink.circle(x, y, r * 0.86, 2, p, INK, a * 0.6)
    for i in range(12):
        an = i * math.pi / 6 - math.pi / 2; px, py = x + math.cos(an) * r * 0.7, y + math.sin(an) * r * 0.7
        ink.dot(px, py, max(2.5, r * 0.07), GLOW, a * clamp(p * 2 - i / 12) * glow)
    ink.line((x, y), (x + math.cos(t * .5) * r * .5, y + math.sin(t * .5) * r * .5), 3, p, INK, a); ink.line((x, y), (x, y - r * 0.6), 3, p, INK, a)

def table(ink, x0, x1, y, p, a):
    top = [(x0, y), (x1, y), (x1, y + 24), (x0, y + 24)]; ink.fill(top, SEPIA, 0.45 * a * p); ink.stroke(top + [top[0]], 4, p, INK, a, taper=False, dense=False)
    for lx in (x0 + 20, x1 - 20): ink.line((lx, y + 24), (lx, y + 170), 5, p, INK, a)

def painter(ink, x, y, h, p, a, t, var=0, lick=0.0, expr="neutral", glow=0.0):
    """A seated dial painter: brush in the right hand, raised to the lips when lick > 0."""
    pose = dict(STAND); pose.update(aR=lerp(40, 150, lick), eR=lerp(-70, -150, lick), aL=35, eL=-60, head=-6 + 6 * lick, hL=-70, kL=80, hR=-70, kR=80)
    figure(ink, x, y, h, pose, p, "woman", a, expr=expr, t=t, var=var)
    if glow > 0: halo(ink, x + 4, y - 0.82 * h, 0.13 * h, glow * a, t)

def lerp(a, b, u): return a + (b - a) * u

def factory(ink, x, y, s, p, a):
    R = pm.Reveal(p, 6)
    body = [(x - 330 * s, y), (x - 330 * s, y - 300 * s), (x + 330 * s, y - 300 * s), (x + 330 * s, y)]
    pr = R(); ink.fill(body, SEPIA, 0.3 * a * pr); ink.hatch(body, pr, 0, 18, 1.6, INK, 0.35 * a); ink.stroke(body + [body[0]], 4, pr, INK, a, taper=False, dense=False)
    pr = R()
    for i in range(5):                                     # saw-tooth roof
        bx = x - 330 * s + i * 132 * s; ink.stroke([(bx, y - 300 * s), (bx + 132 * s, y - 380 * s), (bx + 132 * s, y - 300 * s)], 4, pr, INK, a, taper=False)
    pr = R()
    for i in range(6):                                     # glowing windows
        wx = x - 280 * s + i * 100 * s; win = [(wx, y - 200 * s), (wx + 60 * s, y - 200 * s), (wx + 60 * s, y - 120 * s), (wx, y - 120 * s)]
        ink.fill(win, GLOW, 0.5 * a * pr); ink.stroke(win + [win[0]], 3, pr, INK, a, taper=False, dense=False)
    pr = R(); ink.stroke([(x + 250 * s, y - 380 * s), (x + 250 * s, y - 560 * s), (x + 300 * s, y - 560 * s), (x + 300 * s, y - 380 * s)], 4, pr, INK, a, taper=False)
    for k in range(4): ink.circle(x + 275 * s + 30 * math.sin(k), y - 600 * s - k * 50 * s, (22 + 8 * k) * s, 3, pr, INK, a * (0.8 - k * 0.15))

def jaw_skull(ink, x, y, r, crumble, p, a):
    pm.skull(ink, x, y, r, p, a)
    for i in range(6):                                     # falling teeth / bone chips
        u = clamp(crumble * 1.6 - i * 0.12);
        if u <= 0: continue
        tx = x - r * 0.5 + i * r * 0.2; ty = y + r * 0.9 + u * 260 + 20 * math.sin(i)
        ink.fill([(tx - 9, ty - 12), (tx + 9, ty - 12), (tx + 7, ty + 12), (tx - 7, ty + 12)], (0.95, 0.93, 0.86), a)
        ink.stroke([(tx - 9, ty - 12), (tx + 9, ty - 12), (tx + 7, ty + 12), (tx - 7, ty + 12), (tx - 9, ty - 12)], 2, 1, INK, a, taper=False, dense=False)
    for k in range(4): ink.stroke([(x - r * .6 + k * r * .4, y + r * .55), (x - r * .5 + k * r * .4, y + r * .8), (x - r * .65 + k * r * .4, y + r * 1.0)], 4, clamp(crumble * 2 - k * .2), RED, a)

def scales(ink, x, y, s, tilt, p, alpha=1.0):
    R = pm.Reveal(p, 4); pr = R()
    ink.line((x, y), (x, y - 320 * s), 5, pr, INK, alpha); ink.line((x - 90 * s, y), (x + 90 * s, y), 6, pr, INK, alpha)
    an = tilt * 0.35; dx, dy = math.cos(an) * 200 * s, math.sin(an) * 200 * s; pr = R()
    ink.line((x - dx, y - 320 * s + dy), (x + dx, y - 320 * s - dy), 5, pr, INK, alpha)
    for sx, sy in ((-dx, dy), (dx, -dy)):
        px, py = x + sx, y - 320 * s + sy; pr = R()
        ink.line((px, py), (px - 60 * s, py + 120 * s), 2.4, pr, INK, alpha); ink.line((px, py), (px + 60 * s, py + 120 * s), 2.4, pr, INK, alpha)
        ink.stroke([(px - 80 * s, py + 120 * s), (px, py + 150 * s), (px + 80 * s, py + 120 * s)], 4, pr, INK, alpha)

def hourglass(ink, x, y, s, u, p, a):
    pts = [(x - 60 * s, y - 120 * s), (x + 60 * s, y - 120 * s), (x, y), (x + 60 * s, y + 120 * s), (x - 60 * s, y + 120 * s), (x, y), (x - 60 * s, y - 120 * s)]
    ink.stroke(pts, 4, p, INK, a, taper=False, dense=False)
    top = 1 - u; ink.fill([(x - 50 * s * top, y - 110 * s * top), (x + 50 * s * top, y - 110 * s * top), (x, y)], SEPIA, 0.8 * a * p)
    ink.fill([(x - 50 * s * u, y + 110 * s), (x + 50 * s * u, y + 110 * s), (x, y + 110 * s * (1 - u))], SEPIA, 0.8 * a * p)

def bed(ink, x, y, p, a, t, var):
    frame = [(x - 150, y), (x + 150, y), (x + 150, y - 60), (x - 150, y - 60)]
    ink.fill(frame, (0.95, 0.93, 0.86), 0.9 * a * p); ink.stroke(frame + [frame[0]], 4, p, INK, a, taper=False, dense=False)
    ink.line((x - 150, y - 60), (x - 150, y - 160), 5, p, INK, a); ink.line((x - 150, y), (x - 150, y + 40), 5, p, INK, a); ink.line((x + 150, y), (x + 150, y + 40), 5, p, INK, a)
    figure(ink, x - 20, y - 60, 220, dance_pose(0, 0, 0), p, "woman", a, rot=-84, expr="tired", t=t, var=var)

def geiger(ink, x, y, s, p, a, t):
    box = [(x - 90 * s, y - 60 * s), (x + 90 * s, y - 60 * s), (x + 90 * s, y + 60 * s), (x - 90 * s, y + 60 * s)]
    ink.fill(box, SEPIA, 0.5 * a * p); ink.stroke(box + [box[0]], 4, p, INK, a, taper=False, dense=False)
    ink.circle(x - 30 * s, y, 32 * s, 3, p, INK, a); ink.line((x - 30 * s, y + 10 * s), (x - 30 * s + 26 * s * math.cos(-2.3 + 0.9 * math.sin(t * 9)), y + 10 * s + 26 * s * math.sin(-2.3 + 0.9 * math.sin(t * 9))), 3, p, RED, a)
    ink.stroke([(x + 90 * s, y), (x + 160 * s, y + 40 * s), (x + 200 * s, y + 140 * s)], 4, p, INK, a)

# ------------------------------------------------------------------ cameras
def cams(Wt, B):
    C = {}
    C["cold"] = [(0, 540, 1080, 1.35), (Wt("cold", "lick") - .3, 520, 980, 1.55), (Wt("cold", "poison") + .4, 540, 1040, 1.4),
                 (B["rewind"]["t0"] + .2, 540, 1040, 1.3), (B["rewind"]["t1"], 540, 960, 1.0)]
    C["start"] = [(B["start"]["t0"], 540, 960, 1.0), (Wt("start", "paint") - .2, 540, 1000, 1.05), (Wt("start", "radium") + .6, 540, 1080, 1.2)]
    C["lip"] = [(Wt("lip"), 540, 1000, 1.05), (Wt("lip", "Lip") - .2, 540, 960, 1.0)]
    C["safe"] = [(Wt("safe"), 540, 1040, 1.15), (Wt("safe", "night") - .3, 540, 1000, 1.05), (Wt("safe", "glowed") + .6, 540, 1060, 1.2)]
    C["jaw"] = [(Wt("jaw"), 540, 960, 1.0), (Wt("jaw", "crumbled"), 540, 1000, 1.15), (Wt("jaw", "radium") + .5, 540, 1000, 1.05)]
    C["cover"] = [(Wt("cover"), 540, 980, 1.05), (Wt("cover", "hoping") - .2, 540, 1000, 1.0)]
    C["trial"] = [(Wt("trial"), 540, 1000, 1.0), (Wt("trial", "settlement"), 540, 980, 1.02), (Wt("trial", "years") + .5, 540, 1040, 1.04)]
    C["impact"] = [(Wt("impact"), 540, 980, 1.05), (Wt("impact", "safety") + .4, 540, 980, 1.0)]
    C["end"] = [(Wt("end"), 540, 1000, 1.05), (Wt("end", "Would"), 540, 1040, 1.15), (B["end"]["t1"] - .1, 540, 1080, 1.3)]
    return C

# ------------------------------------------------------------------ plates
def tableau(ink, t, p, a, lick=1.0):
    """Frame 1: a young dial painter raising the glowing brush to her lips; a red skeleton's shadow behind her."""
    sk = dict(STAND); sk.update(aR=120, eR=-130, aL=40, eL=-60, head=-4)
    figure(ink, 640, 1420, 640, sk, p, "skeleton", a * 0.45, col=RED)
    table(ink, 120, 960, 1180, p, a)
    for i, (dx, dy) in enumerate([(-260, 0), (-110, 0)]): dial(ink, 540 + dx, 1150, 42, p, a, 1.0, t + i)
    painter(ink, 520, 1420, 640, p, a, t, var=0, lick=lick, expr="happy", glow=1.0)
    bx, by = 520 + 60, 1420 - 0.80 * 640 + 20                  # glowing brush tip at her lips
    halo(ink, bx, by, 34, a * p, t)

def plate_cold(c, Wt):
    tr = Wt("rewind"); lk = clamp(0.5 + 0.5 * math.sin(c.t * 2.2)) if c.t < tr else 1.0
    tableau(c.ink, c.t, c.K, c.a, lk)

def plate_start(c, Wt):
    ink, t, a = c.ink, c.t, c.a; t0 = Wt("start"); tw = Wt("start", "women"); tr = Wt("start", "radium")
    pm.ground(ink, 820, c.P(t0, .8), 60, W - 60, a, cobbles=False)
    factory(ink, 540, 820, 1.0, c.P(t0 + .2, 1.6), a)
    ink.text("U.S. RADIUM CORP.", 540, 470, 64, INK, a, p=c.P(t0 + .8, .6))
    table(ink, 80, 1000, 1240, c.P(tw - .3, .6), a)
    for i, x in enumerate((200, 420, 640, 860)):
        painter(ink, x, 1400, 300, c.P(tw + i * .2, .6), a, t, var=i + 1, lick=clamp(.5 + .5 * math.sin(t * 2 + i)) * .3, expr=["happy", "neutral", "happy", "neutral"][i])
        dial(ink, x + 70, 1215, 26, c.P(tw + .3 + i * .2, .5), a, 1.0, t)
    pr = c.P(tr - .2, .6); ink.text("RADIUM", 540, 1580, 110, GLOW, a, p=pr); halo(ink, 540, 1550, 220, 0.6 * a * pr, t)

def plate_lip(c, Wt):
    ink, t, a = c.ink, c.t, c.a; t0 = Wt("lip")
    ai = a * (1 - clamp((t - Wt("lip", "Lip") + .5) / .5))                 # intro: one big glowing brush
    if ai > .01:
        ink.line((380, 1300), (640, 760), 14, c.P(t0, .6), INK, ai); ink.fill([(640, 760), (690, 650), (700, 700), (660, 790)], SEPIA, .8 * ai * c.P(t0, .6)); halo(ink, 690, 660, 70, ai * c.P(t0 + .3, .5), t)
        ink.text("SHARP BRUSHES", 540, 520, 88, INK, ai, p=c.P(t0 + .3, .5))
    steps = [("Lip", "LIP", 200), ("Dip", "DIP", 540), ("Paint", "PAINT", 880)]
    for i, (w, lab, x) in enumerate(steps):
        tw = Wt("lip", w); p = c.P(tw - .2, .5); y = 900
        ink.circle(x, y, 140, 5, p, INK, a)
        if i == 0:   # lips around a brush tip
            ink.stroke([(x - 70, y), (x - 30, y - 30), (x, y - 18), (x + 30, y - 30), (x + 70, y), (x + 30, y + 30), (x - 30, y + 30), (x - 70, y)], 5, p, RED, a)
            ink.line((x, y - 110), (x, y - 5), 6, p, INK, a); halo(ink, x, y - 4, 22, a * p, t)
        elif i == 1: # paint pot
            pot = [(x - 60, y - 30), (x + 60, y - 30), (x + 50, y + 70), (x - 50, y + 70), (x - 60, y - 30)]
            ink.fill(pot, SEPIA, .5 * a * p); ink.stroke(pot, 4, p, INK, a, taper=False, dense=False)
            ink.fill([(x - 56, y - 30), (x + 56, y - 30), (x + 50, y - 10), (x - 50, y - 10)], GLOW, .8 * a * p); ink.line((x + 20, y - 120), (x, y - 20), 6, p, INK, a)
        else:        # a dial being painted
            dial(ink, x, y, 90, p, a, 1.0, t); ink.line((x + 110, y - 100), (x + 40, y - 40), 6, p, INK, a); halo(ink, x + 40, y - 40, 16, a * p, t)
        ink.text(lab, x, 1140, 90, RED if i == 0 else INK, a, p=c.P(tw, .4))
    for k in range(2): ink.text("→", 370 + k * 340, 910, 70, INK, a, p=c.P(Wt("lip", ["Dip", "Paint"][k]) - .3, .3))
    ink.text("× THOUSANDS", 540, 1330, 60, RED, a, p=c.P(Wt("lip", "Paint") + .6, .5))

def plate_safe(c, Wt):
    ink, t, a = c.ink, c.t, c.a; t0 = Wt("safe"); tn = Wt("safe", "night"); tg = Wt("safe", "glowed")
    dark = clamp((t - tn + .3) / .8)
    if dark < 1:
        aa = a * (1 - dark)
        for i, (x, k) in enumerate([(330, "woman"), (750, "woman")]):
            pose = dict(STAND); pose.update(aR=120, eR=-140, aL=-20, head=-8)
            figure(ink, x, 1420, 520, pose, c.P(t0 + i * .3, .6), k, aa, expr="happy", t=t, var=i + 2)
            halo(ink, x + 5, 1420 - .80 * 520 + 25, 30, aa * c.P(Wt("safe", "teeth"), .5), t)      # glowing teeth
            for f in range(4): ink.dot(x + 95 + f * 9, 1420 - 540 + f * 6, 7, GLOW, aa * c.P(Wt("safe", "nails"), .5))
        ink.text("NAILS & TEETH", 540, 520, 76, INK, aa, p=c.P(Wt("safe", "nails"), .5))
    if dark > 0:   # night street: the women glow green
        night = [(0, 0), (W, 0), (W, H), (0, H)]; ink.fill(night, (0.06, 0.07, 0.09), 0.82 * a * dark)
        pm.moon(ink, 820, 430, 48, c.K, a * dark)
        for i, x in enumerate((260, 540, 820)):
            u = (t - tn) * 30
            wk = dict(STAND); sw = math.sin(t * 4 + i) * 16; wk.update(hL=-sw, hR=sw, aL=-sw, aR=sw)
            figure(ink, x - 40 + u * .4, 1400, 360, wk, c.K, "woman", a * dark, col=GLOW, wash=False, expr="happy", t=t, var=i)
            halo(ink, x - 40 + u * .4, 1400 - 180, 140, a * dark * c.P(tg - .4, .6), t)
        ink.text("THEY GLOWED", 540, 600, 104, GLOW, a * dark, p=c.P(tg, .5))

def plate_jaw(c, Wt):
    ink, t, a = c.ink, c.t, c.a; t0 = Wt("jaw"); tc = Wt("jaw", "crumbled"); tr = Wt("jaw", "radium")
    jaw_skull(ink, 540, 860, 150, clamp((t - Wt("jaw", "teeth") + .2) / 2.4), c.P(t0, .8), a)
    halo(ink, 540, 900, 260, .35 * a * c.K, t)
    ink.text("RADIUM JAW", 540, 1360, 112, RED, a, p=c.P(tr - .1, .5))
    ink.text("BONE THAT CRUMBLES", 540, 1460, 50, INK, a, p=c.P(tr + .5, .5))

def plate_cover(c, Wt):
    ink, t, a = c.ink, c.t, c.a; t0 = Wt("cover"); td = Wt("cover", "denied"); th = Wt("cover", "hoping")
    for i, x in enumerate((330, 750)):                         # two men in suits behind a desk
        pose = dict(STAND); pose.update(aL=-30, eL=-50, aR=30, eR=-50)
        figure(ink, x, 1180, 420, pose, c.P(t0 + i * .25, .6), "man", a, expr="smug", t=t, var=5 + i)
    desk = [(120, 1180), (960, 1180), (960, 1240), (120, 1240)]; ink.fill(desk, SEPIA, .55 * a * c.K); ink.stroke(desk + [desk[0]], 4, c.K, INK, a, taper=False, dense=False)
    ink.text("DENIED", 540, 520, 120, RED, a, p=c.P(td, .4))
    hourglass(ink, 540, 1450, 1.1, clamp((t - Wt("cover", "dragged")) / 3), c.P(Wt("cover", "dragged") - .2, .5), a)
    ink.text("WAITING FOR THEM TO DIE", 540, 1700, 54, RED, a, p=c.P(th, .6))

def plate_trial(c, Wt):
    ink, t, a = c.ink, c.t, c.a; t0 = Wt("trial"); ts = Wt("trial", "settlement"); td = Wt("trial", "several")
    aA = a * (1 - clamp((t - ts + .2) / .5))
    if aA > .01:
        for i, x in enumerate((150, 345, 540, 735, 930)):
            figure(ink, x, 1300, 330, dict(STAND), c.P(t0 + .3 + i * .18, .5), "woman", aA, expr=["sad", "tired", "sad", "pain", "tired"][i], t=t, var=i)
        ink.text("5 WOMEN SUED", 540, 520, 100, INK, aA, p=c.P(Wt("trial", "five"), .5))
        ink.text("1927", 540, 640, 70, RED, aA, p=c.P(t0, .5))
    if t > ts - .3:
        scales(ink, 540, 1250, 1.2, ease(clamp((t - ts) / .8)), c.P(ts - .3, .8), a)
        ink.text("$10,000 EACH", 540, 520, 96, INK, a, p=c.P(ts, .5)); ink.text("SETTLED · 1928", 540, 620, 54, INK, a, p=c.P(ts + .4, .5))
        for i in range(3): pm.drip(ink, 330 + i * 210, 1150, 100, c.P(td + i * .25, .8), a)
        ink.text("SEVERAL DIED SOON AFTER", 540, 1330, 46, RED, a, p=c.P(td, .6))

def plate_impact(c, Wt):
    ink, t, a = c.ink, c.t, c.a; t0 = Wt("impact"); ts = Wt("impact", "sue"); tf = Wt("impact", "safety")
    doc = [(240, 700), (840, 700), (840, 1360), (240, 1360), (240, 700)]; pb = c.P(t0 + .2, .7)
    ink.fill(doc, SEPIA, .2 * a * pb); ink.stroke(doc, 4, pb, INK, a, taper=False, dense=False)
    for i in range(9): ink.stroke([(290, 790 + i * 52), (530 + 30 * (i % 3), 792 + i * 52), (790, 788 + i * 52)], 2.2, c.P(t0 + .4 + i * .08, .3), INK, a * .55)
    ink.circle(700, 1260, 70, 6, c.P(ts, .5), RED, a); ink.text("WON", 700, 1270, 40, RED, a, p=c.P(ts + .2, .4))
    ink.text("THE RIGHT TO SUE", 540, 500, 92, INK, a, p=c.P(ts - .2, .5))
    ink.text("+ NEW SAFETY RULES", 540, 600, 58, RED, a, p=c.P(tf, .5))

def plate_end(c, Wt):
    ink, t, a = c.ink, c.t, c.a; t0 = Wt("end"); tq = Wt("end", "Would"); tg = Wt("end", "graves")
    aA = a * (1 - clamp((t - tq + .2) / .5))
    if aA > .01:                                                # a gravestone with a ticking counter
        stone = [(400, 1300), (400, 900), (450, 840), (630, 840), (680, 900), (680, 1300)]
        ink.fill(stone, SEPIA, .5 * aA * c.P(t0, .6)); ink.stroke(stone + [stone[0]], 5, c.P(t0, .6), INK, aA, taper=False, dense=False)
        ink.text("R.I.P.", 540, 980, 70, INK, aA, p=c.P(t0 + .3, .5)); halo(ink, 540, 1240, 180, .55 * aA * c.P(tg, .6), t)
        pm.ground(ink, 1300, c.K, alpha=aA); geiger(ink, 820, 1150, 1.0, c.P(tg, .5), aA, t)
        ink.text("STILL RADIOACTIVE?", 540, 560, 84, GLOW, aA, p=c.P(tg + .4, .5))
    if t > tq - .3:
        tableau(ink, t, c.P(tq - .3, .8), a, 1.0)
        ink.text("?", 880, 520, 300, RED, a, p=c.P(tq + .3, .3))

PLATES = [("cold", plate_cold), ("start", plate_start), ("lip", plate_lip), ("safe", plate_safe), ("jaw", plate_jaw), ("cover", plate_cover),
          ("trial", plate_trial), ("impact", plate_impact), ("end", plate_end)]
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
        ink.text("THEY WERE TOLD", W / 2, 205, 62, INK, al); ink.text("TO LICK THE POISON", W / 2, 315, 76 * pulse, RED, al)
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
    pm.place(sfx, pm.thud(50, 1.4), 0.0, 0.9); pm.place(sfx, pm.thud(42, 1.8), Wt("cold", "poison"), 1.0)
    for w in ("Lip", "Dip", "Paint"): pm.place(sfx, pm.bell(392 if w == "Lip" else 330, 1.2), Wt("lip", w), 0.4)
    pm.place(sfx, pm.bell(523, 3.0), Wt("safe", "glowed"), 0.5); pm.place(sfx, pm.thud(40, 2.0), Wt("jaw", "crumbled"), 1.0)
    pm.place(sfx, pm.thud(60, 0.8), Wt("cover", "denied"), 0.7); pm.place(sfx, pm.bell(196, 5.0), Wt("trial", "several"), 0.6)
    rng = np.random.default_rng(1)
    for k in range(26):                                       # Geiger clicks at the grave
        tt = Wt("end", "graves") + rng.uniform(0, 3.2); i = int(tt * SR)
        if i + 200 < n: sfx[i:i + 200] += (rng.standard_normal(200) * np.exp(-np.arange(200) / 25) * 0.6).astype(np.float32)
    hop = 480; e = np.sqrt(np.convolve(vo ** 2, np.ones(hop) / hop, "same")); duck = np.convolve(1 - 0.45 * np.clip(e / 0.05, 0, 1), np.ones(4800) / 4800, "same")
    mix = vo * 1.0 + mus * 0.32 * duck + sfx * 0.55
    return (np.tanh(mix * 1.1) * 0.92).astype(np.float32)

def main():
    out = sys.argv[1]; stills = "--stills" in sys.argv
    work = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out", "parch"); os.makedirs(work, exist_ok=True)
    meta, vo = build_timeline(os.path.join(work, "radium_vo1"))
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
    wav = os.path.join(work, "radium_mix.wav"); sf.write(wav, build_audio(meta, vo, Wt, B), SR)
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
