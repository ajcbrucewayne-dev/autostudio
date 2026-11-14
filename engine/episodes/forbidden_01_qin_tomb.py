"""Forbidden Places #1: the tomb no one is allowed to open (Mausoleum of Qin Shi Huang, near Xi'an, China).
Facts: China's first emperor, Qin Shi Huang (died 210 BC); burial complex near Xi'an with the Terracotta Army (commonly estimated
at ~8,000 figures); the central tomb has never been opened; historian Sima Qian (~100 years later) described crossbow traps and rivers
of mercury mimicking China's rivers; modern soil studies found unusually high mercury around the mound; officials cite preservation
limits — when the painted warriors were excavated, the lacquer under the paint curled within ~15 s and flaked off in ~4 min (Nat Geo).
Photos (Wikimedia Commons): public domain (User:airunp; Richardelainechambers), CC BY 2.0 (Arian Zwegers; Peter Dowley).
Map: NASA Blue Marble + Natural Earth (public domain).
"""
import math, os
from cartoon import *
import globe
from episodes_util import paint_rgba
from PIL import Image

NAME = "forbidden_01_qin_tomb"
LOOK = "cinematic"
TITLE = "No one is allowed to open this tomb ⚰️ #shorts"
DESCRIPTION = ("China's first emperor has been sealed in his tomb for over 2,000 years. Here's why nobody opens it. "
               "#history #china #mystery #forbiddenplaces #shorts\n\n"
               "Photos: Arian Zwegers (CC BY 2.0), Peter Dowley (CC BY 2.0), User:airunp & Richardelainechambers (public domain), via Wikimedia Commons. "
               "Map: NASA, Natural Earth (public domain).")
TAGS = ["terracotta army", "qin shi huang", "forbidden places", "history", "china", "shorts"]
VOICE, SPEED = "am_michael", 1.05
HOOK = ("NO ONE IS ALLOWED", "TO OPEN THIS TOMB")
BEATS = [
    ("hook", "There's a tomb in China... that no one is allowed to open.", 0.3),
    ("who", "It belongs to China's first emperor, buried over two thousand years ago near the city of Xi'an.", 0.0),
    ("army", "He took an army with him. An estimated eight thousand clay soldiers, guarding him forever.", 0.0),
    ("guess", "But the emperor himself is still sealed inside. Is it cursed? Booby-trapped?", 0.2),
    ("mercury", "An ancient historian wrote that inside, rivers of mercury flow across a map of China. And the soil around the tomb really does hold unusually high mercury.", 0.0),
    ("paint", "But the biggest reason it stays closed? When the clay army was dug up, its painted colors began peeling within seconds, and were gone in minutes.", 0.3),
    ("end", "So the emperor stays sealed, until science can protect what's inside. Would you open it?", 1.0),
]
DIR = os.path.join(ROOT, "assets", "forbidden")
PH = {"faces": ("Terracotta_Warriors_(2661111239).jpg", "Photo: Peter Dowley, CC BY 2.0"),
      "rows": ("Xian_guerreros_terracota_detalle.JPG", "Photo: User:airunp, public domain"),
      "pit": ("Xian,_Terracotta_Army_(6170329474).jpg", "Photo: Arian Zwegers, CC BY 2.0"),
      "dug": ("Terracotta_army_xian_embedded_warrior.jpg", "Photo: Richardelainechambers, public domain"),
      "broken": ("Terracotta_army_xian_assembling_warriors.jpg", "Photo: Richardelainechambers, public domain")}
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

def mound(c, cx, cy, s, t, mercury=0.0, cut=1.0, p=1.0):
    """cross-section of the burial mound: earth layers, sealed chamber, optional mercury rivers"""
    if p <= 0: return
    c.save(); c.translate(cx, cy); c.scale(s * ease_back(p), s * ease_back(p))
    c.new_path(); c.move_to(-460, 140); c.curve_to(-300, -40, -170, -230, 0, -240); c.curve_to(170, -230, 300, -40, 460, 140); c.close_path(); fs(c, rgb("#7a5a3a"), 8)
    for k in range(3):
        y = -150 + k * 90; c.new_path(); c.move_to(-400 + k * 40, y + 230 - k * 20); c.curve_to(-200, y - 40, 200, y - 40, 400 - k * 40, y + 230 - k * 20)
        c.set_source_rgba(0.35, 0.25, 0.15, 0.6); c.set_line_width(6); c.stroke()
    c.new_path(); c.rectangle(-460, 140, 920, 260); fs(c, rgb("#5a3f28"), 8)
    c.new_path(); rrect(c, -190, 170, 380, 190, 16); fs(c, rgb("#2a1c14"), 6)          # the sealed chamber
    if mercury > 0:   # shimmering silver rivers
        for k in range(3):
            pts = [(-170 + x, 215 + k * 48 + 10 * math.sin(x * 0.04 + t * 3 + k)) for x in range(0, 341, 20)]
            c.new_path(); path(c, pts, close=False); c.set_source_rgba(0.85, 0.88, 0.95, mercury); c.set_line_width(12); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke()
            for j in range(4):
                gx = -170 + ((t * 120 + j * 90 + k * 40) % 340); circle(c, gx, 215 + k * 48, 5, WHITE, 0, mercury * 0.9)
    lock = 1 - mercury * 0.6
    circle(c, 0, 265, 34, YEL, 6, lock); c.new_path(); c.arc(0, 240, 22, math.pi, 0); c.set_source_rgba(*OUT, lock); c.set_line_width(8); c.stroke()
    c.restore()

def earth(c, t, lon0, lat0, R, cy=1000):
    bg_cinema(c, t); paint_rgba(c, globe.render_globe(lon0, lat0, R, W / 2, cy, sun=(-0.35, 0.4, 0.85)))

# ---------------- scenes
def s_hook(c, s):
    t = s.t
    full(c, s, "faces", 1.25, 1.45, (0.72, 0.45), 5.0)
    stamp(c, "SEALED", W / 2, 1180, 120, s.P(s.W("hook", "no") - 0.1, 0.3))

def s_who(c, s):
    t = s.t; tx = s.W("who", "Xi'an"); u = clamp((t - s.t0) / 2.2)
    lon0 = lerp(80, 109, ease(u)); lat0 = lerp(30, 34.4, ease(u)); R = lerp(700, 2600, ease(u))
    earth(c, t, lon0, lat0, R)
    globe.fill_region(c, globe.rings("China"), lon0, lat0, R, rgb("#ff5a5a"), 0.45 * (1 - u * 0.5), W / 2, 1000)
    x, y, vis = globe.lonlat_to_screen(109.27, 34.38, lon0, lat0, R, W / 2, 1000)
    if vis:
        glow(c, x, y, 170, (1, 0.8, 0.4), 0.6); circle(c, x, y, 16, YEL, 6)
        if t > tx - 0.3: label(c, "XI'AN", x, y - 100, 60, WHITE, OUT, s.P(tx - 0.3, 0.3))
    label(c, "CHINA'S FIRST EMPEROR", W / 2, 360, 54, YEL, OUT, s.P(s.W("who", "first") - 0.1, 0.3))
    pop_text(c, "DIED 210 BC", W / 2, 470, 60, s.P(s.W("who", "two") - 0.1, 0.3), WHITE)

def s_army(c, s):
    t = s.t; te = s.W("army", "eight")
    full(c, s, "pit", 1.0, 1.25, (0.5, 0.55), 5.0)
    if t > te - 0.3:
        n = 8000 * ease(clamp((t - te + 0.3) / 1.2))
        text(c, f"{n:,.0f}", W / 2, 520, 170, YEL); text(c, "CLAY SOLDIERS", W / 2, 650, 64, WHITE)

def s_guess(c, s):
    t = s.t; tc = s.W("guess", "cursed"); tb = s.W("guess", "Booby")
    bg_cinema(c, t, seed=12, top="#0a0705", bot="#2a1a0e", neb=(("#5a3a1a", 0.4), ("#3a2a1a", 0.3), ("#6a4a2a", 0.2)))
    mound(c, W / 2, 780, 0.95, t, 0.0, 1.0, s.P(s.t0, 0.4))
    label(c, "STILL SEALED", W / 2, 1200, 56, YEL, OUT, s.P(s.W("guess", "sealed") - 0.1, 0.3))
    pop_text(c, "CURSED?", 300, 420, 92, s.P(tc - 0.1, 0.3), WHITE)
    pop_text(c, "BOOBY TRAPS?", 700, 560, 82, s.P(tb - 0.1, 0.3), RED)

def s_mercury(c, s):
    t = s.t; tr = s.W("mercury", "rivers"); ts = s.W("mercury", "soil")
    bg_cinema(c, t, seed=12, top="#0a0705", bot="#2a1a0e", neb=(("#5a3a1a", 0.4), ("#3a2a1a", 0.3), ("#6a4a2a", 0.2)))
    merc = clamp((t - tr + 0.3) / 0.8)
    mound(c, W / 2, 780, 0.95, t, merc)
    if t > tr - 0.3: label(c, "RIVERS OF MERCURY", W / 2, 400, 64, GREY, OUT, s.P(tr - 0.3, 0.3))
    if t > ts - 0.2:   # soil sample probe + reading
        p = s.P(ts - 0.2, 0.3); c.new_path(); c.move_to(780, 440); c.line_to(780, 650); c.set_source_rgba(*WHITE, p); c.set_line_width(10); c.stroke()
        c.new_path(); rrect(c, 640, 1100, 300, 100, 20); fs(c, rgb("#1d1230"), 5, 0.92 * p)
        text(c, "Hg  HIGH!", 790, 1150, 54, RED, alpha=p)
        label(c, "MEASURED IN THE SOIL", 330, 1150, 40, WHITE, OUT, p)

def s_paint(c, s):
    t = s.t; tsec = s.W("paint", "seconds"); tmin = s.W("paint", "minutes"); tb = s.W("paint", "biggest")
    fade = clamp((t - tsec) / max(0.5, tmin - tsec + 0.6))
    photo(c, "dug", 0, 0, W, H, 1.3, (0.55, 0.45))
    # warm 'paint' layer over the photo that drains away as the narration says it peels off
    c.save(); c.identity_matrix(); c.set_source_rgba(0.85, 0.35, 0.25, 0.35 * (1 - fade)); c.set_operator(cairo.OPERATOR_OVERLAY); c.paint(); c.restore()
    c.save(); c.identity_matrix(); g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgba(0, 0, 0, 0, 0.55); g.add_color_stop_rgba(0.4, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, 0.6)
    c.set_source(g); c.paint(); c.restore()
    label(c, "THE BIGGEST REASON", W / 2, 330, 56, YEL, OUT, s.P(tb - 0.2, 0.3))
    if t > tsec - 0.3:
        p = s.P(tsec - 0.3, 0.3); c.new_path(); rrect(c, 190, 880, 700, 220, 30); fs(c, rgb("#1d1230"), 6, 0.92 * p)
        secs = lerp(0, 240, ease(clamp((t - tsec) / max(0.8, tmin - tsec + 0.8))))
        text(c, f"{int(secs // 60)}:{int(secs % 60):02d}", W / 2, 950, 110, RED if secs > 60 else WHITE, alpha=p)
        text(c, "PAINT CURLS AT 0:15 · GONE BY 4:00", W / 2, 1050, 32, WHITE, alpha=p)
    text(c, PH["dug"][1], W / 2, 1880, 26, WHITE, alpha=0.8)

def s_end(c, s):
    t = s.t; tq = s.W("end", "Would")
    full(c, s, "faces", 1.45, 1.25, (0.72, 0.45), 4.0)
    stamp(c, "SEALED", W / 2, 1180, 120, 1.0)
    pop_text(c, "WOULD YOU OPEN IT?", W / 2, 420, 84, s.P(tq, 0.3), YEL)

SCENES = [("hook", s_hook), ("who", s_who), ("army", s_army), ("guess", s_guess), ("mercury", s_mercury), ("paint", s_paint), ("end", s_end)]

def impacts(Wt, B):
    return [Wt("hook", "no"), Wt("paint", "minutes")]

def sfx(Wt, B, put):
    put(sfx_boom(38, 2.2), 0.0, 0.5)
    put(sfx_whoosh(5, 1.6), Wt("who"), 0.5); put(sfx_ding(1500), Wt("who", "Xi'an"), 0.4)
    for i in range(10): put(sfx_tick(), Wt("army", "eight") + i * 0.11, 0.4)
    put(sfx_pop(), Wt("guess", "cursed"), 0.5); put(sfx_pop(400), Wt("guess", "Booby"), 0.5)
    put(sfx_ding(2000), Wt("mercury", "rivers"), 0.4); put(sfx_ding(900), Wt("mercury", "soil"), 0.4)
    for i in range(14): put(sfx_tick(), Wt("paint", "seconds") + i * 0.12, 0.35)
    put(sfx_ding(1320), Wt("end", "Would"), 0.5)
