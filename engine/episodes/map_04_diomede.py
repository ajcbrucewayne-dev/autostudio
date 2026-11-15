"""Map Secrets #4: two islands 3.8 km apart but ~21 hours apart in time (Diomede Islands, Bering Strait).
Facts: Big Diomede (Russia) and Little Diomede (USA) are ~3.8 km (2.4 mi) apart; the International Date Line runs between them, so
Big Diomede is ~21 hours ahead ("Tomorrow Island"/"Yesterday Island"); the USA bought Alaska from Russia in 1867 for $7.2 million and
Little Diomede came with it, Big Diomede did not; in 1948 the Soviet Union closed the border (the "Ice Curtain") and moved Big
Diomede's people to the mainland; in deep winter sea ice can bridge the islands but crossing without clearance is illegal.
Images (Wikimedia Commons, public domain): Diomede Islands from space; NASA MISR Bering Strait; USCG photo of Diomede village (PO Richard Brahm);
1867 Treasury warrant (Alaska Purchase). Map: NASA Blue Marble + Natural Earth (public domain).
"""
import math, os
from cartoon import *
import globe
from episodes_util import paint_rgba
from PIL import Image

NAME = "map_04_diomede"
LOOK = "cinematic"
TITLE = "These islands are 3.8 km apart... and 21 HOURS apart ⏰ #shorts"
DESCRIPTION = ("Russia and the USA almost touch in the Bering Strait, and the International Date Line runs right between them. "
               "#geography #maps #russia #alaska #shorts\n\nImages: Wikimedia Commons / NASA / US Coast Guard (public domain). "
               "Map: NASA, Natural Earth (public domain).")
TAGS = ["diomede islands", "date line", "geography", "maps", "russia", "alaska", "shorts"]
VOICE, SPEED = "am_michael", 1.07
CAPTION_Y = 1450
HOOK = ("3.8 KM APART", "BUT 21 HOURS APART")
BEATS = [
    ("hook", "These two islands are just 3.8 kilometers apart... but one of them lives in tomorrow.", 0.2),
    ("where", "Big Diomede belongs to Russia. Little Diomede belongs to the USA. And between them runs a line you can't see.", 0.0),
    ("dateline", "The International Date Line. Cross it heading west, and you jump forward a whole day.", 0.1),
    ("why", "Why does it exist? Earth spins, so a new day has to begin somewhere. So we drew the line through the Pacific, where almost nobody lives.", 0.0),
    ("history", "And the border? In 1867, Russia sold Alaska to the USA for 7.2 million dollars. But Big Diomede stayed Russian.", 0.0),
    ("ice", "In winter, sea ice can form a bridge between them. But crossing it is illegal. The border has been closed since 1948.", 0.2),
    ("end", "Sunday afternoon on one island... Monday on the other. Which island would you choose?", 1.0),
]
DIR = os.path.join(ROOT, "assets", "mapsecrets")
PH = {"space": ("The_Diomede_Islands_in_the_BeringSea_(picture_from_space).jpg", "Image: Wikimedia Commons, public domain"),
      "village": ("Little_Diomede_Island_village.jpeg", "Photo: US Coast Guard, PO Richard Brahm, public domain"),
      "check": ("Alaska_Purchase_(hi-res).jpg", "1867 Treasury warrant, public domain"),
      "strait": ("BeringSt-close-VE.jpg", "Image: NASA (MISR), public domain")}
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


RU, US = rgb("#ff5a5a"), rgb("#3fa9ff")
BIG, LITTLE = (-169.05, 65.78), (-168.93, 65.75)

def earth(c, t, lon0, lat0, R, cy=1000, sun=(-0.35, 0.4, 0.85), night=0.18):
    bg_cinema(c, t); paint_rgba(c, globe.render_globe(lon0, lat0, R, W / 2, cy, sun=sun, night=night))

BOX = (40, 520, 1000, 800)    # the space photo is 900x720 (5:4) -> shown whole so BOTH islands are visible
def island_shot(c, s, z=1.0, labels=1.0):
    bg_cinema(c, s.t, seed=14)
    photo(c, "space", *BOX, z, (0.5, 0.5))
    c.new_path(); c.rectangle(*BOX); c.set_source_rgba(1, 1, 1, 0.9); c.set_line_width(6); c.stroke()
    text(c, PH["space"][1], W / 2, 1880, 26, WHITE, alpha=0.8)

def card(c, x, y, w, h, title, sub, col, p):
    if p <= 0: return
    k = ease_back(p); c.save(); c.translate(x, y); c.scale(k, k)
    c.new_path(); rrect(c, -w / 2, -h / 2, w, h, 26); fs(c, WHITE, 7)
    c.new_path(); rrect(c, -w / 2, -h / 2, w, h * 0.32, 26); c.set_source_rgb(*col); c.fill()
    text(c, title, 0, -h / 2 + h * 0.16, h * 0.17, WHITE, outline=None); text(c, sub, 0, h * 0.14, h * 0.24, OUT, outline=None)
    c.restore()

# ---------------- scenes
def s_hook(c, s):
    t = s.t; tt = s.W("hook", "tomorrow")
    island_shot(c, s, 1.0 + 0.02 * t)
    label(c, "RUSSIA", 290, 600, 50, RU, WHITE, s.P(0.2, 0.3)); label(c, "USA", 860, 780, 50, US, WHITE, s.P(0.4, 0.3))
    arrow(c, (450, 930), (720, 930), s.P(0.6, 0.4), YEL, 10, 26); arrow(c, (720, 930), (450, 930), s.P(0.6, 0.4), YEL, 10, 26)
    label(c, "3.8 KM", 585, 1010, 52, YEL, OUT, s.P(0.7, 0.3))
    if t > tt - 0.2: card(c, 290, 1170, 280, 170, "TOMORROW", "MONDAY", RU, s.P(tt - 0.2, 0.3))

def s_where(c, s):
    t = s.t; tb = s.W("where", "Big"); tl = s.W("where", "Little"); tline = s.W("where", "line")
    u = clamp((t - s.t0) / 2.0); lon0 = lerp(-140, -169, ease(u)); lat0 = lerp(45, 65.7, ease(u)); R = lerp(600, 6500, ease(u))
    earth(c, t, lon0, lat0, R)
    globe.fill_region(c, globe.rings("Russia"), lon0, lat0, R, RU, 0.45, W / 2, 1000)
    globe.fill_region(c, globe.rings("Alaska", "ne_50m_admin_1_states_provinces", ("name",)), lon0, lat0, R, US, 0.45, W / 2, 1000)
    for (lon, lat), txt, col, tw, dx in ((BIG, "BIG DIOMEDE · RUSSIA", RU, tb, -60), (LITTLE, "LITTLE DIOMEDE · USA", US, tl, 60)):
        x, y, vis = globe.lonlat_to_screen(lon, lat, lon0, lat0, R, W / 2, 1000)
        if vis and t > tw - 0.3:
            circle(c, x, y, 14, col, 5); label(c, txt, x + dx * 3.5, y + (-90 if dx < 0 else 90), 40, col, WHITE, s.P(tw - 0.3, 0.3))
    if t > tline - 0.3: pop_text(c, "AN INVISIBLE LINE...", W / 2, 400, 76, s.P(tline - 0.3, 0.3), YEL)

def s_dateline(c, s):
    t = s.t; tj = s.W("dateline", "jump")
    lon0, lat0, R = -178, 35, 900
    earth(c, t, lon0, lat0, R)
    globe.fill_region(c, globe.rings("Russia"), lon0, lat0, R, RU, 0.35, W / 2, 1000)
    globe.draw_path(c, globe.DATE_LINE, lon0, lat0, R, W / 2, 1000, p=ease(s.P(s.t0, 1.6)), col=YEL)
    label(c, "INTERNATIONAL DATE LINE", W / 2, 360, 52, YEL, OUT, s.P(s.t0 + 0.3, 0.3))
    if t > tj - 0.3:
        card(c, 270, 1180, 340, 210, "WEST SIDE", "MONDAY", RU, s.P(tj - 0.3, 0.3))
        card(c, 810, 1180, 340, 210, "EAST SIDE", "SUNDAY", US, s.P(tj - 0.1, 0.3))
        arrow(c, (650, 980), (430, 980), s.P(tj, 0.4), WHITE, 12, 30); pop_text(c, "+1 DAY", 540, 920, 64, s.P(tj + 0.2, 0.3), YEL)

def s_why(c, s):
    t = s.t; ts = s.W("why", "spins"); tp = s.W("why", "Pacific"); tn = s.W("why", "nobody")
    spin = (t - s.t0) * 40
    lon0 = -100 + spin if t < tp - 0.4 else lerp(-100 + (tp - 0.4 - s.t0) * 40, 180, ease((t - tp + 0.4) / 1.0))
    earth(c, t, lon0, 10, 430, 1000, sun=globe.sun_dir(-55, 0.2), night=0.05)
    c.new_path(); c.arc(W / 2, 1000, 520, -2.6, -0.5); c.set_source_rgba(1, 1, 1, 0.8 * s.P(ts - 0.2, 0.3)); c.set_line_width(8); c.stroke()
    arrow(c, (W / 2 + 520 * math.cos(-0.7), 1000 + 520 * math.sin(-0.7)), (W / 2 + 520 * math.cos(-0.5), 1000 + 520 * math.sin(-0.5)), s.P(ts, 0.3), WHITE, 8, 28)
    sun(c, 120, 420, 60, t)
    pop_text(c, "A NEW DAY MUST START", W / 2, 330, 70, s.P(s.W("why", "begin") - 0.2, 0.3), WHITE)
    pop_text(c, "SOMEWHERE...", W / 2, 420, 70, s.P(s.W("why", "somewhere") - 0.2, 0.3), YEL)
    if t > tp - 0.4:
        globe.draw_path(c, globe.DATE_LINE, lon0, 10, 430, W / 2, 1000, p=ease(s.P(tp - 0.2, 0.8)), col=YEL, width=6, glow_w=20)
    if t > tn - 0.3: label(c, "MOSTLY OCEAN", W / 2, 1520, 56, CYAN, OUT, s.P(tn - 0.3, 0.3))

def s_history(c, s):
    t = s.t; ts = s.W("history", "sold"); tm = s.W("history", "7.2") if False else s.W("history", "million"); tb = s.W("history", "Big")
    if t < tm + 0.6:   # the actual 1867 cheque
        bg_cinema(c, t, seed=15)
        photo(c, "check", 40, 560, 1000, 520, 1.0 + 0.04 * (t - s.t0), (0.45, 0.5))
        c.new_path(); c.rectangle(40, 560, 1000, 520); c.set_source_rgb(1, 1, 1); c.set_line_width(6); c.stroke()
        bg_t = 1 - s.P(s.t0, 0.3)
        pop_text(c, "1867", W / 2, 380, 130, s.P(s.t0 + 0.1, 0.3), YEL)
        if t > tm - 0.6: stamp(c, "$7,200,000", W / 2, 1220, 100, s.P(tm - 0.6, 0.3), GREEN)
        text(c, PH["check"][1], W / 2, 1880, 26, WHITE, alpha=0.8)
    else:
        lon0, lat0, R = -160, 63, 1500
        earth(c, t, lon0, lat0, R)
        f = ease(clamp((t - tm - 0.6) / 0.8))
        globe.fill_region(c, globe.rings("Russia"), lon0, lat0, R, RU, 0.45, W / 2, 1000)
        globe.fill_region(c, globe.rings("Alaska", "ne_50m_admin_1_states_provinces", ("name",)), lon0, lat0, R, mix(RU, US, f), 0.6, W / 2, 1000)
        label(c, "ALASKA → USA", 760, 420, 56, US, WHITE, s.P(tm + 0.8, 0.3))
        x, y, vis = globe.lonlat_to_screen(*BIG, lon0, lat0, R, W / 2, 1000)
        if vis and t > tb - 0.3:
            circle(c, x, y, 16, RU, 6); label(c, "BIG DIOMEDE STAYED RUSSIAN", W / 2, 1180, 46, RU, WHITE, s.P(tb - 0.3, 0.3))
            globe.draw_path(c, [(-169.0, 60), (-169.0, 72)], lon0, lat0, R, W / 2, 1000, p=s.P(tb, 0.6), col=YEL, width=5, glow_w=16, dash=[18, 12])

def s_ice(c, s):
    t = s.t; ti = s.W("ice", "illegal"); tc = s.W("ice", "closed")
    island_shot(c, s, 1.0)
    g = ease(s.P(s.t0, 1.6))   # sea ice spreading between the islands
    rng = np.random.default_rng(8)
    for k in range(60):
        x, y, r = rng.uniform(470, 720), rng.uniform(560, 1290), rng.uniform(30, 70)
        if clamp(g * 1.5 - k / 60) > 0: c.new_path(); path(c, blob(x, y, r * clamp(g * 1.5 - k / 60), k, 0.3)); c.set_source_rgba(0.92, 0.96, 1, 0.75); c.fill()
    pop_text(c, "WINTER: ICE BRIDGE", W / 2, 380, 70, s.P(s.t0 + 0.2, 0.3), WHITE)
    wx = lerp(720, 615, ease(clamp((t - s.t0 - 0.8) / (ti - s.t0 - 0.6))))   # a walker heads across... and stops at the border
    c.new_path(); c.move_to(595, 520); c.line_to(595, 1320); c.set_dash([20, 14]); c.set_source_rgb(*YEL); c.set_line_width(6); c.stroke(); c.set_dash([])
    circle(c, wx, 905, 16, rgb("#f2c9a0"), 5); c.new_path(); rrect(c, wx - 16, 922, 32, 52, 10); fs(c, ORANGE, 5)
    if t > ti - 0.1: stamp(c, "ILLEGAL", W / 2, 1180, 110, s.P(ti - 0.1, 0.3))
    if t > tc - 0.3: label(c, "CLOSED SINCE 1948", W / 2, 470, 46, RU, WHITE, s.P(tc - 0.3, 0.3))

def s_end(c, s):
    t = s.t; tq = s.W("end", "Which")
    island_shot(c, s, 1.0 + 0.02 * (t - s.t0))
    card(c, 290, 720, 340, 220, "BIG DIOMEDE", "MON 12 PM", RU, s.P(s.t0 + 0.1, 0.3))
    card(c, 830, 1130, 340, 220, "LITTLE DIOMEDE", "SUN 3 PM", US, s.P(s.t0 + 0.5, 0.3))
    pop_text(c, "WHICH ISLAND?", W / 2, 420, 100, s.P(tq, 0.3), YEL)

SCENES = [("hook", s_hook), ("where", s_where), ("dateline", s_dateline), ("why", s_why), ("history", s_history), ("ice", s_ice), ("end", s_end)]

def impacts(Wt, B):
    return [Wt("dateline", "jump"), Wt("ice", "illegal")]

def sfx(Wt, B, put):
    put(sfx_boom(45, 1.6), 0.0, 0.4); put(sfx_pop(), 0.2, 0.4); put(sfx_pop(700), 0.4, 0.4)
    put(sfx_ding(1500), Wt("hook", "tomorrow"), 0.4)
    put(sfx_whoosh(5, 1.8), Wt("where"), 0.5)
    put(sfx_whoosh(6, 1.6), Wt("dateline"), 0.4); put(sfx_ding(1800), Wt("dateline", "jump"), 0.5)
    put(sfx_whoosh(7, 2.5), Wt("why", "spins"), 0.4)
    put(sfx_ding(1320), Wt("history", "million"), 0.5)
    put(sfx_whoosh(8, 1.5), Wt("ice"), 0.4)
    put(sfx_ding(1568), Wt("end", "Which"), 0.5)
