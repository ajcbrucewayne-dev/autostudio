"""Nature's Weirdest #1 v2 — "The Vanishing": globe-to-ocean format (GeoGlobeTales rhythm + story).
Facts: sea sapphires (Sapphirina) live in warm/tropical & subtropical oceans worldwide; males carry stacked guanine crystal
plates; at some viewing angles the reflection shifts into the UV and the animal practically disappears (Gur et al., JACS 2015).
Purpose of the trick is not proven -> narrated as "scientists think". Real photo: Georgina Jones, CC BY-SA 4.0 (credited on screen).
"""
import math, os, importlib.util
from cartoon import *
import globe
from PIL import Image

_spec = importlib.util.spec_from_file_location("v1", os.path.join(os.path.dirname(os.path.abspath(__file__)), "nature_seasapphire.py"))
v1 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(v1)
sapphire, bg_ocean, hue, fish, bubbles_burst = v1.sapphire, v1.bg_ocean, v1.hue, v1.fish, v1.bubbles_burst

NAME = "nature_seasapphire_v2"
LOOK = "cinematic"
TITLE = "This animal can turn INVISIBLE 💎 #shorts"
DESCRIPTION = ("The sea sapphire sparkles like a jewel... then vanishes. #nature #animals #ocean #science #shorts\n\n"
               "Photo: \"Sapphirina\" by Georgina Jones (iNaturalist), CC BY-SA 4.0 — https://commons.wikimedia.org/wiki/File:Sapphirina.jpg\n"
               "Earth imagery: NASA Goddard (Blue Marble), public domain.")
TAGS = ["sea sapphire", "invisible animal", "nature", "ocean", "weird animals", "shorts"]
VOICE, SPEED = "am_michael", 1.07
HOOK = ("THIS ANIMAL CAN", "TURN INVISIBLE")
BEATS = [
    ("hook", "This tiny animal can vanish... right in front of your eyes.", 0.2),
    ("where", "It's the sea sapphire, and it drifts through warm oceans all around the world.", 0.0),
    ("real", "And no, this isn't a cartoon. This is a real photo.", 0.2),
    ("chase", "But out here, sparkling is dangerous. A hungry fish has spotted it... and it's closing in.", 0.0),
    ("trick", "So the sea sapphire tilts its body. Its shine slips into ultraviolet, a color your eyes can't see... and it's gone.", 0.5),
    ("how", "The secret? Stacks of tiny crystals on its back, made of guanine, the same stuff in your DNA. Scientists think the trick helps it hide.", 0.0),
    ("end", "So the next time the ocean looks empty... look again.", 1.0),
]

# ---------------- globe helpers
def paint_rgba(c, rgba):
    """paint an (H, W, 4) uint8 RGBA numpy image onto the cairo context in screen space"""
    a = rgba[..., 3:4].astype(np.float32) / 255
    pm = np.dstack([(rgba[..., 2::-1].astype(np.float32) * a).astype(np.uint8), rgba[..., 3]])
    S = cairo.ImageSurface.create_for_data(bytearray(np.ascontiguousarray(pm).tobytes()), cairo.FORMAT_ARGB32, W, H)
    c.save(); c.identity_matrix(); c.set_source_surface(S); c.paint(); c.restore()

_DOTS = None
def warm_ocean_dots(n=140):
    """random points in tropical/subtropical ocean (picked from dark-blue pixels of the texture)"""
    global _DOTS
    if _DOTS is None:
        t = globe.tex(); th, tw, _ = t.shape; rng = np.random.default_rng(7); pts = []
        while len(pts) < n:
            lon, lat = rng.uniform(-180, 180), rng.uniform(-32, 32)
            r, g, b = t[int((90 - lat) / 180 * th), int((lon + 180) / 360 * tw) % tw]
            if b > r * 1.4 and b > g * 1.05 and b < 0.5: pts.append((lon, lat, rng.uniform(0, 6)))
        _DOTS = pts
    return _DOTS

def globe_shot(c, t, lon0, lat0, R, cy=960, dots=0.0, dot_t=0.0):
    bg_cinema(c, t)
    paint_rgba(c, globe.render_globe(lon0, lat0, R, W / 2, cy))
    if dots > 0:
        for lon, lat, ph in warm_ocean_dots():
            x, y, vis = globe.lonlat_to_screen(lon, lat, lon0, lat0, R, W / 2, cy)
            if not vis or not (-50 < x < W + 50 and -50 < y < H + 50): continue
            k = hue(ph * 0.17 + t * 0.2); f = dots * (0.6 + 0.4 * math.sin(t * 4 + ph * 3)) * clamp((dot_t - ph * 0.08) / 0.3)
            if f > 0.02: glow(c, x, y, 34, k, 0.9 * f); circle(c, x, y, 5, mix(k, WHITE, 0.5), 0, f)

# ---------------- scenes
def s_hook(c, s):
    t = s.t; tv = s.W("hook", "vanish")
    bg_ocean(c, t)
    vis = 1 - ease((t - tv) / 0.35) if t > tv else 1.0
    sapphire(c, 540, 860, 1.35, t, vis, ang=0.15 * math.sin(t))
    if t > tv:
        bubbles_burst(c, 540, 860, t - tv); pop_text(c, "?!", 540, 860, 170, clamp((t - tv - 0.3) / 0.3), YEL)

def s_where(c, s):
    t = s.t; t0 = s.t0; t1 = s.B["where"]["t1"]; tw = s.W("where", "warm")
    u = clamp((t - t0) / (t1 - t0))
    lon0 = lerp(-20, 38, ease(u)) ; lat0 = lerp(5, 20, ease(u))
    R = lerp(420, 420, u) if u < 0.55 else lerp(420, 2600, ease((u - 0.55) / 0.45))
    globe_shot(c, t, lon0, lat0, R, 980, dots=1.0 if t > tw - 0.2 else 0.0, dot_t=t - tw + 0.2)
    label(c, "SEA SAPPHIRE", W / 2, 300, 66, YEL, OUT, s.P(s.W("where", "sea") - 0.1, 0.35))
    label(c, "WARM OCEANS WORLDWIDE", W / 2, 440, 48, CYAN, OUT, s.P(tw, 0.35))
    if u > 0.9:  # dive flash into the water
        f = (u - 0.9) / 0.1; c.save(); c.identity_matrix(); c.set_source_rgba(0.75, 0.95, 1, 0.85 * f); c.paint(); c.restore()

_PHOTO = None
def s_real(c, s):
    global _PHOTO
    t = s.t
    if _PHOTO is None:
        im = Image.open(os.path.join(ROOT, "assets", "photos", "sapphirina_georgina_jones_ccbysa4.jpg")).convert("RGB")
        w = 1000; h = int(im.height * w / im.width); a = np.asarray(im.resize((w, h), Image.LANCZOS))
        rgba = np.zeros((H, W, 4), np.uint8); x0, y0 = (W - w) // 2, 560; rgba[y0:y0 + h, x0:x0 + w, :3] = a; rgba[y0:y0 + h, x0:x0 + w, 3] = 255
        _PHOTO = (rgba, (x0, y0, w, h))
    bg_ocean(c, t, "#062a5a", "#010612")
    rgba, (x0, y0, w, h) = _PHOTO
    p = ease_out(s.P(s.t0, 0.5))
    c.save(); c.translate(W / 2, y0 + h / 2); c.scale(0.85 + 0.15 * p, 0.85 + 0.15 * p); c.translate(-W / 2, -(y0 + h / 2))
    c.new_path(); rrect(c, x0 - 14, y0 - 14, w + 28, h + 28, 24); fs(c, WHITE, 6, p)
    c.restore()
    if p > 0.3: paint_rgba(c, (rgba.astype(np.float32) * np.array([1, 1, 1, clamp((p - 0.3) / 0.7)])).astype(np.uint8))
    label(c, "REAL PHOTO", W / 2, 470, 64, RED, WHITE, s.P(s.W("real", "real") - 0.15, 0.35))
    text(c, "Photo: Georgina Jones, CC BY-SA 4.0", W / 2, y0 + h + 50, 30, WHITE, alpha=p)
    glow(c, W / 2 + 60, y0 + h * 0.5, 200, (0.3, 0.6, 1), 0.35 * (0.6 + 0.4 * math.sin(t * 3)))

def s_chase(c, s):
    t = s.t; ts = s.W("chase", "spotted"); tc = s.W("chase", "closing")
    bg_ocean(c, t)
    if t < ts + 0.3:   # extreme close-up of the hunter's eye, with the sparkle reflected in it
        circle(c, 540, 860, 420, rgb("#ff7a3a"), 10); circle(c, 540, 860, 300, WHITE, 10)
        look = math.sin(t * 2.5) * 30
        circle(c, 560 + look, 860, 170, OUT, 0)
        sapphire(c, 600 + look, 820, 0.18, t)          # reflection of the prey in the pupil
        circle(c, 470 + look, 780, 40, WHITE, 0, 0.85)
        label(c, "HUNGRY FISH", 540, 300, 60, ORANGE, OUT, s.P(s.W("chase", "hungry") - 0.1, 0.35))
    else:              # the chase: camera follows, speed streaks, bubbles trail
        u = t - ts
        for k in range(14):
            yy = 300 + k * 80; x = ((k * 173 - u * 1600) % (W + 400)) - 200
            c.new_path(); c.move_to(x, yy); c.line_to(x + 160, yy); c.set_source_rgba(1, 1, 1, 0.25); c.set_line_width(5); c.stroke()
        gap = lerp(330, 120, ease(clamp((t - tc) / 1.6)))
        sx, sy = 800 + math.sin(u * 5) * 40, 820 + math.cos(u * 4) * 70
        sapphire(c, sx, sy, 0.62, t, ang=math.sin(u * 5) * 0.5)
        fish(c, sx - gap - 230, sy + 60 + math.sin(u * 6) * 20, 1.5, t, "hungry")
        for k in range(6): circle(c, sx - gap - 560 - k * 60, sy + 60 + math.sin(u * 7 + k) * 25, 10 + k * 2, (0.9, 0.98, 1), 3, 0.7 - k * 0.1)
        if t > tc - 0.2: label(c, "CLOSING IN", W / 2, 320, 62, RED, WHITE, s.P(tc - 0.2, 0.35))

def s_trick(c, s):
    t = s.t; tt = s.W("trick", "tilts"); tu = s.W("trick", "ultraviolet"); tg = s.W("trick", "gone")
    bg_ocean(c, t)
    tilt = ease(s.P(tt - 0.2, 1.0)) * 0.9
    vis = 1 - ease((t - tg + 0.15) / 0.4) if t > tg - 0.15 else 1.0
    sparkle = 1 - clamp((t - tu) / 0.8)
    sapphire(c, 600, 780, 1.0, t, vis, ang=tilt, sparkle=max(sparkle, 0.0))
    if t > tu - 0.2 and vis > 0.05:
        c.save(); c.translate(600, 780); c.rotate(tilt); c.new_path(); c.save(); c.scale(1, 1.45); c.arc(0, 0, 130, 0, 2 * math.pi); c.restore()
        c.set_source_rgba(0.55, 0.25, 1, 0.35 * clamp((t - tu + 0.2) / 0.5) * vis); c.fill(); c.restore()
        label(c, "ULTRAVIOLET", 600, 300, 60, PURPLE, WHITE, s.P(tu - 0.2, 0.35))
    fx = lerp(-300, 380, ease(clamp((t - tg + 0.9) / 0.9)))
    fish(c, fx, 820, 1.25, t, "hungry" if t < tg + 0.4 else "confused")
    if t > tg:
        bubbles_burst(c, 600, 780, t - tg); pop_text(c, "?", fx - 40, 560, 150, s.P(tg + 0.4, 0.3), YEL)
        label(c, "GONE.", W / 2, 1200, 76, WHITE, OUT, s.P(tg + 0.2, 0.3))

def s_how(c, s):
    t = s.t; tg = s.W("how", "guanine"); td = s.W("how", "DNA"); th = s.W("how", "hide")
    bg_ocean(c, t, "#081c44", "#020613")
    for layer in range(3):
        lp = ease(s.P(s.t0 + 0.2 + layer * 0.5, 0.7)); off = (1 - lp) * 700 * (1 if layer % 2 else -1)
        for row in range(-5, 6):
            for col in range(-4, 5):
                hx = 540 + col * 120 + (60 if row % 2 else 0) + off + layer * 18; hy = 760 + row * 104 + layer * 14
                k = hue(t * 0.12 + (col + row) * 0.04 + layer * 0.2)
                hexa = [(hx + 58 * math.cos(math.pi / 3 * i + math.pi / 6), hy + 58 * math.sin(math.pi / 3 * i + math.pi / 6)) for i in range(6)]
                c.new_path(); path(c, hexa); c.set_source_rgba(*k, 0.35 + 0.2 * layer); c.fill_preserve(); c.set_source_rgba(1, 1, 1, 0.5 * lp); c.set_line_width(4); c.stroke()
    label(c, "CRYSTAL STACKS", W / 2, 300, 60, WHITE, OUT, s.P(s.W("how", "crystals") - 0.1, 0.35))
    label(c, "GUANINE", 300, 1000, 60, YEL, OUT, s.P(tg - 0.1, 0.35))
    if t > td - 0.4:
        p = max(1e-3, s.P(td - 0.4, 0.5)); c.save(); c.translate(820, 960); c.scale(p, p)
        for i in range(9):
            yy = -160 + i * 40; dx = 60 * math.sin(i * 0.8 + t * 2)
            c.new_path(); c.move_to(-dx, yy); c.line_to(dx, yy); c.set_source_rgb(*(YEL if i % 3 == 0 else WHITE)); c.set_line_width(8); c.stroke()
            circle(c, -dx, yy, 11, CYAN, 4); circle(c, dx, yy, 11, PINK, 4)
        c.restore()
    if t > th - 0.3: label(c, "SCIENTISTS THINK: TO HIDE", W / 2, 470, 50, CYAN, OUT, s.P(th - 0.3, 0.35))

def s_end(c, s):
    t = s.t; tl = s.W("end", "again") - 0.3
    u = clamp((t - s.t0) / 2.2)
    R = lerp(2600, 430, ease(u)); lon0 = lerp(38, 60, ease(u)); lat0 = lerp(20, 2, ease(u))
    globe_shot(c, t, lon0, lat0, R, 960, dots=1.0, dot_t=t - s.t0 + 0.4)
    pop_text(c, "LOOK AGAIN.", W / 2, 330, 104, s.P(tl, 0.35), YEL)
    text(c, "THEY'RE EVERYWHERE", W / 2, 1520, 56, WHITE, alpha=s.P(tl + 0.5, 0.4))

SCENES = [("hook", s_hook), ("where", s_where), ("real", s_real), ("chase", s_chase), ("trick", s_trick), ("how", s_how), ("end", s_end)]

def cams(Wt, B):
    return {"hook": [(0, 540, 860, 1.15), (Wt("hook", "vanish"), 540, 880, 1.25), (B["hook"]["t1"], 540, 960, 1.0)],
            "chase": [(Wt("chase"), 540, 900, 1.15), (Wt("chase", "spotted"), 540, 960, 1.0), (B["chase"]["t1"], 600, 900, 1.12)],
            "how": [(Wt("how"), 540, 800, 1.3), (B["how"]["t1"], 540, 960, 1.0)]}

def impacts(Wt, B):
    return [Wt("trick", "gone")]

def sfx(Wt, B, put):
    for i in range(5): put(sfx_ding(1800 + i * 220), 0.05 + i * 0.22, 0.25)
    put(sfx_pop(900), Wt("hook", "vanish"), 0.8)
    put(sfx_whoosh(3, 1.6), Wt("where"), 0.5)
    for i in range(8): put(sfx_ding(1500 + i * 180), Wt("where", "warm") + i * 0.1, 0.18)
    put(sfx_whoosh(4, 0.7), B["where"]["t1"] - 0.35, 0.8)
    put(sfx_ding(1320), Wt("real", "real"), 0.5)
    put(sfx_boom(60, 0.6), Wt("chase", "spotted"), 0.6)
    for i in range(6): put(sfx_whoosh(10 + i, 0.4), Wt("chase", "spotted") + 0.3 + i * 0.45, 0.25)
    put(sfx_pop(1200), Wt("trick", "gone") + 0.4, 0.6)
    for i in range(3): put(sfx_ding(2400 - i * 300), Wt("how") + 0.2 + i * 0.5, 0.3)
    for i in range(10): put(sfx_ding(1400 + i * 200), Wt("end") + 0.4 + i * 0.12, 0.2)
