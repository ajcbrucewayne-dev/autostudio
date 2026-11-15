"""Forbidden Places #1 v2 — the tomb no one may open, with animated "why" explanations.
Facts: Qin Shi Huang (d. 210 BC), tomb mound near Xi'an; Terracotta Army found 29 March 1974 by farmers digging a well, ~1.5 km
east of the mound; commonly estimated ~8,000 figures; Sima Qian (~100 years later) described "a hundred rivers" simulated with
mercury and a ceiling decorated with heavenly bodies — and does not mention the army; soil tests found unusually high mercury
in the mound; reasons to wait: preservation limits and safety (mercury vapour); excavated warriors' lacquer curled ~15 s after
exposure and flaked off in ~4 min (National Geographic).
Photos (Wikimedia Commons): public domain (User:airunp; Richardelainechambers), CC BY 2.0 (Arian Zwegers; Peter Dowley).
Map: NASA Blue Marble + Natural Earth (public domain).
"""
import math, os, importlib.util
from cartoon import *
import globe
from episodes_util import paint_rgba

_spec = importlib.util.spec_from_file_location("v1", os.path.join(os.path.dirname(os.path.abspath(__file__)), "forbidden_01_qin_tomb.py"))
v1 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(v1)
photo, full, stamp, PH = v1.photo, v1.full, v1.stamp, v1.PH

NAME = "forbidden_01_qin_tomb_v2"
LOOK = "cinematic"
TITLE = v1.TITLE
DESCRIPTION = v1.DESCRIPTION
TAGS = v1.TAGS
VOICE, SPEED = "am_michael", 1.06
HOOK = ("SEALED FOR 2,200 YEARS", "WHY?")
BEATS = [
    ("hook", "No one is allowed to open this tomb... and it's not because of a curse.", 0.2),
    ("who", "It belongs to China's first emperor, buried over two thousand years ago near Xi'an.", 0.0),
    ("dig", "In 1974, farmers digging a well hit something strange. A clay head.", 0.2),
    ("army", "They had found a buried army. An estimated eight thousand soldiers, and not one history book had mentioned it.", 0.0),
    ("inside", "But the emperor's own tomb is still sealed. An ancient historian wrote that inside flow a hundred rivers of mercury, under a ceiling of stars.", 0.0),
    ("proof", "And when scientists tested the soil above it, they found unusually high mercury.", 0.0),
    ("why", "So why not dig? Mercury vapor could poison the diggers. And when the clay army was dug up, its paint curled in fifteen seconds and flaked off in four minutes.", 0.3),
    ("end", "So the emperor waits, until science can open his tomb without destroying it. Would you open it?", 1.0),
]
EARTH_BROWN, DIRT = rgb("#7a5a3a"), rgb("#5a3f28")

def dark_bg(c, t):
    bg_cinema(c, t, seed=12, top="#0a0705", bot="#2a1a0e", neb=(("#5a3a1a", 0.4), ("#3a2a1a", 0.3), ("#6a4a2a", 0.2)))

def earth(c, t, lon0, lat0, R, cy=1000):
    bg_cinema(c, t); paint_rgba(c, globe.render_globe(lon0, lat0, R, W / 2, cy, sun=(-0.35, 0.4, 0.85)))

def farmer(c, x, y, s, t, dig=True):
    """little farmer with a shovel, digging"""
    c.save(); c.translate(x, y); c.scale(s, s); a = 0.6 * math.sin(t * 6) if dig else 0
    c.new_path(); c.move_to(-14, 0); c.line_to(-10, -70); c.move_to(14, 0); c.line_to(10, -70); c.set_source_rgb(*OUT); c.set_line_width(12); c.stroke()
    c.new_path(); rrect(c, -26, -150, 52, 85, 18); fs(c, rgb("#3a6fb0"), 5)
    circle(c, 0, -178, 26, rgb("#f2c9a0"), 5); c.new_path(); path(c, [(-36, -190), (0, -222), (36, -190)]); fs(c, rgb("#e3c76a"), 4)
    c.save(); c.translate(20, -120); c.rotate(0.9 + a); c.new_path(); c.move_to(0, 0); c.line_to(0, 120); c.set_source_rgb(*rgb("#8b5a2b")); c.set_line_width(8); c.stroke()
    c.new_path(); rrect(c, -16, 116, 32, 40, 8); fs(c, GREY, 4); c.restore()
    c.restore()

def ground_section(c, t, depth, hit=0.0):
    """cutaway of the earth: surface at y=640, a well shaft dug to `depth` px, and a clay head revealed when hit > 0"""
    c.new_path(); c.rectangle(0, 640, W, 900); fs(c, DIRT, 0)
    for k in range(4):
        y = 700 + k * 150; c.new_path(); c.move_to(0, y); [c.line_to(x, y + 12 * math.sin(x * 0.01 + k)) for x in range(0, W + 40, 40)]
        c.set_source_rgba(0.3, 0.2, 0.12, 0.6); c.set_line_width(5); c.stroke()
    rng = np.random.default_rng(2)
    for k in range(40): circle(c, rng.uniform(0, W), rng.uniform(680, 1500), rng.uniform(4, 12), rgb("#6e4e32"), 0, 0.8)
    c.new_path(); c.rectangle(0, 560, W, 80); fs(c, rgb("#4cc35a"), 6)
    if depth > 0: c.new_path(); c.rectangle(470, 640, 140, depth); fs(c, rgb("#1e140c"), 5)
    if hit > 0:   # a terracotta head buried below the shaft
        k = ease_back(hit); c.save(); c.translate(540, 640 + depth + 90); c.scale(k, k)
        c.new_path(); c.save(); c.scale(1, 1.2); c.arc(0, 0, 60, 0, 2 * math.pi); c.restore(); fs(c, rgb("#b08a6a"), 7)
        for sx in (-1, 1): c.new_path(); c.move_to(sx * 28, -6); c.line_to(sx * 10, -6); c.set_source_rgb(*OUT); c.set_line_width(7); c.stroke()
        c.new_path(); c.move_to(-16, 34); c.line_to(16, 34); c.set_line_width(6); c.stroke()
        c.new_path(); path(c, [(-62, -30), (-40, -86), (40, -86), (62, -30)]); fs(c, rgb("#9a7656"), 6)
        c.restore()
        ring(c, 540, 640 + depth + 90, 90 + 160 * clamp(hit * 2 - 1), YEL, 8, 1 - clamp(hit * 2 - 1))

def site_plan(c, t, p):
    """top-down plan: mound + the army pits 1.5 km east"""
    if p <= 0: return
    c.new_path(); c.arc(330, 800, 170 * ease_back(p), 0, 2 * math.pi); fs(c, EARTH_BROWN, 7)
    text(c, "TOMB MOUND", 330, 1010, 40, WHITE, alpha=p)
    for i in range(3):
        c.new_path(); c.rectangle(760, 640 + i * 150, 220 * p, 100); fs(c, rgb("#c9a27a"), 5)
    text(c, "ARMY PITS", 870, 1100, 40, YEL, alpha=p)
    arrow(c, (520, 800), (740, 800), p, WHITE, 8, 22); text(c, "1.5 KM", 630, 760, 40, WHITE, alpha=p)

def chamber(c, t, merc, stars, cut=1.0):
    """big cutaway of the sealed chamber: palace floor with mercury rivers, ceiling of stars"""
    c.new_path(); c.move_to(-50, 1300); c.curve_to(150, 600, 350, 380, 540, 370); c.curve_to(730, 380, 930, 600, 1130, 1300); c.close_path(); fs(c, EARTH_BROWN, 8)
    c.new_path(); rrect(c, 140, 640, 800, 560, 30); fs(c, rgb("#120c18"), 7)
    rng = np.random.default_rng(5)
    for k in range(50):   # star ceiling
        x, y = rng.uniform(170, 910), rng.uniform(670, 830); a = stars * (0.6 + 0.4 * math.sin(t * 3 + k))
        if a > 0.02: star(c, x, y, 7 + 4 * (k % 3), (1, 0.9, 0.5), 0, t * 0.3 + k)
    if merc > 0:          # a hundred rivers of mercury (we draw a few, flowing)
        for k in range(6):
            pts = [(170 + x, 900 + k * 45 + 14 * math.sin(x * 0.02 + t * 2.5 + k)) for x in range(0, 741, 20)]
            pts = pts[:max(2, int(len(pts) * merc))]
            c.new_path(); path(c, pts, close=False); c.set_source_rgba(0.85, 0.88, 0.95, 0.9); c.set_line_width(14); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke()
            for j in range(3):
                gx = 170 + ((t * 140 + j * 230 + k * 60) % 740) * merc; circle(c, gx, 900 + k * 45, 6, WHITE, 0, 0.9)
    c.new_path(); rrect(c, 470, 1110, 140, 70, 12); fs(c, rgb("#7a5a2a"), 5); text(c, "EMPEROR", 540, 1145, 26, (1, 0.9, 0.6), outline=None)

def heat_soil(c, t, p):
    """soil mercury readings: probes along the mound, a hot zone above the tomb"""
    if p <= 0: return
    for i in range(9):
        x = 140 + i * 100; v = math.exp(-((x - 540) / 170) ** 2); pk = clamp(p * 9 - i)
        if pk <= 0: continue
        c.new_path(); c.move_to(x, 420); c.line_to(x, 560); c.set_source_rgb(1, 1, 1); c.set_line_width(6); c.stroke()
        h = 30 + 220 * v * pk; c.new_path(); rrect(c, x - 30, 400 - h, 60, h, 10); fs(c, mix(YEL, RED, v), 4)
    if p > 0.95: label(c, "Hg HIGHEST ABOVE THE TOMB", W / 2, 220, 46, RED, WHITE, clamp((p - 0.95) * 20))

def vapor(c, t, t0, p):
    if p <= 0: return
    for k in range(18):
        u = ((t - t0) * 0.35 + k / 18) % 1; x = 220 + (k * 157) % 640; y = 1150 - u * 700
        cloud(c, x, y, 40 + (k % 3) * 12, (0.7, 0.85, 0.6), 0.25 * p * math.sin(math.pi * u))
    c.save(); c.translate(540, 520); k = ease_back(p); c.scale(k, k)
    c.new_path(); path(c, [(0, -110), (100, 70), (-100, 70)]); fs(c, YEL, 8)
    skull_r = 30; circle(c, 0, 10, skull_r, WHITE, 5)
    for sx in (-1, 1): circle(c, sx * 11, 6, 8, OUT, 0)
    c.restore()

def peel(c, t, t0, dur):
    """paint flakes curling and flying off the warrior photo"""
    u = clamp((t - t0) / dur); rng = np.random.default_rng(9)
    for k in range(70):
        start = k / 70 * 0.85
        if u < start: continue
        f = clamp((u - start) / 0.25); x0, y0 = rng.uniform(250, 830), rng.uniform(450, 1250)
        x = x0 + f * rng.uniform(-200, 200); y = y0 + f * f * 500
        c.save(); c.translate(x, y); c.rotate(f * 6 + k); c.new_path(); rrect(c, -14, -8, 28, 16, 4)
        c.set_source_rgba(*[RED, rgb("#3a8f5a"), rgb("#d9b48a"), rgb("#3a5fb0")][k % 4], 1 - f); c.fill(); c.restore()

# ---------------- scenes
def s_hook(c, s):
    t = s.t
    z = 1.62 - 0.22 * ease_out(t / 0.6) + 0.04 * t          # fast punch-in pull-back on frame 1, then a slow drift
    photo(c, "faces", 0, 0, W, H, z, (0.72, 0.45))
    c.save(); c.identity_matrix(); g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgba(0, 0, 0, 0, 0.6); g.add_color_stop_rgba(0.35, 0, 0, 0, 0); g.add_color_stop_rgba(0.65, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, 0.7)
    c.set_source(g); c.paint(); c.restore()
    stamp(c, "SEALED", W / 2, 1150, 130, clamp((t - 0.25) / 0.25))      # slams at 0.3 s
    if t > s.W("hook", "curse") - 0.2:
        c.new_path(); rrect(c, 290, 1270, 500, 90, 20); c.set_source_rgba(0, 0, 0, 0.6); c.fill()
        text(c, "NOT A CURSE.", W / 2, 1315, 56, WHITE)
    text(c, PH["faces"][1], W / 2, 1880, 26, WHITE, alpha=0.8)

def s_who(c, s):
    v1.s_who(c, s)

def s_dig(c, s):
    t = s.t; th = s.W("dig", "strange"); tc = s.W("dig", "clay")
    dark_bg(c, t)
    depth = 520 * ease(clamp((t - s.t0) / (th - s.t0)))
    ground_section(c, t, depth, s.P(tc - 0.3, 0.6))
    farmer(c, 400, 560, 1.0, t, dig=t < th)
    pop_text(c, "1974", W / 2, 330, 130, s.P(s.t0 + 0.1, 0.3), YEL)
    label(c, "DIGGING A WELL", W / 2, 460, 48, WHITE, OUT, s.P(s.W("dig", "well") - 0.2, 0.3))

def s_army(c, s):
    t = s.t; te = s.W("army", "eight"); th = s.W("army", "history")
    if t < te - 0.3:
        dark_bg(c, t); site_plan(c, t, s.P(s.t0, 0.5))
        pop_text(c, "A BURIED ARMY", W / 2, 360, 96, s.P(s.t0 + 0.2, 0.3), YEL)
    else:
        full(c, s, "pit", 1.0, 1.2, (0.5, 0.55), 5.0)
        n = 8000 * ease(clamp((t - te + 0.3) / 1.2)); text(c, f"{n:,.0f}", W / 2, 520, 170, YEL); text(c, "CLAY SOLDIERS", W / 2, 650, 64, WHITE)
        if t > th - 0.3: stamp(c, "NOT IN ANY HISTORY BOOK", W / 2, 1180, 56, s.P(th - 0.3, 0.3), YEL, -0.08)

def s_inside(c, s):
    t = s.t; tr = s.W("inside", "hundred"); ts = s.W("inside", "stars")
    dark_bg(c, t)
    chamber(c, t, clamp((t - tr + 0.2) / 1.4), clamp((t - ts + 0.4) / 0.6))
    label(c, "STILL SEALED", W / 2, 300, 60, YEL, OUT, s.P(s.W("inside", "sealed") - 0.2, 0.3))
    if t > tr - 0.2: label(c, "100 RIVERS OF MERCURY", W / 2, 420, 50, GREY, OUT, s.P(tr - 0.2, 0.3))

def s_proof(c, s):
    t = s.t; tt = s.W("proof", "tested")
    dark_bg(c, t)
    c.new_path(); c.move_to(-50, 1300); c.curve_to(150, 760, 350, 600, 540, 590); c.curve_to(730, 600, 930, 760, 1130, 1300); c.close_path(); fs(c, EARTH_BROWN, 8)
    c.new_path(); rrect(c, 340, 980, 400, 200, 20); fs(c, rgb("#120c18"), 6); text(c, "TOMB", 540, 1080, 40, (1, 0.9, 0.6), outline=None)
    heat_soil(c, t, clamp((t - tt + 0.2) / 2.2))

def s_why(c, s):
    t = s.t; tv = s.W("why", "vapor"); td = s.W("why", "clay"); tf = s.W("why", "fifteen"); tfo = s.W("why", "four")
    if t < td - 0.3:
        dark_bg(c, t); chamber(c, t, 1.0, 1.0); vapor(c, t, tv - 0.5, s.P(tv - 0.4, 0.4))
        if t > tv - 0.2: label(c, "TOXIC VAPOR", W / 2, 300, 64, YEL, OUT, s.P(tv - 0.2, 0.3))
    else:
        photo(c, "dug", 0, 0, W, H, 1.3, (0.55, 0.45))
        cl = 1 - clamp((t - tf) / max(0.6, tfo - tf + 0.8))
        c.save(); c.identity_matrix(); c.set_source_rgba(0.85, 0.35, 0.25, 0.45 * cl); c.set_operator(cairo.OPERATOR_OVERLAY); c.paint(); c.restore()
        peel(c, t, tf - 0.2, max(1.0, tfo - tf + 1.0))
        p = s.P(tf - 0.3, 0.3); c.new_path(); rrect(c, 190, 880, 700, 220, 30); fs(c, rgb("#1d1230"), 6, 0.92 * p)
        secs = lerp(0, 240, ease(clamp((t - tf) / max(0.8, tfo - tf + 0.8))))
        text(c, f"{int(secs // 60)}:{int(secs % 60):02d}", W / 2, 950, 110, RED if secs > 60 else WHITE, alpha=p)
        text(c, "PAINT CURLS AT 0:15 · GONE BY 4:00", W / 2, 1050, 32, WHITE, alpha=p)
        text(c, PH["dug"][1], W / 2, 1880, 26, WHITE, alpha=0.8)

def s_end(c, s):
    v1.s_end(c, s)

SCENES = [("hook", s_hook), ("who", s_who), ("dig", s_dig), ("army", s_army), ("inside", s_inside), ("proof", s_proof), ("why", s_why), ("end", s_end)]

def impacts(Wt, B):
    return [0.3, Wt("dig", "clay"), Wt("why", "four")]

def sfx(Wt, B, put):
    put(sfx_boom(38, 2.2), 0.0, 0.5)
    put(sfx_whoosh(5, 1.6), Wt("who"), 0.5); put(sfx_ding(1500), Wt("who", "Xi'an"), 0.4)
    for i in range(8): put(sfx_tick(), Wt("dig") + 0.2 + i * 0.32, 0.5)
    put(sfx_boom(60, 0.8), Wt("dig", "clay"), 0.7)
    for i in range(10): put(sfx_tick(), Wt("army", "eight") + i * 0.11, 0.4)
    put(sfx_ding(2000), Wt("inside", "hundred"), 0.4); put(sfx_ding(2600), Wt("inside", "stars"), 0.3)
    for i in range(9): put(sfx_pop(400 + i * 60), Wt("proof", "tested") + i * 0.24, 0.3)
    put(sfx_whoosh(9, 2.0), Wt("why", "vapor"), 0.5)
    for i in range(14): put(sfx_tick(), Wt("why", "fifteen") + i * 0.12, 0.35)
    put(sfx_ding(1320), Wt("end", "Would"), 0.5)
