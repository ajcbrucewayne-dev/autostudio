"""Dark History #1 (parchment): The Dancing Plague of 1518.

python3 engine/parch_dancing.py out.mp4              full render
python3 engine/parch_dancing.py out_dir --stills 1.0 5.2 ...   PNG stills at given seconds
"""
import math, os, sys, json, subprocess
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parchment as pm
from parchment import (W, H, FPS, SR, INK, RED, SEPIA, clamp, ease, ease_out, Ink, figure, dance_pose, STAND)

VOICE, SPEED = "bm_george", 0.95
BEATS = [
    ("cold", "In fifteen eighteen, an entire city started dancing... and nobody could make them stop.", 0.5),
    ("rewind", "Let's go back to where it began.", 0.2),
    ("start", "July, fifteen eighteen. Strasbourg. A woman named Frau Troffea stepped into the street... and began to dance.", 0.0),
    ("days", "There was no music. No reason. She danced... for nearly a week.", 0.0),
    ("spread", "Then others joined her. Thirty-four people in a week. By some accounts, four hundred in a month.", 0.0),
    ("cure", "Doctors blamed overheated blood. Their cure? More dancing. The city built a stage... and hired musicians.", 0.2),
    ("cost", "In the summer heat, dancers collapsed from exhaustion. And some, it's said... never got up.", 0.9),
    ("shrine", "At last, the city banned music, and sent the dancers to a mountain shrine, in red shoes marked with holy crosses.", 0.2),
    ("why", "Slowly, the dancing stopped. Historians think famine, disease and fear pushed a desperate city into mass hysteria.", 0.3),
    ("end", "But no one knows for sure. Would you have joined the dance?", 1.6),
]
STAMPS = {"cold": "1518", "start": "STRASBOURG · JULY 1518", "days": "DAYS I – VI", "spread": "IT SPREADS",
          "cure": "THE CURE", "cost": "THE COST", "shrine": "SHRINE OF ST. VITUS", "why": "WHY?", "end": "THE DANCING PLAGUE"}
GAP = 0.25

# ------------------------------------------------------------------ timeline (voice)
def build_timeline(cache):
    import render
    if os.path.exists(cache + ".json"):
        meta = json.load(open(cache + ".json")); vo = np.load(cache + ".npy"); return meta, vo
    t = 0.3; meta = []; clips = []
    for name, text, pause in BEATS:
        a = render.tts(text, VOICE, SPEED); d = len(a) / SR
        words = render.word_times(text, t, d)
        meta.append({"name": name, "t0": t, "s0": t, "s1": t + d, "words": words}); clips.append((t, a))
        t += d + GAP + pause
    total = t + 0.3; vo = np.zeros(int(total * SR), np.float32)
    for t0, a in clips: pm.place(vo, a, t0)
    for i, m in enumerate(meta): m["t1"] = meta[i + 1]["t0"] if i + 1 < len(meta) else total
    json.dump(meta, open(cache + ".json", "w")); np.save(cache + ".npy", vo)
    return meta, vo

def mk_W(meta):
    B = {m["name"]: m for m in meta}
    def Wt(beat, word=None, end=False):
        m = B[beat]
        if word is None: return m["t0"]
        for w, s, e in m["words"]:
            if w.lower().strip(".,?!…'").startswith(word.lower()): return e if end else s
        raise KeyError((beat, word))
    return Wt, B

# ------------------------------------------------------------------ plates
class Ctx:  # per-plate drawing context
    def __init__(s, ink, t, t0, K=1.0, a=1.0): s.ink, s.t, s.lt, s.K, s.a = ink, t, t - t0, K, a
    def P(s, start, dur): return clamp((s.t - start) / max(dur, 1e-3)) * s.K

def plate_frenzy(c, Wt):
    ink, t, a = c.ink, c.t, c.a; t0 = Wt("cold")
    pm.sun(ink, 200, 330, 70, c.P(t0, 0.6), t, a)
    pm.ground(ink, 1330, c.P(t0, 0.5), alpha=a)
    spots = [(170, 1150, 260, "man", 0.3), (330, 1240, 300, "woman", 1.7), (760, 1240, 300, "man", 2.6), (910, 1150, 260, "woman", 4.0),
             (250, 1340, 380, "woman", 0.9), (830, 1340, 380, "woman", 3.1)]
    for i, (x, y, h, k, ph) in enumerate(spots):
        figure(ink, x, y, h, dance_pose(t, ph, 1.0, 1.25), c.P(t0 + 0.05 * i, 0.6), k, a)
    figure(ink, 540, 1300, 420, dance_pose(t, 2.2, 1.0, 1.25), c.P(t0 + 0.2, 0.7), "skeleton", a, col=INK if t < Wt("cold", "nobody") else RED)

def plate_street(c, Wt):
    ink, t, a = c.ink, c.t, c.a; t0 = Wt("start")
    gy = 900
    pm.ground(ink, gy, c.P(t0, 0.8), 60, W - 60, a, cobbles=False)
    for i, (x, w, h) in enumerate([(70, 120, 170), (200, 105, 210), (315, 130, 160), (455, 110, 200), (575, 100, 150)]):
        pm.house(ink, x, gy, w, h, c.P(t0 + 0.3 + i * 0.35, 1.3), a * 0.9)
    pm.cathedral(ink, 830, gy, 0.72, c.P(t0 + 1.2, 2.6), a * 0.9)
    pm.sun(ink, 190, 360, 62, c.P(t0 + 0.8, 1.2), t, a)
    pm.ground(ink, 1400, c.P(Wt("start", "Frau"), 0.8), alpha=a)
    tw = Wt("start", "dance")
    pose = dance_pose(t, 0, ease(clamp((t - tw + 0.6) / 1.2))) if t > tw - 0.6 else STAND
    figure(ink, 540, 1400, 470, pose, c.P(Wt("start", "woman"), 1.6), "woman", a)

def plate_days(c, Wt):
    ink, t, a = c.ink, c.t, c.a; t0 = Wt("days"); t1 = Wt("days", "week", end=True)
    d = max(1, t1 - t0 - 0.3); u = clamp((t - t0 - 0.3) / d) * 6     # 0..6 days
    pm.ground(ink, 1300, c.P(t0, 0.6), alpha=a)
    k = u % 1; body_is_sun = k < 0.55; f = (k / 0.55) if body_is_sun else (k - 0.55) / 0.45
    bx = 110 + 860 * f; by = 640 - math.sin(math.pi * f) * 270
    if u < 6:
        if body_is_sun: pm.sun(ink, bx, by, 55, c.K, t, a, face=False)
        else: pm.moon(ink, bx, by, 45, c.K, a)
    else: pm.sun(ink, 540, 380, 55, c.K, t, a, face=True)
    ink.stroke([(90, 680), (540, 330), (990, 680)], 2, c.P(t0, 0.8), INK, a * 0.25)
    e = 1 - 0.45 * clamp(u / 6)
    figure(ink, 540, 1300, 520, dance_pose(t, 0, e, 1 - 0.3 * clamp(u / 6)), c.K, "woman", a)
    pm.tally(ink, 420, 1410, int(min(6, math.floor(u + 0.0001))), 1.0 * c.K, 80, INK, a)
    tn = Wt("days", "music")
    nx, ny = 850, 820
    pm.note(ink, nx, ny, 1.6, c.P(tn - 0.2, 0.4), a)
    ink.line((nx - 50, ny - 90), (nx + 70, ny + 30), 8, c.P(tn + 0.25, 0.3), RED, a)
    ink.line((nx + 70, ny - 90), (nx - 50, ny + 30), 8, c.P(tn + 0.45, 0.3), RED, a)

CROWD = [(540, 1330, 330, "woman", 0.0)]
rng = np.random.default_rng(5)
for row, (y, h, n) in enumerate([(1330, 300, 6), (1080, 230, 7), (880, 180, 8), (720, 140, 9)]):
    for j in range(n):
        x = 110 + (W - 220) * (j + 0.5 * (row % 2)) / (n - 0.5 + 0.5 * (row % 2))
        if row == 0 and abs(x - 540) < 120: continue
        CROWD.append((x + rng.uniform(-20, 20), y + rng.uniform(-10, 10), h * rng.uniform(0.9, 1.05), rng.choice(["man", "woman"]), rng.uniform(0, 6)))
CROWD.sort(key=lambda s: s[1])

def plate_spread(c, Wt):
    ink, t, a = c.ink, c.t, c.a; t0 = Wt("spread")
    t34 = Wt("spread", "Thirty"); t400 = Wt("spread", "four", end=False)
    n = len(CROWD)
    for i, (x, y, h, k, ph) in enumerate(sorted(CROWD, key=lambda s: -s[1])):
        if i == 0: st = t0
        else: st = t0 + 0.6 + (t34 + 1.5 - t0 - 0.6) * (i / (n - 1)) ** 0.8
        figure(ink, x, y, h, dance_pose(t, ph, 1.0, 1.1), c.P(st, 0.5), k, a * (0.75 + 0.25 * (y > 1000)))
    pm.ground(ink, 1330, c.P(t0, 0.6), alpha=a)
    ink.text("34", 540, 400, 170, INK, a, p=c.P(t34, 0.25) * 1.0)
    ink.line((420, 420), (660, 360), 10, c.P(t400 - 0.1, 0.3), RED, a)
    ink.text("400 ?", 540, 580, 150, RED, a, p=c.P(t400, 0.6))

def doctor_pose(t):
    p = dict(STAND); p.update(aR=95, eR=-60, aL=-20, eL=-30, head=-6); return p

def plate_cure(c, Wt):
    ink, t, a = c.ink, c.t, c.a; t0 = Wt("cure"); tc = Wt("cure", "More")
    aA = a * (1 - clamp((t - tc + 0.2) / 0.5))
    if aA > 0.01:
        figure(ink, 320, 1350, 560, doctor_pose(t), c.P(t0, 1.0), "man", aA)
        ink.circle(320 + 140, 1350 - 470, 26, 3, c.P(t0 + 0.8, 0.4), INK, aA)  # urine flask
        ink.line((320 + 140, 1350 - 496), (320 + 140, 1350 - 525), 6, c.P(t0 + 0.9, 0.3), INK, aA)
        sc = [(560, 640), (980, 640), (980, 820), (560, 820)]
        pm.Ink.fill(ink, sc, SEPIA, 0.25 * aA * c.P(t0 + 0.5, 0.5))
        ink.stroke(sc + [sc[0]], 4, c.P(t0 + 0.5, 0.6), INK, aA, taper=False, dense=False)
        ink.text("HOT", 770, 690, 70, RED, aA, p=c.P(Wt("cure", "overheated"), 0.4))
        ink.text("BLOOD", 770, 775, 70, RED, aA, p=c.P(Wt("cure", "blood"), 0.4))
        for i in range(4): pm.drip(ink, 640 + i * 95, 820, 60 + 30 * (i % 2), c.P(Wt("cure", "blood") + 0.3 + i * 0.15, 0.8), aA)
    if t >= tc - 0.2:
        ts = Wt("cure", "stage"); tm = Wt("cure", "musicians")
        stage = [(130, 1180), (950, 1180), (950, 1240), (130, 1240)]
        ps = c.P(tc - 0.3, 0.8)
        ink.fill(stage, SEPIA, 0.4 * a * ps); ink.hatch(stage, ps, 0, 12, 2, INK, 0.6 * a)
        ink.stroke(stage + [stage[0]], 4, ps, INK, a, taper=False, dense=False)
        for lx in (170, 400, 680, 910): ink.line((lx, 1240), (lx, 1360), 6, ps, INK, a)
        for i, (x, ph, k) in enumerate([(400, 0.3, "woman"), (540, 2.1, "man"), (680, 4.0, "woman")]):
            figure(ink, x, 1180, 300, dance_pose(t, ph, 1, 1.15), c.P(tc + i * 0.25, 0.6), k, a)
        pf = c.P(tm - 0.4, 0.8)
        fp = dict(STAND); fp.update(aL=-100, eL=-40, aR=60 + 25 * math.sin(t * 9), eR=-70, head=-10)
        figure(ink, 220, 1180, 290, fp, pf, "man", a)
        ink.circle(195, 1180 - 210, 18, 3, pf, INK, a)
        bx = 220 + 60 + 30 * math.sin(t * 9); ink.line((bx - 60, 1180 - 230), (bx + 40, 1180 - 190), 3, pf, INK, a)
        dp = dict(STAND); hit = abs(math.sin(t * 7)); dp.update(aL=-60 - 40 * hit, eL=-30, aR=60, eR=40)
        figure(ink, 860, 1180, 290, dp, pf, "man", a, flip=True)
        ink.circle(860, 1180 - 110, 38, 4, pf, INK, a); ink.fill([(822, 1070), (898, 1070), (898, 1095), (822, 1095)], SEPIA, 0.4 * a * pf)
        if t > tm:
            for i in range(6):
                u = ((t - tm) * 0.5 + i / 6) % 1; side = i % 2
                nx = (250 if side == 0 else 830) + math.sin(u * 7 + i) * 50 + (u * 150 if side == 0 else -u * 150); ny = 900 - u * 520
                pm.note(ink, nx, ny, 1.1, c.K, a * math.sin(math.pi * u))

def plate_cost(c, Wt):
    ink, t, a = c.ink, c.t, c.a; t0 = Wt("cost"); tcol = Wt("cost", "collapsed"); tn = Wt("cost", "never")
    pm.sun(ink, 540, 420, 95, c.P(t0, 0.8), t, a, face=False)
    for i in range(5):  # heat shimmer
        y = 650 + i * 40; ink.stroke([(150 + x, y + math.sin(x * 0.03 + t * 5 + i) * 8) for x in range(0, 780, 60)], 2.5, c.P(Wt("cost", "heat"), 0.6), INK, a * 0.5, taper=False)
    pm.ground(ink, 1330, c.P(t0, 0.6), alpha=a)
    dancers = [(230, "woman", 0.3, None, 0), (440, "man", 1.9, 0.0, -82), (640, "woman", 3.3, 0.7, 82), (850, "man", 4.4, None, 0)]
    for x, k, ph, delay, rr in dancers:
        if delay is None:
            tired = clamp((t - tcol) / 3); pose = dance_pose(t, ph, 1 - 0.5 * tired, 1.2 - 0.5 * tired); f = 0
        else:
            cs = tcol + delay; f = ease(clamp((t - cs) / 0.7)); pose = dance_pose(t, ph, 1 - f, 1.2 - 0.6 * f)
        figure(ink, x, 1330, 300, pose, c.P(t0 + 0.1, 0.8), k, a, rot=rr * f)
    skc = RED if t > tn else INK
    figure(ink, 540, 1330, 380, dance_pose(t, 2.6, 1, 1.3), c.P(Wt("cost", "some") - 0.2, 0.8), "skeleton", a, col=skc)
    for i in range(6): pm.drip(ink, 130 + i * 165, 70, 80 + 50 * ((i * 7) % 3), c.P(tn + 0.1 + i * 0.12, 0.9), a)

PATH = [(160, 1330), (520, 1250), (300, 1120), (640, 1030), (470, 900), (700, 760), (760, 650)]
def plate_shrine(c, Wt):
    ink, t, a = c.ink, c.t, c.a; t0 = Wt("shrine"); tb = Wt("shrine", "banned"); tsh = Wt("shrine", "shrine")
    pm.mountain(ink, 60, W - 60, 1340, [(200, 1000), (380, 840), (520, 900), (760, 600), (900, 820), (1000, 900)], c.P(t0, 1.4), a)
    pm.chapel(ink, 760, 620, 0.8, c.P(t0 + 1.0, 1.2), a)
    tp = Wt("shrine", "sent")
    ink.stroke(PATH, 3, c.P(tp - 0.2, 1.2), INK, a * 0.6, taper=False)
    # crossed-out music note over the city (banned)
    nx, ny = 200, 520
    pm.note(ink, nx, ny, 1.4, c.P(tb - 0.4, 0.4), a * (1 - clamp((t - tb - 2.5) / 0.6)))
    ink.line((nx - 45, ny - 80), (nx + 65, ny + 25), 8, c.P(tb, 0.25), RED, a * (1 - clamp((t - tb - 2.5) / 0.6)))
    ink.line((nx + 65, ny - 80), (nx - 45, ny + 25), 8, c.P(tb + 0.15, 0.25), RED, a * (1 - clamp((t - tb - 2.5) / 0.6)))
    P = pm.smooth(PATH, 10); seg = np.sqrt(((P[1:] - P[:-1]) ** 2).sum(1)); cum = np.concatenate([[0], np.cumsum(seg)])
    for i in range(7):
        s = clamp((t - tp - 0.4) * 0.07 - i * 0.07)
        if s <= 0: continue
        L = cum[-1] * min(0.97, s); j = min(len(seg) - 1, np.searchsorted(cum, L) - 1); x, y = P[j]
        hh = 120 - 50 * (L / cum[-1]); wk = dict(STAND); sw = math.sin(t * 6 + i) * 18
        wk.update(hL=-sw, hR=sw, aL=-sw * 0.8, aR=sw * 0.8, bob=0)
        figure(ink, x, y, hh, wk, c.K, "woman" if i % 2 else "man", a, shoes=RED, wash=False)
    pm.shoe(ink, 760, 1420, 1.15, c.P(Wt("shrine", "red"), 0.6), a)
    pm.shoe(ink, 860, 1450, 1.15, c.P(Wt("shrine", "shoes"), 0.6), a)

def plate_why(c, Wt):
    ink, t, a = c.ink, c.t, c.a; t0 = Wt("why")
    figure(ink, 540, 760, 300, dance_pose(t, 0, 0.25, 0.4), c.P(t0, 0.8) * (1 - clamp((t - Wt("why", "Historians")) / 0.6)), "woman", a)
    items = [("famine", "FAMINE", lambda p: pm.wheat(ink, 190, 1080, 0.95, p, a, droop=0.6)),
             ("disease", "DISEASE", lambda p: pm.skull(ink, 540, 940, 72, p, a)),
             ("fear", "FEAR", lambda p: pm.eye(ink, 890, 960, 0.95, p, a, t))]
    for i, (w, lab, fn) in enumerate(items):
        tw = Wt("why", w); fn(c.P(tw - 0.15, 0.6))
        ink.text(lab, [190, 540, 890][i], 1165, 50, INK, a, p=c.P(tw, 0.4))
    th = Wt("why", "mass")
    ink.text("MASS HYSTERIA", 540, 1330, 92, RED, a, p=c.P(th, 0.7))
    ink.line((170, 1385), (910, 1385), 6, c.P(th + 0.7, 0.4), RED, a)

def plate_end(c, Wt):
    ink, t, a = c.ink, c.t, c.a; t0 = Wt("end")
    pm.ground(ink, 1330, c.P(t0, 0.6), alpha=a)
    figure(ink, 540, 1330, 560, dance_pose(t, 0, 1, 1.0), c.P(t0, 1.2), "woman", a)
    tq = Wt("end", "Would")
    ink.text("?", 860, 560, 330, RED, a, p=c.P(tq, 0.3))

PLATES = [("cold", plate_frenzy), ("start", plate_street), ("days", plate_days), ("spread", plate_spread), ("cure", plate_cure),
          ("cost", plate_cost), ("shrine", plate_shrine), ("why", plate_why), ("end", plate_end)]
FADE = 0.45

# ------------------------------------------------------------------ frame
def draw_frame(ink, t, meta, Wt, B):
    import render
    pm.BOIL[0] = int(t * 8)
    ink.clear()
    tr = Wt("rewind"); tr1 = B["rewind"]["t1"]
    starts = [(Wt(n) if n != "start" else B["start"]["t0"]) for n, _ in PLATES]
    for i, (name, fn) in enumerate(PLATES):
        st = starts[i]; nxt = starts[i + 1] if i + 1 < len(PLATES) else 1e9
        if t < st - 0.01 or t > nxt + FADE: continue
        a = 1 - clamp((t - nxt) / FADE); K = 1.0
        if name == "cold":
            K = 1 - ease(clamp((t - tr) / 1.3)); a = 1.0 if t < tr1 else 0.0
            if K <= 0.001: continue
        dur = (nxt if nxt < 1e8 else st + 8) - st
        z = 1 + 0.04 * clamp((t - st) / max(dur, 1))
        c = ink.ctx; c.save(); c.translate(W / 2, H * 0.5); c.scale(z, z); c.translate(-W / 2, -H * 0.5)
        fn(Ctx(ink, t, st, K, a), Wt); c.restore()
    # stamp
    for m in meta:
        s = STAMPS.get(m["name"])
        if not s: continue
        st = m["t0"]; en = m["t1"]
        if m["name"] == "cold": en = B["rewind"]["t0"] + 0.9
        if st <= t < en + 0.3:
            al = 1 - clamp((t - en) / 0.3)
            if m["name"] == "cold": pm.stamp(ink, s, (t - st) * 4, H * 0.09, 110, al)
            else: pm.stamp(ink, s, t - st, H * 0.085, 54, al)
    # captions
    for m in meta:
        if m["s0"] - 0.05 <= t <= m["s1"] + 0.2:
            for g in render.build_groups([tuple(w) for w in m["words"]]):
                if g[0][1] <= t < g[-1][2] + 0.15: pm.caption(ink, g, t); break

def build_audio(meta, vo, Wt, B):
    n = len(vo); mus = pm.drone(n) * 0.55
    jt = np.zeros(n, np.float32)
    det = np.zeros(n, np.float32)
    tcost = Wt("cost"); i0 = int(tcost * SR); det[i0:] = np.linspace(0, 0.03, n - i0)
    J = pm.jig(n, det)
    def env(a, b, fi=0.15, fo=0.05):
        e = np.zeros(n, np.float32); s0, s1 = int(a * SR), min(n, int(b * SR))
        e[s0:s1] = 1
        k = int(fi * SR); e[s0:s0 + k] *= np.linspace(0, 1, k)[:max(0, min(k, s1 - s0))] if s1 > s0 else 1
        k2 = int(fo * SR); e[max(s0, s1 - k2):s1] *= np.linspace(1, 0, s1 - max(s0, s1 - k2))
        return e
    jenv = env(0, Wt("rewind") + 0.2, 0.01, 0.4) * 0.8 + env(Wt("cure", "hired") - 0.1, Wt("shrine", "banned") + 0.35, 0.3, 0.04) * 1.0 \
        + env(Wt("end", "Would"), n / SR, 1.5, 1.0) * 0.45
    mus += J * jenv
    sfx = np.zeros(n, np.float32)
    for name, _ in PLATES:
        st = B[name]["t0"]
        pm.place(sfx, pm.page_whoosh(hash(name) % 99), st - 0.25, 0.5)
        pm.place(sfx, pm.quill(1.8, hash(name) % 77), st, 0.35)
    pm.place(sfx, pm.quill(1.2, 5)[::-1].copy(), Wt("rewind"), 0.5)
    pm.place(sfx, pm.thud(42, 2.0), Wt("cost", "never"), 1.0)
    pm.place(sfx, pm.thud(55, 1.2), Wt("cold", "nobody"), 0.6)
    pm.place(sfx, pm.bell(196, 5.0), Wt("shrine", "shrine"), 0.7)
    pm.place(sfx, pm.thud(60, 0.8), Wt("why", "mass"), 0.5)
    # duck music under voice
    hop = 480; e = np.sqrt(np.convolve(vo ** 2, np.ones(hop) / hop, "same")); duck = 1 - 0.45 * np.clip(e / 0.05, 0, 1)
    duck = np.convolve(duck, np.ones(4800) / 4800, "same")
    mix = vo * 1.0 + mus * 0.32 * duck + sfx * 0.55
    mix = np.tanh(mix * 1.1) * 0.92
    return mix.astype(np.float32)

def main():
    out = sys.argv[1]; stills = "--stills" in sys.argv
    work = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out", "parch"); os.makedirs(work, exist_ok=True)
    meta, vo = build_timeline(os.path.join(work, "dancing_vo"))
    Wt, B = mk_W(meta); total = len(vo) / SR
    paper = pm.make_paper(); glow = pm.glow_map(); ink = Ink()
    if stills:
        from PIL import Image
        os.makedirs(out, exist_ok=True)
        for s in sys.argv[sys.argv.index("--stills") + 1:]:
            t = float(s); draw_frame(ink, t, meta, Wt, B)
            Image.fromarray(pm.composite(paper, glow, ink, t)).resize((540, 960)).save(os.path.join(out, f"t{t:06.2f}.png"))
        print("beats:", [(m["name"], round(m["t0"], 2)) for m in meta], "total", round(total, 1)); return
    import soundfile as sf
    wav = os.path.join(work, "dancing_mix.wav"); sf.write(wav, build_audio(meta, vo, Wt, B), SR)
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
