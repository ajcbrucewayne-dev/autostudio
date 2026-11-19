"""Inkbound History #2 (parchment): The Great Molasses Flood, Boston, 1919.

python3 engine/parch_molasses.py out.mp4                      full render
python3 engine/parch_molasses.py out_dir --stills 1.0 5.2 ... PNG stills at given seconds
Facts (checked): 15 Jan 1919, Purity Distilling (USIA) tank, Commercial St, North End; ~2.3 million US gallons; wave up to ~25 ft (~7.6 m)
at ~35 mph; 21 dead, ~150 injured; the tank leaked and was painted brown; witnesses heard rivets shoot out; the molasses thickened as it
cooled; cause: thin, brittle steel, never properly tested; after a long lawsuit the company was held liable, and Massachusetts began
requiring engineers' and architects' sign-off on such plans; residents said the area smelled of molasses on hot days for decades.
"""
import math, os, sys, json, subprocess
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parchment as pm
import parch_dancing as pd                              # shared timeline/camera helpers
from parchment import (W, H, FPS, SR, INK, RED, SEPIA, clamp, ease, ease_out, Ink, figure, dance_pose, STAND)
MOL = (0.27, 0.13, 0.05)                                # molasses brown

VOICE, SPEED = "bm_george", 1.0
BEATS = [
    ("cold", "A wave of syrup, twenty-five feet high, tore through a city... and killed twenty-one people.", 0.2),
    ("rewind", "And it all started with one giant tank.", 0.1),
    ("start", "Boston, nineteen nineteen. A steel tank in the North End held over two million gallons of molasses.", 0.0),
    ("leak", "It leaked so badly, locals collected the drips. The company's fix? Paint the tank brown, to hide the stains.", 0.2),
    ("burst", "Then, on a mild January day, witnesses heard rivets shoot out like gunfire... and the tank split open.", 0.3),
    ("wave", "A wave of molasses up to twenty-five feet high raced through the streets, at around thirty-five miles an hour.", 0.0),
    ("cost", "It crushed buildings and swept people away. Twenty-one died, and about a hundred and fifty were hurt.", 0.6),
    ("rescue", "As the evening cooled, the syrup turned thick as glue, trapping rescuers and victims alike.", 0.2),
    ("why", "Why? The tank was rushed, never properly tested, and its steel was too thin and brittle.", 0.2),
    ("impact", "Its impact? The company was found responsible, and Massachusetts began requiring engineers to sign off on plans like these.", 0.2),
    ("end", "Locals said the street smelled sweet for decades. Would you have believed a flood of syrup?", 0.6),
]
STAMPS = {"start": "BOSTON · JANUARY 1919", "leak": "THE LEAK", "burst": "12:30 PM", "wave": "THE WAVE", "cost": "THE COST", "rescue": "THE RESCUE",
          "why": "WHY?", "impact": "THE IMPACT", "end": "THE GREAT MOLASSES FLOOD"}
pd.BEATS, pd.VOICE, pd.SPEED = BEATS, VOICE, SPEED      # build_timeline / mk_W read these
build_timeline, mk_W, cam_at, Ctx = pd.build_timeline, pd.mk_W, pd.cam_at, pd.Ctx

# ------------------------------------------------------------------ props
def tank(ink, x, y, r, h, p, alpha=1.0, painted=0.0, cracks=0.0, t=0.0):
    """Riveted steel cylinder (x = centre, y = ground)."""
    R = pm.Reveal(p, 6)
    body = [(x - r, y), (x - r, y - h), (x + r, y - h), (x + r, y)]
    pr = R(); ink.fill(body, SEPIA if painted < .5 else MOL, (0.22 + 0.4 * painted) * alpha * pr); ink.hatch(body, pr, 90, 14, 1.6, INK, 0.35 * alpha)
    ink.stroke(body, 5, pr, INK, alpha, taper=False, dense=False)
    pr = R(); ink.stroke([(x - r, y - h), (x - r * .5, y - h - r * .22), (x + r * .5, y - h - r * .22), (x + r, y - h)], 5, pr, INK, alpha)
    pr = R()
    for k in range(1, 6):                                   # riveted seams
        yy = y - h * k / 6; ink.stroke([(x - r, yy), (x + r, yy)], 2.2, pr, INK, alpha * 0.7)
        for j in range(9): ink.dot(x - r + 2 * r * (j + .5) / 9, yy - 7, 3.2, INK, alpha * pr * 0.9)
    if cracks > 0:
        for k, (sx, sy) in enumerate([(-.2, .35), (.15, .6), (-.05, .8)]):
            pts = [(x + sx * r, y - h * sy)]; ang = -1.2 + k
            for i in range(6): px, py = pts[-1]; pts.append((px + math.cos(ang + i * .9) * 34, py + math.sin(ang - i * .6) * 30 + 22))
            ink.stroke(pts, 4, clamp(cracks * 1.4 - k * .25), RED, alpha)

def wave(ink, x0, x1, y, hgt, front, p, alpha=1.0, t=0.0):
    """A dark molasses wave whose front is at x = front, curling over at the top."""
    if p <= 0: return
    pts = [(x0, y + 10)]
    for i in range(30):
        u = i / 29; x = x0 + (front - x0) * u
        crest = hgt * (0.55 + 0.45 * u ** 2.2) + 14 * math.sin(u * 13 + t * 4)
        pts.append((x, y - crest * p))
    cx = front; ty = y - hgt * p
    pts += [(cx + 40, ty + 25), (cx + 70, ty + 90), (cx + 30, ty + 70), (cx + 55, ty + 160), (cx + 20, y - 20), (cx + 30, y + 10), (x1, y + 10)][:6]
    pts.append((front + 20, y + 10))
    ink.fill(pts, MOL, 0.85 * alpha); ink.stroke(pts, 4, 1.0, INK, alpha * 0.8, taper=False, dense=False)
    for k in range(5):                                       # glossy swirls
        yy = y - hgt * p * (0.25 + 0.13 * k)
        ink.stroke([(x0 + 60 + k * 40, yy), (front * .5 + x0 * .5, yy - 20 + 10 * math.sin(t * 3 + k)), (front - 30, yy + 8)], 2.4, 1.0, SEPIA, alpha * 0.7)

def bucket(ink, x, y, s, p, alpha=1.0):
    pts = [(x - 22 * s, y - 40 * s), (x + 22 * s, y - 40 * s), (x + 16 * s, y), (x - 16 * s, y), (x - 22 * s, y - 40 * s)]
    ink.fill(pts, SEPIA, 0.5 * alpha * p); ink.stroke(pts, 3, p, INK, alpha, taper=False, dense=False)
    ink.stroke([(x - 22 * s, y - 40 * s), (x, y - 70 * s), (x + 22 * s, y - 40 * s)], 2.4, p, INK, alpha)

def thermometer(ink, x, y, s, level, p, alpha=1.0):
    ink.stroke([(x - 14 * s, y), (x - 14 * s, y - 260 * s), (x + 14 * s, y - 260 * s), (x + 14 * s, y)], 3, p, INK, alpha, taper=False, dense=False)
    ink.circle(x, y + 22 * s, 30 * s, 3, p, INK, alpha); ink.dot(x, y + 22 * s, 24 * s, RED, alpha * p)
    ink.fill([(x - 7 * s, y), (x - 7 * s, y - 240 * s * level), (x + 7 * s, y - 240 * s * level), (x + 7 * s, y)], RED, 0.9 * alpha * p)

def scales(ink, x, y, s, tilt, p, alpha=1.0):
    R = pm.Reveal(p, 4); pr = R()
    ink.line((x, y), (x, y - 320 * s), 5, pr, INK, alpha); ink.line((x - 90 * s, y), (x + 90 * s, y), 6, pr, INK, alpha)
    a = tilt * 0.35; dx, dy = math.cos(a) * 200 * s, math.sin(a) * 200 * s; pr = R()
    ink.line((x - dx, y - 320 * s + dy), (x + dx, y - 320 * s - dy), 5, pr, INK, alpha)
    for sx, sy in ((-dx, dy), (dx, -dy)):
        px, py = x + sx, y - 320 * s + sy; pr = R()
        ink.line((px, py), (px - 60 * s, py + 120 * s), 2.4, pr, INK, alpha); ink.line((px, py), (px + 60 * s, py + 120 * s), 2.4, pr, INK, alpha)
        ink.stroke([(px - 80 * s, py + 120 * s), (px, py + 150 * s), (px + 80 * s, py + 120 * s)], 4, pr, INK, alpha)

# ------------------------------------------------------------------ cameras
FACE = pd.FACE
def cams(Wt, B):
    C = {}
    C["cold"] = [(0, 540, 1150, 1.25), (Wt("cold", "killed") - .3, 560, 1120, 1.4), (Wt("cold", "killed") + .4, 540, 1180, 1.3),
                 (B["rewind"]["t0"] + .2, 540, 1180, 1.3), (B["rewind"]["t1"], 540, 960, 1.0)]
    C["start"] = [(B["start"]["t0"], 540, 960, 1.0), (Wt("start", "steel"), 620, 1000, 1.15), (Wt("start", "molasses") + .6, 700, 900, 1.3)]
    C["leak"] = [(Wt("leak"), 640, 1080, 1.25), (Wt("leak", "Paint") - .3, 580, 1000, 1.05), (Wt("leak", "stains") + .4, 560, 960, 1.05)]
    C["burst"] = [(Wt("burst"), 600, 960, 1.05), (Wt("burst", "rivets") - .2, 580, 920, 1.08), (Wt("burst", "split") + .5, 560, 980, 1.0)]
    C["wave"] = [(Wt("wave"), 540, 1060, 1.0), (Wt("wave", "raced"), 500, 1080, 1.1), (Wt("wave", "thirty") + .8, 540, 1000, 1.0)]
    C["cost"] = [(Wt("cost"), 540, 1060, 1.1), (Wt("cost", "Twenty") - .3, 540, 980, 1.0), (Wt("cost", "hurt") + .4, 540, 960, 1.0)]
    C["rescue"] = [(Wt("rescue"), 540, 1000, 1.02), (Wt("rescue", "glue"), 540, 1040, 1.08), (Wt("rescue", "alike") + .4, 540, 1060, 1.12)]
    C["why"] = [(Wt("why"), 540, 960, 1.05), (Wt("why", "brittle"), 540, 1000, 1.0)]
    C["impact"] = [(Wt("impact"), 540, 980, 1.1), (Wt("impact", "Massachusetts") - .2, 540, 1000, 1.0), (Wt("impact", "plans") + .4, 560, 980, 1.08)]
    C["end"] = [(Wt("end"), 540, 960, 1.0), (Wt("end", "Would"), 540, 1020, 1.12), (B["end"]["t1"] - .1, 540, 1150, 1.3)]
    return C

# ------------------------------------------------------------------ plates
def street(ink, gy, p, a, n=5, x0=60, tilt=None):
    for i, (x, w, h) in enumerate([(60, 120, 180), (195, 110, 220), (320, 130, 170), (465, 115, 210), (595, 105, 160)][:n]):
        if tilt is not None and tilt[i] > 0:
            c = ink.ctx; c.save(); c.translate(x + w, gy); c.rotate(math.radians(tilt[i] * 55)); c.translate(-(x + w), -gy)
            pm.house(ink, x, gy, w, h, p, a * (1 - .4 * tilt[i])); c.restore()
        else: pm.house(ink, x, gy, w, h, p, a)

def tableau(ink, t, p, a, run=1.0):
    """Frame 1: the black wave towering over a street, people running for their lives."""
    pm.ground(ink, 1420, p, alpha=a)
    street(ink, 1420, p, a, 4, tilt=[0, 0, .35 * clamp(t / 3), .7 * clamp(t / 2)])
    front = 560 + 60 * ease(clamp(t / 3.5))
    wave(ink, 60, 1020, 1420, 760, front, p, a, t)
    for i, (x, k) in enumerate([(700, "man"), (820, "woman"), (930, "man")]):
        pose = dance_pose(t * 1.6, i, 1.0 * run, 1.8); pose.update(lean=14, aL=-70, aR=50)
        figure(ink, x + 40 * math.sin(t * 2 + i), 1420, 230, pose, p, k, a, expr="fear", t=t, var=i + 2)

def plate_cold(c, Wt):
    tableau(c.ink, c.t, c.K, c.a, 1 - clamp((c.t - Wt("rewind")) / .8))
    tr = Wt("rewind")
    if c.t > tr: pm.ground(c.ink, 1300, 1.0, alpha=c.a * clamp((c.t - tr) / .4)); tank(c.ink, 760, 1300, 200, 520, clamp((c.t - tr) / 1.8), c.a, t=c.t)

def plate_start(c, Wt):
    ink, t, a = c.ink, c.t, c.a; t0 = Wt("start")
    pm.ground(ink, 1300, c.P(t0, .8), alpha=a)
    street(ink, 1300, c.P(t0 + .3, 1.4), a * .9, 3)
    tank(ink, 760, 1300, 200, 520, 1.0, a, t=t)
    tg = Wt("start", "two"); n = 2.3 * ease(clamp((t - tg + .2) / 1.2))
    ink.text(f"{n:.1f} MILLION", 540, 460, 104, INK, a, p=c.P(tg - .2, .3))
    ink.text("GALLONS OF MOLASSES", 540, 560, 54, RED, a, p=c.P(Wt("start", "molasses"), .5))

def plate_leak(c, Wt):
    ink, t, a = c.ink, c.t, c.a; t0 = Wt("leak"); tp = Wt("leak", "Paint")
    pm.ground(ink, 1300, c.K, alpha=a)
    painted = ease(clamp((t - tp) / 1.6))
    tank(ink, 760, 1300, 200, 520, c.K, a, painted=painted, t=t)
    for i in range(6): pm.drip(ink, 600 + i * 62, 860 + (i % 3) * 120, 70 + 40 * (i % 2), c.P(t0 + .2 + i * .15, .9), a)
    tc = Wt("leak", "collected")
    for i, (x, k) in enumerate([(380, "woman"), (520, "man")]):
        pose = dict(STAND); pose.update(aR=60, eR=-40, lean=8)
        figure(ink, x, 1300, 260, pose, c.P(tc - .3 + i * .2, .6), k, a, expr="happy", t=t, var=i)
        bucket(ink, x + 70, 1300, 1.0, c.P(tc + i * .2, .5), a)
    if t > tp - .4:                                   # painter on a ladder
        lp = c.P(tp - .4, .6); ink.line((560, 1300), (600, 820), 5, lp, INK, a); ink.line((610, 1300), (650, 820), 5, lp, INK, a)
        for k in range(8): ink.line((565 + k * 5, 1250 - k * 55), (615 + k * 5, 1250 - k * 55), 3, lp, INK, a)
        pose = dict(STAND); pose.update(aR=110 + 20 * math.sin(t * 6), eR=-20)
        figure(ink, 640, 1010, 220, pose, lp, "man", a, expr="smug", t=t, var=3)
        ink.text("PAINTED BROWN", 540, 470, 92, MOL, a, p=c.P(Wt("leak", "brown"), .5))
        ink.text("TO HIDE THE LEAKS", 540, 560, 52, RED, a, p=c.P(Wt("leak", "stains"), .5))

def plate_burst(c, Wt):
    ink, t, a = c.ink, c.t, c.a; t0 = Wt("burst"); tr = Wt("burst", "rivets"); ts = Wt("burst", "split")
    pm.ground(ink, 1300, c.K, alpha=a)
    shake = 6 * math.sin(t * 40) * clamp((t - tr) / .3) * (1 - clamp((t - ts - .6) / .4))
    cx = ink.ctx; cx.save(); cx.translate(shake, 0)
    tank(ink, 760, 1300, 200, 520, c.K, a, painted=1.0, cracks=clamp((t - tr) / 1.8), t=t); cx.restore()
    pm.sun(ink, 220, 420, 60, c.P(t0, .8), t, a * .8, face=False)
    rng = np.random.default_rng(3)
    for k in range(16):                               # rivets shooting out
        st = tr + rng.uniform(0, 1.4); u = (t - st) / .6
        if u <= 0 or u > 1.2: continue
        ang = rng.uniform(-2.6, -.4); sx, sy = 760 + rng.uniform(-150, 150), 1300 - rng.uniform(120, 480)
        x, y = sx + math.cos(ang) * 600 * u, sy + math.sin(ang) * 600 * u + 300 * u * u
        ink.line((x - math.cos(ang) * 40, y - math.sin(ang) * 40), (x, y), 3, 1, INK, a * .6); ink.dot(x, y, 7, INK, a)
    ink.text("RIVETS FLEW", 540, 470, 96, RED, a, p=c.P(tr, .4))
    ink.text("LIKE GUNFIRE", 540, 570, 60, INK, a, p=c.P(Wt("burst", "gunfire"), .4))
    if t > ts - .2: wave(ink, 560, 1000, 1300, 320 * ease(clamp((t - ts + .2) / .8)), 560 - 380 * ease(clamp((t - ts) / 1.2)), 1.0, a, t)

def plate_wave(c, Wt):
    ink, t, a = c.ink, c.t, c.a; t0 = Wt("wave"); tr = Wt("wave", "raced")
    pm.ground(ink, 1420, c.K, alpha=a)
    u = ease(clamp((t - t0) / 4.5)); front = 60 + 900 * u
    tilt = [clamp((front - x - 40) / 160) for x in (60, 195, 320, 465, 595)]
    street(ink, 1420, c.K, a, 5, tilt=tilt)
    wave(ink, 40, 1040, 1420, 520, front, c.K, a, t)
    tf = Wt("wave", "twenty"); tm = Wt("wave", "thirty")
    ink.text("25 FT", 300, 470, 120, RED, a, p=c.P(tf, .4)); ink.text("≈7.6 M HIGH", 300, 560, 46, INK, a, p=c.P(tf + .3, .4))
    ink.text("35 MPH", 790, 470, 120, RED, a, p=c.P(tm, .4)); ink.text("≈56 KM/H", 790, 560, 46, INK, a, p=c.P(tm + .3, .4))

def plate_cost(c, Wt):
    ink, t, a = c.ink, c.t, c.a; t0 = Wt("cost"); t21 = Wt("cost", "Twenty"); t150 = Wt("cost", "hundred")
    gy = 1320; pm.ground(ink, gy, c.K, alpha=a)
    street(ink, gy, c.K, a * .8, 5, tilt=[.9, 1, .7, 1, .8])
    lake = [(60, gy - 30), (300, gy - 60), (620, gy - 45), (1020, gy - 70), (1020, gy + 60), (60, gy + 60)]
    ink.fill(lake, MOL, 0.8 * a * c.P(t0, .6)); ink.stroke(lake[:4], 3, c.P(t0, .6), INK, a)
    for i, x in enumerate((250, 520, 820)):
        figure(ink, x, gy - 10, 220, dance_pose(0, 0, 0), c.P(t0 + .5 + i * .3, .6), ["man", "woman", "man"][i], a * .9, rot=[-80, 84, -78][i], expr="dead", t=t, var=i)
    ink.text("21", 330, 560, 190, RED, a, p=c.P(t21, .4)); ink.text("DIED", 330, 650, 56, INK, a, p=c.P(t21 + .3, .4))
    ink.text("~150", 760, 560, 160, INK, a, p=c.P(t150, .4)); ink.text("HURT", 760, 650, 56, INK, a, p=c.P(t150 + .3, .4))

def plate_rescue(c, Wt):
    ink, t, a = c.ink, c.t, c.a; t0 = Wt("rescue"); tg = Wt("rescue", "glue")
    gy = 1360; pm.ground(ink, gy, c.K, alpha=a)
    pm.moon(ink, 820, 420, 50, c.P(t0, .8), a)
    thermometer(ink, 200, 900, 1.2, 0.7 - 0.45 * ease(clamp((t - t0 - .3) / 2)), c.P(t0, .6), a)
    for i, (x, k) in enumerate([(430, "man"), (620, "man"), (800, "woman")]):
        pose = dict(STAND); pose.update(aL=-60 - 30 * math.sin(t * 2 + i), aR=70, lean=-10 + 6 * math.sin(t * 1.5 + i))
        figure(ink, x, gy + 90, 300, pose, c.P(t0 + .4 + i * .25, .6), k, a, expr=["pain", "fear", "tired"][i], t=t, var=i + 4)
    mud = [(60, gy - 110), (1020, gy - 120), (1020, gy + 120), (60, gy + 120)]
    ink.fill(mud, MOL, 0.92 * a * c.K); ink.stroke(mud[:2], 4, c.K, INK, a)
    for k in range(6): ink.stroke([(120 + k * 150, gy - 70), (170 + k * 150, gy - 85), (220 + k * 150, gy - 70)], 2.4, c.P(tg + k * .1, .4), SEPIA, a * .8)
    ink.text("THICK AS GLUE", 540, 640, 96, MOL, a, p=c.P(tg, .5))

def plate_why(c, Wt):
    ink, t, a = c.ink, c.t, c.a; t0 = Wt("why")
    tank(ink, 540, 900, 140, 360, c.P(t0, .8) * (1 - clamp((t - Wt("why", "rushed") - .4) / .5)), a, painted=1.0, cracks=1.0, t=t)
    items = [("rushed", "RUSHED"), ("tested", "NEVER TESTED"), ("brittle", "THIN, BRITTLE STEEL")]
    for i, (w, lab) in enumerate(items):
        tw = Wt("why", w); x = [190, 540, 890][i]; y = 1040
        p = c.P(tw - .15, .6)
        if i == 0:   # a clock spinning fast
            ink.circle(x, y, 80, 4, p, INK, a); ang = t * 8; ink.line((x, y), (x + math.cos(ang) * 60, y + math.sin(ang) * 60), 4, p, RED, a); ink.line((x, y), (x, y - 45), 4, p, INK, a)
        elif i == 1:  # a water test, crossed out
            pm.drip(ink, x, y - 80, 110, p, a); ink.line((x - 70, y - 70), (x + 70, y + 70), 8, c.P(tw + .3, .3), RED, a); ink.line((x + 70, y - 70), (x - 70, y + 70), 8, c.P(tw + .45, .3), RED, a)
        else:         # a cracked steel plate
            pl = [(x - 80, y - 70), (x + 80, y - 70), (x + 80, y + 70), (x - 80, y + 70), (x - 80, y - 70)]
            ink.fill(pl, SEPIA, .4 * a * p); ink.stroke(pl, 4, p, INK, a, taper=False, dense=False)
            ink.stroke([(x - 10, y - 70), (x + 15, y - 20), (x - 5, y + 10), (x + 20, y + 70)], 5, c.P(tw + .3, .4), RED, a)
        ink.text(lab, x, 1200, 44, INK, a, p=c.P(tw, .4))
    ink.text("A DISASTER", 540, 1360, 86, RED, a, p=c.P(Wt("why", "brittle") + .6, .6)); ink.text("WAITING TO HAPPEN", 540, 1440, 58, RED, a, p=c.P(Wt("why", "brittle") + 1.0, .6))

def plate_impact(c, Wt):
    ink, t, a = c.ink, c.t, c.a; t0 = Wt("impact"); tr = Wt("impact", "responsible"); tm = Wt("impact", "Massachusetts")
    aA = a * (1 - clamp((t - tm + .2) / .5))
    if aA > .01:
        scales(ink, 540, 1300, 1.3, ease(clamp((t - tr + .4) / .8)), c.P(t0, 1.0), aA)
        ink.text("GUILTY", 540, 520, 120, RED, aA, p=c.P(tr, .4)); ink.text("THE COMPANY WAS HELD LIABLE", 540, 610, 44, INK, aA, p=c.P(tr + .3, .4))
    if t > tm - .3:
        pb = c.P(tm - .3, .7); doc = [(270, 700), (810, 700), (810, 1300), (270, 1300), (270, 700)]
        ink.fill(doc, SEPIA, .2 * a * pb); ink.stroke(doc, 4, pb, INK, a, taper=False, dense=False)
        for i in range(8): ink.stroke([(320, 780 + i * 50), (560 + 30 * (i % 3), 782 + i * 50), (760, 778 + i * 50)], 2.2, c.P(tm + i * .1, .3), INK, a * .6)
        ink.circle(680, 1190, 70, 6, c.P(Wt("impact", "engineers"), .5), RED, a)
        ink.text("APPROVED", 680, 1200, 30, RED, a, p=c.P(Wt("impact", "sign"), .4))
        ink.stroke([(330, 1220), (400, 1180), (450, 1230), (520, 1190)], 3, c.P(Wt("impact", "sign"), .6), INK, a)
        ink.text("ENGINEERS MUST SIGN OFF", 540, 560, 64, INK, a, p=c.P(Wt("impact", "engineers"), .5))

def plate_end(c, Wt):
    ink, t, a = c.ink, c.t, c.a; t0 = Wt("end"); tq = Wt("end", "Would")
    tableau(ink, t, c.P(t0, 1.0), a, 1.0)
    for k in range(5):                                # sweet smell curls
        u = ((t - t0) * .3 + k / 5) % 1
        ink.stroke([(200 + k * 160 + 30 * math.sin(u * 9), 1100 - u * 600), (230 + k * 160, 1050 - u * 600), (200 + k * 160, 1000 - u * 600)], 3, c.K, SEPIA, a * math.sin(math.pi * u))
    ink.text("?", 880, 520, 300, RED, a * (1 - clamp((t - tq - 1.4) / .4)), p=c.P(tq, .3))

PLATES = [("cold", plate_cold), ("start", plate_start), ("leak", plate_leak), ("burst", plate_burst), ("wave", plate_wave), ("cost", plate_cost),
          ("rescue", plate_rescue), ("why", plate_why), ("impact", plate_impact), ("end", plate_end)]
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
        if name == "cold": K = 1 - ease(clamp((t - tr) / 1.3)); a = 1 - clamp((t - tr1) / FADE)
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
        ink.text("A 25-FOOT WAVE", W / 2, 215, 104 * pulse, RED, al); ink.text("OF SYRUP", W / 2, 330, 70, INK, al)
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
    pm.place(sfx, pm.thud(50, 1.4), 0.0, 0.9); pm.place(sfx, pm.thud(42, 1.8), Wt("cold", "killed"), 1.0)
    for k in range(8): pm.place(sfx, pm.thud(140 + 20 * k, 0.12), Wt("burst", "rivets") + k * 0.11, 0.5)
    pm.place(sfx, pm.thud(38, 2.4), Wt("burst", "split"), 1.0); pm.place(sfx, pm.thud(44, 1.6), Wt("wave", "raced"), 0.8)
    pm.place(sfx, pm.bell(196, 5.0), Wt("cost", "Twenty"), 0.6); pm.place(sfx, pm.thud(60, 0.8), Wt("impact", "responsible"), 0.6)
    hop = 480; e = np.sqrt(np.convolve(vo ** 2, np.ones(hop) / hop, "same")); duck = np.convolve(1 - 0.45 * np.clip(e / 0.05, 0, 1), np.ones(4800) / 4800, "same")
    mix = vo * 1.0 + mus * 0.32 * duck + sfx * 0.55
    return (np.tanh(mix * 1.1) * 0.92).astype(np.float32)

def main():
    out = sys.argv[1]; stills = "--stills" in sys.argv
    work = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out", "parch"); os.makedirs(work, exist_ok=True)
    meta, vo = build_timeline(os.path.join(work, "molasses_vo1"))
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
    wav = os.path.join(work, "molasses_mix.wav"); sf.write(wav, build_audio(meta, vo, Wt, B), SR)
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
