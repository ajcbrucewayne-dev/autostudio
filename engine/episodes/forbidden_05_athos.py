"""Off The Map #5 (Forbidden): Mount Athos, the mountain no woman may enter.
Facts (checked, hedged where sources differ):
- The "avaton" bans women from the whole Athos peninsula (northern Greece); it has lasted over 1,000 years (no exact start date used).
- Female farm animals are traditionally banned too; cats are the well-known exception (they keep mice down); wild animals can't be policed.
- Boats carrying women must stay at least 500 m from the coast.
- Legend: the Virgin Mary landed here and claimed it as her garden, so she is the only woman who belongs there (told as legend).
- 20 monasteries, roughly 2,000 monks.
- 1953: a woman (Maria Poimenidou) entered dressed as a man and stayed about 3 days; Greece then made it a crime
  (Legislative Decree 2623/1953, prison of 2 months to 1 year).
- Men need a permit (diamonitirion); only around 100 Orthodox + 10 non-Orthodox pilgrims a day (sources vary, so "around a hundred").
Map: NASA Blue Marble + Natural Earth (public domain). Photos: Wikimedia Commons, credited on screen + in the description.
"""
import math, os
from cartoon import *
import globe
from episodes_util import paint_rgba
from PIL import Image

NAME = "forbidden_05_athos"
LOOK = "cinematic"
TITLE = "The mountain no woman may enter 🚫 #shorts"
DESCRIPTION = ("No woman has been allowed on Mount Athos for over 1,000 years. Not even female animals. Here's why. "
               "#history #greece #mystery #forbiddenplaces #offthemap #shorts\n\n"
               "Map: NASA, Natural Earth (public domain).\nPhotos (Wikimedia Commons): Simonopetra by Thodoris Lakiotis, CC BY-SA 3.0 "
               "(creativecommons.org/licenses/by-sa/3.0); Simonopetra Monastery, public domain."
               "\nMusic: \"Lightless Dawn\" by Kevin MacLeod (incompetech.com), CC BY 3.0 (creativecommons.org/licenses/by/3.0).")
MUSIC = "assets/music/Lightless_Dawn_(ISRC_USUAN1100655).mp3"
TAGS = ["mount athos", "forbidden places", "greece", "history", "off the map", "shorts"]
VOICE, SPEED = "am_michael", 1.06
HOOK = ("NO WOMEN FOR 1,000+ YEARS", "NOT EVEN HENS")
BEATS = [
    ("hook", "No woman has set foot here in over a thousand years. Not even hens.", 0.3),
    ("where", "This is Mount Athos in Greece. A strip of land run by monks, with twenty monasteries and around two thousand men.", 0.0),
    ("animals", "Female animals are banned too. No cows. No hens. The only exception? Cats, because they catch the mice.", 0.2),
    ("boats", "Even boats carrying women have to stay five hundred meters away from the shore.", 0.2),
    ("why", "So why? Legend says the Virgin Mary landed here, and claimed the mountain as her garden. So she's the only woman who belongs here.", 0.2),
    ("broke", "In 1953, a woman dressed as a man sneaked in and stayed for three days. After that, Greece made it a crime, with up to a year in prison.", 0.2),
    ("today", "Even men need a special permit, and only around a hundred pilgrims get in each day.", 0.0),
    ("end", "A place where half the world isn't allowed... Would you go?", 1.0),
]
CAPTION_Y = 1450
DIR = os.path.join(ROOT, "assets", "athos")
PH = {}          # filled from the fetched files below
def _pick(sub, credit):
    for f in sorted(os.listdir(DIR)) if os.path.isdir(DIR) else []:
        if sub.lower() in f.lower(): return (f, credit)
    return None

# ---------------- photos
_S = {}
def surf(key):
    if key not in _S:
        im = Image.open(os.path.join(DIR, PH[key][0])).convert("RGB"); im.thumbnail((2000, 2000)); a = np.asarray(im)
        bgra = np.dstack([a[..., ::-1], np.full(a.shape[:2], 255, np.uint8)])
        _S[key] = (cairo.ImageSurface.create_for_data(bytearray(np.ascontiguousarray(bgra).tobytes()), cairo.FORMAT_RGB24, im.width, im.height), im.width, im.height)
    return _S[key]

def photo(c, key, x, y, w, h, zoom=1.0, focus=(0.5, 0.5), alpha=1.0):
    S, iw, ih = surf(key); s = max(w / iw, h / ih) * zoom
    ox = x + w / 2 - focus[0] * iw * s; oy = y + h / 2 - focus[1] * ih * s
    ox = min(x, max(x + w - iw * s, ox)); oy = min(y, max(y + h - ih * s, oy))
    c.save(); c.new_path(); c.rectangle(x, y, w, h); c.clip(); c.translate(ox, oy); c.scale(s, s)
    c.set_source_surface(S); c.get_source().set_filter(cairo.FILTER_GOOD); c.paint_with_alpha(alpha); c.restore()

def full(c, s, key, z0, z1, focus=(0.5, 0.5), dur=4.0):
    photo(c, key, 0, 0, W, H, lerp(z0, z1, clamp((s.t - s.t0) / dur)), focus)
    c.save(); c.identity_matrix(); g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgba(0, 0, 0, 0, 0.6); g.add_color_stop_rgba(0.3, 0, 0, 0, 0.0); g.add_color_stop_rgba(0.62, 0, 0, 0, 0.0); g.add_color_stop_rgba(1, 0, 0, 0, 0.75)
    c.set_source(g); c.paint(); c.restore()
    credit(c, key)

def credit(c, key): text(c, PH[key][1], W / 2, 1885, 24, WHITE, alpha=0.8)

def stamp(c, txt, x, y, size, p, col=RED, rot=-0.15):
    if p <= 0: return
    k = 1 + 0.6 * (1 - ease_out(p)); c.save(); c.translate(x, y); c.rotate(rot); c.scale(k, k)
    c.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(size); e = c.text_extents(txt)
    c.new_path(); rrect(c, -e.x_advance / 2 - 30, -size * 0.75, e.x_advance + 60, size * 1.5, 14)
    c.set_source_rgba(0, 0, 0, 0.35 * min(1, p * 1.5)); c.fill_preserve()
    c.set_source_rgba(*col, min(1, p * 1.5)); c.set_line_width(10); c.stroke()
    c.move_to(-e.x_advance / 2, size * 0.36); c.show_text(txt); c.restore()

def xmark(c, x, y, r, p, col=RED, w=16):
    if p <= 0: return
    a = ease_out(clamp(p * 2)); b = ease_out(clamp(p * 2 - 1))
    c.set_line_cap(1); c.set_source_rgb(*col); c.set_line_width(w)
    c.new_path(); c.move_to(x - r, y - r); c.line_to(x - r + 2 * r * a, y - r + 2 * r * a); c.stroke()
    if b > 0: c.new_path(); c.move_to(x + r, y - r); c.line_to(x + r - 2 * r * b, y - r + 2 * r * b); c.stroke()

def tick(c, x, y, r, p, col=GREEN, w=16):
    if p <= 0: return
    q = ease_out(p); pts = [(x - r, y), (x - r * 0.3, y + r * 0.7), (x + r, y - r * 0.8)]
    c.set_line_cap(1); c.set_line_join(1); c.set_source_rgb(*col); c.set_line_width(w); c.new_path(); c.move_to(*pts[0])
    if q < 0.4: c.line_to(lerp(pts[0][0], pts[1][0], q / 0.4), lerp(pts[0][1], pts[1][1], q / 0.4))
    else: c.line_to(*pts[1]); u = (q - 0.4) / 0.6; c.line_to(lerp(pts[1][0], pts[2][0], u), lerp(pts[1][1], pts[2][1], u))
    c.stroke()

def bg(c, t, seed=21):
    bg_cinema(c, t, seed=seed, top="#05080f", bot="#1a2336", neb=(("#2a4a7a", 0.35), ("#5a3a6a", 0.25), ("#2a6a7a", 0.2)))

def woman(c, x, y, s=1.0, col=(0.95, 0.45, 0.55)):
    """simple figure: head + dress (trapezoid)"""
    circle(c, x, y - 70 * s, 26 * s, rgb("#f2c9a0"), 4)
    c.new_path(); c.move_to(x - 22 * s, y - 40 * s); c.line_to(x + 22 * s, y - 40 * s); c.line_to(x + 40 * s, y + 40 * s); c.line_to(x - 40 * s, y + 40 * s); c.close_path(); fs(c, col, 4)

def man(c, x, y, s=1.0, col=(0.2, 0.2, 0.25), beard=True):
    circle(c, x, y - 70 * s, 26 * s, rgb("#f2c9a0"), 4)
    if beard: c.new_path(); c.arc(x, y - 62 * s, 22 * s, 0.2, math.pi - 0.2); fs(c, rgb("#555555"), 0)
    c.new_path(); rrect(c, x - 30 * s, y - 42 * s, 60 * s, 84 * s, 18 * s); fs(c, col, 4)

# ---------------- map
ATHOS = [np.array([(23.99, 40.42), (24.03, 40.41), (24.21, 40.33), (24.29, 40.24), (24.34, 40.15), (24.23, 40.22),
                   (24.16, 40.28), (24.06, 40.30), (23.97, 40.35)], np.float32)]
def earth(c, t, lon0, lat0, R, cy=1000):
    bg(c, t); paint_rgba(c, globe.render_globe(lon0, lat0, R, W / 2, cy, sun=(-0.35, 0.4, 0.85)))

def s_hook(c, s):
    t = s.t; tj = s.W("hook", "hens")
    full(c, s, "mon", 1.35 - 0.2 * ease_out(clamp(t / 0.6)), 1.15, (0.45, 0.5), 5.0)
    p = ease_back(clamp(t / 0.35))                   # a big no-entry sign slams on from frame 1
    c.save(); c.translate(540, 1000); c.scale(p, p)
    c.new_path(); c.arc(0, 0, 250, 0, 2 * math.pi); c.set_source_rgba(1, 1, 1, 0.85); c.fill()
    woman(c, 0, 70, 3.0)
    c.new_path(); c.arc(0, 0, 250, 0, 2 * math.pi); c.set_source_rgb(*RED); c.set_line_width(44); c.stroke()
    d = ease_out(clamp((t - 0.3) / 0.25)); c.new_path(); c.move_to(-177, -177); c.line_to(-177 + 354 * d, -177 + 354 * d); c.set_line_width(44); c.stroke()
    c.restore()
    stamp(c, "NO WOMEN", W / 2, 620, 96, clamp((t - 0.55) / 0.25))
    if t > tj - 0.3:                                 # "Not even hens" -> a hen gets banned too
        q = s.P(tj - 0.3, 0.35); hen(c, 840, 1290, 1.3 * ease_back(q)); xmark(c, 860, 1270, 100, clamp((t - tj) / 0.35), RED, 14)

def hen(c, x, y, s=1.0):
    if s <= 0: return
    c.new_path(); c.arc(x, y, 60 * s, 0, 2 * math.pi); fs(c, WHITE, 4)
    circle(c, x + 50 * s, y - 50 * s, 32 * s, WHITE, 4)
    c.new_path(); path(c, [(x + 40 * s, y - 82 * s), (x + 50 * s, y - 100 * s), (x + 60 * s, y - 84 * s), (x + 72 * s, y - 96 * s), (x + 76 * s, y - 74 * s)]); fs(c, RED, 3)
    c.new_path(); c.move_to(x + 80 * s, y - 52 * s); c.line_to(x + 104 * s, y - 44 * s); c.line_to(x + 80 * s, y - 36 * s); c.close_path(); fs(c, ORANGE, 3)
    circle(c, x + 58 * s, y - 56 * s, 5 * s, OUT, 0)

def cow(c, x, y, s=1.0):
    if s <= 0: return
    for lx in (-70, -40, 15, 45): c.new_path(); rrect(c, x + lx * s - 9 * s, y + 20 * s, 18 * s, 55 * s, 6 * s); fs(c, WHITE, 3)
    c.new_path(); rrect(c, x - 95 * s, y - 45 * s, 160 * s, 85 * s, 36 * s); fs(c, WHITE, 4)
    circle(c, x - 50 * s, y - 15 * s, 18 * s, rgb("#3a3a3a"), 0); circle(c, x + 10 * s, y + 10 * s, 13 * s, rgb("#3a3a3a"), 0)
    for sx in (-1, 1): c.new_path(); path(c, [(x + (78 + sx * 22) * s, y - 82 * s), (x + (78 + sx * 36) * s, y - 104 * s), (x + (78 + sx * 30) * s, y - 76 * s)]); fs(c, rgb("#e8d9a8"), 3)
    c.new_path(); c.arc(x + 78 * s, y - 55 * s, 36 * s, 0, 2 * math.pi); fs(c, WHITE, 4)
    c.new_path(); rrect(c, x + 52 * s, y - 40 * s, 52 * s, 30 * s, 14 * s); fs(c, rgb("#f4a9b8"), 3)
    for sx in (-1, 1): circle(c, x + (78 + sx * 14) * s, y - 66 * s, 5 * s, OUT, 0)

def cat(c, x, y, s=1.0):
    if s <= 0: return
    col = rgb("#f0a040")
    for sx in (-1, 1): c.new_path(); path(c, [(x + sx * 20 * s, y - 50 * s), (x + sx * 55 * s, y - 100 * s), (x + sx * 62 * s, y - 30 * s)]); fs(c, col, 4)
    circle(c, x, y - 20 * s, 66 * s, col, 4)
    for sx in (-1, 1): circle(c, x + sx * 24 * s, y - 30 * s, 9 * s, OUT, 0)
    c.new_path(); c.move_to(x - 8 * s, y - 8 * s); c.line_to(x + 8 * s, y - 8 * s); c.line_to(x, y + 2 * s); c.close_path(); fs(c, rgb("#e06080"), 0)

def s_where(c, s):
    t = s.t; tg = s.W("where", "Greece"); tm = s.W("where", "twenty"); tk = s.W("where", "two")
    u = clamp((t - s.t0) / 2.6); lon0 = lerp(10, 24.15, ease(u)); lat0 = lerp(48, 40.3, ease(u)); R = lerp(900, 4200, ease(u) ** 1.5)
    earth(c, t, lon0, lat0, R)
    globe.fill_region(c, globe.rings("Greece"), lon0, lat0, R, rgb("#3fa9ff"), 0.35 * clamp((t - tg + 0.3) / 0.5), W / 2, 1000)
    globe.fill_region(c, ATHOS, lon0, lat0, R, YEL, 0.85 * clamp((t - s.t0 - 1.6) / 0.5), W / 2, 1000, glow_w=30)
    x, y, vis = globe.lonlat_to_screen(24.33, 40.16, lon0, lat0, R, W / 2, 1000)
    if vis and t > s.t0 + 1.4:                     # pulsing ring + callout so the tiny peninsula is easy to spot
        q = s.P(s.t0 + 1.4, 0.4); x2, y2, _ = globe.lonlat_to_screen(24.15, 40.28, lon0, lat0, R, W / 2, 1000)
        ring(c, x2, y2, (70 + 8 * math.sin(t * 5)) * ease_back(q), YEL, 8)
        if t > tg - 0.3:
            c.new_path(); c.move_to(x2, y2 - 75); c.line_to(x2, 650); c.set_source_rgba(1, 1, 1, 0.9 * s.P(tg - 0.3, 0.3)); c.set_line_width(5); c.stroke()
    if t > tg - 0.3: label(c, "MOUNT ATHOS, GREECE", W / 2, 600, 62, WHITE, OUT, s.P(tg - 0.3, 0.3))
    if t > tm - 0.3:    # 20 monastery dots around the peninsula
        rng = np.random.default_rng(7)
        for k in range(20):
            f = rng.uniform(0.05, 0.95); side = rng.choice([-1, 1])
            lo = lerp(24.0, 24.32, f) + side * 0.02; la = lerp(40.38, 40.17, f) + side * 0.025
            px, py, v = globe.lonlat_to_screen(lo, la, lon0, lat0, R, W / 2, 1000)
            q = s.P(tm - 0.3 + k * 0.05, 0.25)
            if v and q > 0: circle(c, px, py, 9 * ease_back(q), WHITE, 3)
        pop_text(c, "20 MONASTERIES", W / 2, 1220, 80, s.P(tm - 0.2, 0.3), YEL)
    if t > tk - 0.2: pop_text(c, "~2,000 MONKS. 0 WOMEN.", W / 2, 1320, 62, s.P(tk - 0.2, 0.3), WHITE)

def card(c, x, y, p, draw, ok):
    if p <= 0: return
    k = 1.45 * ease_back(p); c.save(); c.translate(x, y); c.scale(k, k)
    c.new_path(); rrect(c, -150, -160, 300, 320, 36); c.set_source_rgba(0, 0, 0, 0.45); c.fill_preserve()
    c.set_source_rgb(*(GREEN if ok else RED)); c.set_line_width(8); c.stroke()
    draw(c, 0, 10); c.restore()

def s_animals(c, s):
    t = s.t; tc = s.W("animals", "cows"); th = s.W("animals", "hens"); tx = s.W("animals", "Cats"); tm = s.W("animals", "mice")
    bg(c, t, 22)
    pop_text(c, "FEMALE ANIMALS: BANNED", W / 2, 330, 70, s.P(s.t0 + 0.1, 0.3), RED)
    card(c, 280, 640, s.P(tc - 0.25, 0.35), lambda c, x, y: cow(c, x - 10, y + 20, 1.0), False)
    xmark(c, 280, 640, 170, clamp((t - tc) / 0.35), RED, 14)
    card(c, 800, 640, s.P(th - 0.25, 0.35), lambda c, x, y: hen(c, x - 30, y + 20, 1.1), False)
    xmark(c, 800, 640, 170, clamp((t - th) / 0.35), RED, 14)
    if t > tx - 0.3:
        c.save(); c.translate(0, 0); card(c, 540, 1130, s.P(tx - 0.3, 0.4), lambda c, x, y: cat(c, x, y + 20, 1.2), True); c.restore()
        tick(c, 720, 1010, 60, clamp((t - tx) / 0.4))
        label(c, "EXCEPTION", 540, 880, 50, GREEN, OUT, s.P(tx - 0.1, 0.3))
    if t > tm - 0.3:      # a little mouse scurries away
        mx = lerp(1150, 760, ease_out(clamp((t - tm + 0.3) / 0.8)))
        c.new_path(); c.arc(mx, 1250, 30, 0, 2 * math.pi); fs(c, rgb("#9a9aa6"), 3); circle(c, mx - 30, 1230, 14, rgb("#9a9aa6"), 3)

def s_boats(c, s):
    t = s.t; tf = s.W("boats", "five"); ts = s.W("boats", "shore")
    # top-down coast: sea on the left, peninsula land on the right
    c.new_path(); c.rectangle(0, 0, W, H); c.set_source_rgb(*rgb("#0d3a5c")); c.fill()
    for k in range(14):      # wave lines
        y = (k * 150 + t * 40) % H; c.new_path(); c.move_to(0, y)
        for x in range(0, W + 40, 40): c.line_to(x, y + 8 * math.sin(x / 60 + t * 2))
        c.set_source_rgba(1, 1, 1, 0.06); c.set_line_width(3); c.stroke()
    shore = lambda y: 820 + 60 * math.sin(y / 180) + 30 * math.sin(y / 70)
    c.new_path(); c.move_to(W, 0); c.line_to(shore(0), 0)
    for y in range(0, H + 20, 20): c.line_to(shore(y), y)
    c.line_to(W, H); c.close_path(); fs(c, rgb("#3d6b35"), 0)
    c.new_path(); c.move_to(shore(0), 0)
    for y in range(0, H + 20, 20): c.line_to(shore(y), y)
    c.set_source_rgb(*rgb("#e8d9a8")); c.set_line_width(18); c.stroke()
    lim = 300                                      # the 500 m line
    d = clamp((t - tf + 0.4) / 0.6)
    if d > 0:
        c.save(); c.set_dash([30, 20]); c.new_path(); c.move_to(lim, 0); c.line_to(lim, H * ease(d)); c.set_source_rgb(*RED); c.set_line_width(8); c.stroke(); c.restore()
        arrow(c, (lim + 20, 1250), (shore(1250) - 30, 1250), s.P(tf, 0.4), YEL, 8, 24); arrow(c, (shore(1250) - 30, 1250), (lim + 20, 1250), s.P(tf, 0.4), YEL, 8, 24)
        label(c, "500 M", (lim + shore(1250)) / 2, 1180, 56, YEL, OUT, s.P(tf + 0.1, 0.3))
    # boat sails toward the shore, then is stopped at the line
    bx = lerp(-300, lim - 170, ease_out(clamp((t - s.t0) / 2.2))); by = 950 + 6 * math.sin(t * 3)
    c.new_path(); c.move_to(bx - 170, by - 50); c.line_to(bx + 170, by - 50); c.line_to(bx + 130, by + 55); c.line_to(bx - 130, by + 55); c.close_path(); fs(c, WHITE, 6)
    for k, dx in enumerate((-80, 0, 80)): woman(c, bx + dx, by - 75, 1.0, [(0.95, 0.45, 0.55), (0.6, 0.4, 0.9), (0.95, 0.7, 0.2)][k])
    label(c, "WOMEN ON BOARD", max(bx, 200), by + 130, 40, WHITE, OUT, s.P(s.t0 + 0.4, 0.3))
    if t > ts - 0.4: stamp(c, "STOP", lim - 20, 700, 100, s.P(ts - 0.4, 0.3))
    pop_text(c, "THE RULE REACHES THE SEA", W / 2, 360, 62, s.P(s.t0 + 0.1, 0.3), WHITE)

def mountain(c, t, glowp=0.0, bloom=0.0):
    c.new_path(); c.move_to(80, 1300); c.line_to(540, 520); c.line_to(1000, 1300); c.close_path(); fs(c, rgb("#4a5a6a"), 0)
    c.new_path(); c.move_to(450, 673); c.line_to(540, 520); c.line_to(630, 673); c.line_to(580, 640); c.line_to(540, 690); c.line_to(500, 640); c.close_path(); fs(c, WHITE, 0)
    c.new_path(); c.rectangle(0, 1300, W, 620); c.set_source_rgb(*rgb("#0d3a5c")); c.fill()
    if bloom > 0:         # garden: flowers and trees spread up the mountain
        rng = np.random.default_rng(11)
        for k in range(46):
            x = rng.uniform(150, 930); y = rng.uniform(800, 1290)
            if abs(x - 540) > (y - 520) * 0.59: continue
            q = clamp(bloom * 1.6 - k / 46)
            if q > 0:
                if k % 3: circle(c, x, y, 14 * ease_back(q), [rgb("#ff7aa8"), YEL, WHITE, rgb("#c58cff")][k % 4], 0)
                else: c.new_path(); c.arc(x, y, 26 * ease_back(q), 0, 2 * math.pi); fs(c, rgb("#2f8a3a"), 0)

def s_why(c, s):
    t = s.t; tl = s.W("why", "landed"); tg = s.W("why", "garden"); to = s.W("why", "only")
    bg(c, t, 23)
    pop_text(c, "THE LEGEND", W / 2, 360, 80, s.P(s.t0 + 0.1, 0.3), YEL)
    mountain(c, t, bloom=clamp((t - tg + 0.3) / 1.6))
    # a small boat glides in on "landed", with a glowing figure
    bp = ease_out(clamp((t - tl + 1.0) / 1.2)); bx = lerp(-200, 380, bp); by = 1330
    c.new_path(); c.move_to(bx - 90, by - 30); c.line_to(bx + 90, by - 30); c.line_to(bx + 65, by + 25); c.line_to(bx - 65, by + 25); c.close_path(); fs(c, rgb("#8a5a3a"), 4)
    if bp > 0: glow(c, bx, by - 90, 140, (1, 0.9, 0.6), 0.7); woman(c, bx, by - 40, 0.9, (0.35, 0.55, 0.95))
    if t > tg - 0.2: label(c, "\"MY GARDEN\"", W / 2, 470, 54, WHITE, OUT, s.P(tg - 0.2, 0.3))
    if t > to - 0.3: pop_text(c, "THE ONLY WOMAN", W / 2, 1640, 74, s.P(to - 0.3, 0.3), YEL)

def s_broke(c, s):
    t = s.t; td = s.W("broke", "dressed"); tt = s.W("broke", "three"); tc = s.W("broke", "crime"); ty = s.W("broke", "year")
    bg(c, t, 24)
    pop_text(c, "1953", W / 2, 360, 120, s.P(s.t0, 0.3), YEL)
    if t < tc - 0.3:
        dp = ease(clamp((t - td + 0.2) / 0.6))       # her dress morphs into a man's coat + hat + fake moustache
        x, y = 540, 1020
        if dp < 1: woman(c, x, y, 3.0)
        if dp > 0:
            c.save(); c.push_group(); man(c, x, y, 3.0, rgb("#3a3a46"), beard=False)
            c.new_path(); c.rectangle(x - 110, y - 330, 220, 40); fs(c, rgb("#222222"), 0); c.new_path(); c.rectangle(x - 70, y - 400, 140, 80); fs(c, rgb("#222222"), 0)
            c.new_path(); c.move_to(x - 40, y - 185); c.curve_to(x - 20, y - 205, x + 20, y - 205, x + 40, y - 185); c.set_line_width(14); c.set_source_rgb(0.2, 0.15, 0.1); c.stroke()
            c.pop_group_to_source(); c.paint_with_alpha(dp); c.restore()
            label(c, "DISGUISED", x, 1220, 50, WHITE, OUT, s.P(td + 0.3, 0.3))
        if t > tt - 0.3:
            n = 1 + min(2, int((t - tt + 0.3) / 0.35))
            pop_text(c, f"DAY {n}", W / 2, 1330, 80, 1.0, YEL)
    else:
        man(c, 540, 1020, 3.0, rgb("#3a3a46"), beard=False)
        p = ease_out(clamp((t - tc + 0.3) / 0.4))
        for k in range(7):                           # prison bars drop
            x = 140 + k * 133; c.new_path(); c.rectangle(x - 14, 480, 28, 720 * p); fs(c, rgb("#9aa0aa"), 4)
        stamp(c, "CRIME", W / 2, 700, 100, s.P(tc - 0.2, 0.3))
        if t > ty - 0.3: pop_text(c, "UP TO 1 YEAR IN PRISON", W / 2, 1290, 66, s.P(ty - 0.3, 0.3), RED)

def s_today(c, s):
    t = s.t; tp = s.W("today", "permit"); th = s.W("today", "hundred")
    full(c, s, "mon2", 1.05, 1.18, (0.5, 0.5), 6.0)
    if t > tp - 0.4:        # the permit card
        k = ease_back(s.P(tp - 0.4, 0.4)); c.save(); c.translate(540, 760); c.rotate(-0.05); c.scale(k, k)
        c.new_path(); rrect(c, -300, -170, 600, 340, 24); fs(c, rgb("#f3ead2"), 6)
        text(c, "DIAMONITIRION", 0, -100, 52, OUT, outline=None); text(c, "PILGRIM PERMIT · MEN ONLY", 0, -40, 32, OUT, outline=None)
        for i in range(3): c.new_path(); c.rectangle(-240, 10 + i * 40, 300 - i * 60, 14); c.set_source_rgba(0, 0, 0, 0.25); c.fill()
        c.restore()
        stamp(c, "APPROVED", 700, 900, 54, s.P(tp + 0.2, 0.3), GREEN, -0.25)
    if t > th - 0.4:
        n = int(100 * ease(clamp((t - th + 0.4) / 1.0)))
        pop_text(c, f"~{n} PILGRIMS / DAY", W / 2, 1220, 74, 1.0, YEL)

def s_end(c, s):
    t = s.t; tq = s.W("end", "Would")
    full(c, s, "mon", 1.0, 1.12, (0.5, 0.5), 5.0)
    stamp(c, "NO WOMEN", W / 2, 900, 100, 1.0)
    pop_text(c, "WOULD YOU GO?", W / 2, 420, 100, s.P(tq, 0.3), YEL)

SCENES = [("hook", s_hook), ("where", s_where), ("animals", s_animals), ("boats", s_boats), ("why", s_why),
          ("broke", s_broke), ("today", s_today), ("end", s_end)]

def impacts(Wt, B):
    return [0.5, Wt("animals", "Cats"), Wt("boats", "shore"), Wt("broke", "crime")]

def sfx(Wt, B, put):
    put(sfx_boom(38, 2.2), 0.0, 0.5); put(sfx_whoosh(2, 2.0), 0.2, 0.3)
    put(sfx_whoosh(5, 1.8), Wt("where"), 0.5); put(sfx_ding(1500), Wt("where", "Greece"), 0.4)
    for i in range(20): put(sfx_tick(), Wt("where", "twenty") - 0.3 + i * 0.05, 0.25)
    put(sfx_pop(500), Wt("animals", "cows"), 0.4); put(sfx_pop(600), Wt("animals", "hens"), 0.4); put(sfx_ding(1320), Wt("animals", "Cats"), 0.5)
    put(sfx_whoosh(7, 1.6), Wt("boats"), 0.4); put(sfx_boom(45, 0.8), Wt("boats", "shore"), 0.5)
    put(sfx_whoosh(9, 2.0), Wt("why", "landed") - 0.8, 0.4); put(sfx_ding(1760), Wt("why", "garden"), 0.4)
    put(sfx_pop(450), Wt("broke", "dressed"), 0.4)
    put(sfx_boom(35, 1.6), Wt("broke", "crime"), 0.9)
    put(sfx_pop(520), Wt("today", "permit"), 0.4); put(sfx_ding(1320), Wt("end", "Would"), 0.5)

# photo assignment (after fetch)
PH.update({
    "mon": ("Simonopetra_Aug2006.jpg", "Simonopetra, Mount Athos · Photo: Thodoris Lakiotis, CC BY-SA 3.0"),
    "mon2": ("Simonopetra_Monastery,_Mount_Athos.jpg", "Simonopetra, Mount Athos · Photo: Wikimedia Commons, public domain"),
})
