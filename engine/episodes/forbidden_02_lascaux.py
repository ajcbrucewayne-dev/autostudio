"""Forbidden Places #2: the cave our breath almost destroyed (Lascaux, Dordogne, France).
Facts: discovered in 1940 by teenagers; paintings ~17,000 years old; opened to the public in 1948; visitors' exhaled CO2, heat and
moisture (plus lighting) disturbed the cave — green algae appeared in 1962 ("green sickness"), calcite ("white sickness");
closed in April 1963; an exact replica of the main halls (Lascaux II) opened in 1983; later fungal outbreaks (1990s/2001).
Photos (Wikimedia Commons, public domain): Lascaux painting (aurochs/horses), Lascaux horse, Lascaux replica (Brno, Anthropos museum, by HTO).
Map: NASA Blue Marble + Natural Earth (public domain).
"""
import math, os
from cartoon import *
import globe
from episodes_util import paint_rgba
from PIL import Image

NAME = "forbidden_02_lascaux"
LOOK = "cinematic"
TITLE = "This cave was closed because of our BREATH 🫁 #shorts"
DESCRIPTION = ("17,000-year-old paintings survived the Ice Age... then visitors' breath nearly destroyed them. "
               "#history #france #mystery #forbiddenplaces #shorts\n\n"
               "Photos: Wikimedia Commons (public domain). Map: NASA, Natural Earth (public domain).")
TAGS = ["lascaux", "cave paintings", "forbidden places", "history", "france", "shorts"]
VOICE, SPEED = "am_michael", 1.05
HOOK = ("THIS CAVE WAS CLOSED", "BECAUSE OF OUR BREATH")
BEATS = [
    ("hook", "This cave was closed... because our breath was destroying it.", 0.3),
    ("find", "In 1940, a group of teenagers found it in France. Its walls were covered in paintings, around seventeen thousand years old.", 0.0),
    ("crowds", "It opened to the public in 1948, and huge crowds poured in.", 0.0),
    ("damage", "But every visitor breathed out carbon dioxide, heat and moisture. And in 1962, green slime started spreading across the walls.", 0.2),
    ("closed", "So in 1963, France locked the door.", 0.3),
    ("today", "Today, visitors see an exact copy instead, while the real cave stays sealed in the dark.", 0.0),
    ("end", "Seventeen thousand years it survived... until us. Would you still want to go in?", 1.0),
]
DIR = os.path.join(ROOT, "assets", "forbidden")
PH = {"wall": ("Lascaux_painting.jpg", "Photo: Wikimedia Commons, public domain"),
      "horse": ("Lascaux2.jpg", "Photo: Wikimedia Commons, public domain"),
      "replica": ("Lascaux,_replica_03.JPG", "Replica (Anthropos museum, Brno) · Photo: HTO, public domain")}
_S = {}
def surf(key, grey=False):
    k = (key, grey)
    if k not in _S:
        im = Image.open(os.path.join(DIR, PH[key][0])).convert("RGB"); im.thumbnail((2000, 2000)); a = np.asarray(im)
        if grey: g = a.mean(axis=2, keepdims=True).astype(np.uint8); a = np.repeat(g, 3, axis=2)
        bgra = np.dstack([a[..., ::-1], np.full(a.shape[:2], 255, np.uint8)])
        _S[k] = (cairo.ImageSurface.create_for_data(bytearray(np.ascontiguousarray(bgra).tobytes()), cairo.FORMAT_RGB24, im.width, im.height), im.width, im.height)
    return _S[k]

def photo(c, key, x, y, w, h, zoom=1.0, focus=(0.5, 0.5), alpha=1.0, grey=False):
    S, iw, ih = surf(key, grey); s = max(w / iw, h / ih) * zoom
    ox = x + w / 2 - focus[0] * iw * s; oy = y + h / 2 - focus[1] * ih * s
    ox = min(x, max(x + w - iw * s, ox)); oy = min(y, max(y + h - ih * s, oy))
    c.save(); c.new_path(); c.rectangle(x, y, w, h); c.clip(); c.translate(ox, oy); c.scale(s, s)
    c.set_source_surface(S); c.get_source().set_filter(cairo.FILTER_GOOD); c.paint_with_alpha(alpha); c.restore()

def full(c, s, key, z0, z1, focus, dur=4.0, grey=False):
    z = lerp(z0, z1, clamp((s.t - s.t0) / dur))
    photo(c, key, 0, 0, W, H, z, focus, grey=grey)
    c.save(); c.identity_matrix(); g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgba(0, 0, 0, 0, 0.55); g.add_color_stop_rgba(0.35, 0, 0, 0, 0.0); g.add_color_stop_rgba(0.65, 0, 0, 0, 0.0); g.add_color_stop_rgba(1, 0, 0, 0, 0.65)
    c.set_source(g); c.paint(); c.restore()
    text(c, PH[key][1], W / 2, 1880, 26, WHITE, alpha=0.8)

def stamp(c, txt, x, y, size, p, col=RED, rot=-0.18):
    if p <= 0: return
    k = 1 + 0.6 * (1 - ease_out(p)); c.save(); c.translate(x, y); c.rotate(rot); c.scale(k, k)
    c.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(size); e = c.text_extents(txt)
    c.new_path(); rrect(c, -e.x_advance / 2 - 30, -size * 0.75, e.x_advance + 60, size * 1.5, 14)
    c.set_source_rgba(*col, min(1, p * 1.5)); c.set_line_width(10); c.stroke()
    c.move_to(-e.x_advance / 2, size * 0.36); c.set_source_rgba(*col, min(1, p * 1.5)); c.show_text(txt); c.restore()


def full(c, s, key, z0, z1, focus, dur=4.0):
    z = lerp(z0, z1, clamp((s.t - s.t0) / dur))
    photo(c, key, 0, 0, W, H, z, focus)
    c.save(); c.identity_matrix(); g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgba(0, 0, 0, 0, 0.6); g.add_color_stop_rgba(0.35, 0, 0, 0, 0.0); g.add_color_stop_rgba(0.65, 0, 0, 0, 0.0); g.add_color_stop_rgba(1, 0, 0, 0, 0.7)
    c.set_source(g); c.paint(); c.restore()
    text(c, PH[key][1], W / 2, 1880, 26, WHITE, alpha=0.8)

def framed(c, key, cx, cy, w, h, p=1.0, rot=0.0, zoom=1.0, focus=(0.5, 0.5)):
    if p <= 0: return
    k = ease_back(p); c.save(); c.translate(cx, cy); c.rotate(rot); c.scale(k, k)
    c.new_path(); c.rectangle(-w / 2 - 14 + 12, -h / 2 - 14 + 16, w + 28, h + 28); c.set_source_rgba(0, 0, 0, 0.5); c.fill()
    c.new_path(); c.rectangle(-w / 2 - 14, -h / 2 - 14, w + 28, h + 28); c.set_source_rgb(0.95, 0.93, 0.88); c.fill()
    photo(c, key, -w / 2, -h / 2, w, h, zoom, focus); c.restore()

def breath(c, t, t0, n=26, strength=1.0):
    """drifting breath clouds + CO2 bubbles floating toward the wall"""
    if t < t0: return
    for k in range(n):
        u = ((t - t0) * 0.25 + k / n) % 1; x = 100 + (k * 137) % 880; y = 1500 - u * 1200
        a = strength * math.sin(math.pi * u)
        cloud(c, x + math.sin(t + k) * 30, y, 34 + (k % 4) * 10, (0.9, 0.95, 1), 0.18 * a)
        if k % 3 == 0: text(c, "CO2", x, y - 50, 30, (0.85, 0.95, 1), outline=None, alpha=0.7 * a)

def slime(c, t, g, seed=3):
    """green algae blotches spreading over the painting (g = 0..1 growth)"""
    if g <= 0: return
    rng = np.random.default_rng(seed)
    for k in range(34):
        x, y, r = rng.uniform(40, 1040), rng.uniform(280, 1350), rng.uniform(40, 120)
        gk = clamp(g * 1.6 - k / 34)
        if gk > 0:
            c.new_path(); path(c, blob(x, y, r * gk, k + 50, 0.45)); c.set_source_rgba(0.25, 0.6, 0.2, 0.55 * gk); c.fill()

def earth(c, t, lon0, lat0, R, cy=1000):
    bg_cinema(c, t); paint_rgba(c, globe.render_globe(lon0, lat0, R, W / 2, cy, sun=(-0.35, 0.4, 0.85)))

# ---------------- scenes
def s_hook(c, s):
    t = s.t
    full(c, s, "replica", 1.0, 1.12, (0.55, 0.45), 4.0)
    breath(c, t, -2.0, 20, 0.9)
    stamp(c, "CLOSED", W / 2, 1180, 120, s.P(s.W("hook", "closed") - 0.1, 0.3))

def s_find(c, s):
    t = s.t; tf = s.W("find", "France"); tp = s.W("find", "paintings"); ty = s.W("find", "seventeen")
    if t < tp - 0.3:
        u = clamp((t - s.t0) / 2.0); lon0 = lerp(-20, 1.17, ease(u)); lat0 = lerp(30, 45.05, ease(u)); R = lerp(700, 2600, ease(u))
        earth(c, t, lon0, lat0, R)
        globe.fill_region(c, globe.rings("France"), lon0, lat0, R, rgb("#3fa9ff"), 0.5, W / 2, 1000)
        x, y, vis = globe.lonlat_to_screen(1.17, 45.05, lon0, lat0, R, W / 2, 1000)
        if vis:
            glow(c, x, y, 160, (1, 0.8, 0.4), 0.6); circle(c, x, y, 16, YEL, 6)
            if t > tf - 0.3: label(c, "LASCAUX, FRANCE", x, y - 100, 54, WHITE, OUT, s.P(tf - 0.3, 0.3))
        pop_text(c, "1940", W / 2, 420, 120, s.P(s.t0, 0.3), YEL)
    else:
        bg_cinema(c, t, seed=13, top="#0a0705", bot="#2a1a0e", neb=(("#5a3a1a", 0.4), ("#3a2a1a", 0.3), ("#6a4a2a", 0.2)))
        framed(c, "wall", W / 2, 760, 980, 640, s.P(tp - 0.3, 0.35), -0.02)
        if t > ty - 0.2:
            yrs = 17000 * ease(clamp((t - ty + 0.2) / 1.0))
            text(c, f"~{yrs:,.0f} YEARS OLD", W / 2, 1210, 84, YEL)
        text(c, PH["wall"][1], W / 2, 1880, 26, WHITE, alpha=0.8)

def s_crowds(c, s):
    t = s.t; tc = s.W("crowds", "crowds")
    full(c, s, "replica", 1.1, 1.2, (0.5, 0.5), 4.0)
    pop_text(c, "OPENED 1948", W / 2, 400, 100, s.P(s.t0 + 0.1, 0.3), WHITE)
    if t > tc - 0.3:   # crowd of little visitor heads filling the bottom of the frame
        p = ease(clamp((t - tc + 0.3) / 1.2)); rng = np.random.default_rng(4)
        for k in range(int(60 * p)):
            x, y = rng.uniform(20, 1060), rng.uniform(1450, 1800)
            circle(c, x, y - 40, 26, rgb("#f2c9a0"), 4); c.new_path(); rrect(c, x - 34, y - 14, 68, 90, 24); fs(c, [RED, BLUE, YEL, GREEN][k % 4], 4)

def s_damage(c, s):
    t = s.t; tco = s.W("damage", "carbon"); tg = s.W("damage", "green")
    bg_cinema(c, t, seed=13, top="#0a0705", bot="#2a1a0e", neb=(("#5a3a1a", 0.4), ("#3a2a1a", 0.3), ("#6a4a2a", 0.2)))
    framed(c, "horse", W / 2, 780, 980, 740, 1.0, 0.0, 1.05)
    breath(c, t, tco - 0.5, 28, 1.0)
    for i, (lab, tw) in enumerate((("CO2", "carbon"), ("HEAT", "heat"), ("MOISTURE", "moisture"))):
        label(c, lab, 200 + i * 340, 330, 50, [SKY, ORANGE, CYAN][i], OUT, s.P(s.W("damage", tw) - 0.15, 0.3))
    g = clamp((t - tg + 0.3) / 2.5); slime(c, t, g)
    if t > tg - 0.2: pop_text(c, "1962: GREEN SLIME", W / 2, 1225, 62, s.P(tg - 0.2, 0.3), GREEN)
    text(c, PH["horse"][1], W / 2, 1880, 26, WHITE, alpha=0.8)

def s_closed(c, s):
    t = s.t; tl = s.W("closed", "locked")
    bg_cinema(c, t, seed=13, top="#0a0705", bot="#2a1a0e", neb=(("#5a3a1a", 0.4), ("#3a2a1a", 0.3), ("#6a4a2a", 0.2)))
    framed(c, "horse", W / 2, 780, 980, 740, 1.0, 0.0, 1.05)
    slime(c, t, 1.0)
    # a heavy door slides shut over the painting
    d = ease(clamp((t - tl + 0.3) / 0.6))
    c.new_path(); c.rectangle(0, 380, W * d / 2, 800); fs(c, rgb("#3a3f4a"), 8); c.new_path(); c.rectangle(W - W * d / 2, 380, W * d / 2, 800); fs(c, rgb("#3a3f4a"), 8)
    if d >= 1: circle(c, W / 2, 780, 46, YEL, 7)
    stamp(c, "1963: LOCKED", W / 2, 1215, 90, s.P(tl, 0.3))

def s_today(c, s):
    t = s.t; tc = s.W("today", "copy"); td = s.W("today", "dark")
    full(c, s, "replica", 1.0, 1.15, (0.5, 0.5), 5.0)
    label(c, "WHAT VISITORS SEE: A REPLICA", W / 2, 400, 48, YEL, OUT, s.P(tc - 0.2, 0.3))
    if t > td - 0.4:
        c.save(); c.identity_matrix(); c.set_source_rgba(0, 0, 0, 0.85 * clamp((t - td + 0.4) / 0.8)); c.paint(); c.restore()
        pop_text(c, "THE REAL CAVE: SEALED", W / 2, 960, 78, s.P(td - 0.2, 0.3), WHITE)

def s_end(c, s):
    t = s.t; tq = s.W("end", "Would")
    full(c, s, "replica", 1.12, 1.0, (0.55, 0.45), 4.0)
    breath(c, t, s.t0, 20, 0.8)
    stamp(c, "CLOSED", W / 2, 1180, 120, 1.0)
    pop_text(c, "WOULD YOU GO IN?", W / 2, 420, 90, s.P(tq, 0.3), YEL)

SCENES = [("hook", s_hook), ("find", s_find), ("crowds", s_crowds), ("damage", s_damage), ("closed", s_closed), ("today", s_today), ("end", s_end)]

def impacts(Wt, B):
    return [Wt("hook", "closed"), Wt("closed", "locked")]

def sfx(Wt, B, put):
    put(sfx_boom(38, 2.2), 0.0, 0.5); put(sfx_whoosh(2, 2.0), 0.2, 0.3)
    put(sfx_whoosh(5, 1.6), Wt("find"), 0.5); put(sfx_ding(1500), Wt("find", "France"), 0.4)
    for i in range(10): put(sfx_tick(), Wt("find", "seventeen") + i * 0.1, 0.35)
    for i in range(6): put(sfx_pop(400 + 80 * i), Wt("crowds", "crowds") + i * 0.18, 0.3)
    put(sfx_whoosh(9, 2.2), Wt("damage", "breathed"), 0.5)
    put(sfx_boom(50, 0.8), Wt("damage", "green"), 0.5)
    put(sfx_boom(35, 1.6), Wt("closed", "locked"), 0.9)
    put(sfx_ding(1320), Wt("end", "Would"), 0.5)
