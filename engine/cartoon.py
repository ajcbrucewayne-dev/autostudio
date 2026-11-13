"""Cartoon engine (What If channel, style A): bright, bold, outlined 2D animation with Leo.

An episode is a small Python module (see engine/episodes/whatif_moon.py) that defines:
    NAME, VOICE, SPEED, BEATS = [(beat, text, pause_after), ...]
    SCENES = [(beat, draw_fn), ...]         draw_fn(c: cairo.Context, s: Scene)  -- one per visual scene, starts at that beat
    cams(Wt, B) -> {beat: [(t, cx, cy, zoom), ...]}   (optional camera keys per scene)
    sfx(Wt, B, put)                                     (optional extra sound cues: put(clip, t, gain))
    HOOK = ("LINE 1", "LINE 2")                         (optional on-screen hook text for the first beat)
Run:  python3 engine/cartoon.py engine/episodes/whatif_moon.py out.mp4
      python3 engine/cartoon.py engine/episodes/whatif_moon.py out_dir --stills 0 3.5 10
"""
import importlib.util, json, math, os, subprocess, sys
import numpy as np
import cairo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

W, H, FPS, SR = 1080, 1920, 30, 24000
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ------------------------------------------------------------------ palette + easing
def rgb(h): h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
OUT = rgb("#1b1530"); WHITE = (1, 1, 1); YEL = rgb("#ffd43b"); RED = rgb("#ef4444"); BLUE = rgb("#2f7de1")
GREEN = rgb("#4cc35a"); DKGREEN = rgb("#2e8f3e"); SAND = rgb("#f2cf8b"); PINK = rgb("#ff7aa8"); ORANGE = rgb("#ff9f1c")
GREY = rgb("#c9c9d6"); SKY = rgb("#8fd3ff"); PURPLE = rgb("#7c5cff"); CYAN = rgb("#3dd6d0")

def clamp(v, a=0.0, b=1.0): return max(a, min(b, v))
def ease(p): p = clamp(p); return p * p * (3 - 2 * p)
def ease_out(p): return 1 - (1 - clamp(p)) ** 3
def ease_back(p):
    p = clamp(p); c1 = 1.70158; c3 = c1 + 1; return 1 + c3 * (p - 1) ** 3 + c1 * (p - 1) ** 2
def lerp(a, b, f): return a + (b - a) * f
def mix(c1, c2, f): return tuple(lerp(a, b, f) for a, b in zip(c1, c2))

# ------------------------------------------------------------------ drawing primitives
def path(c, P, close=True):
    c.move_to(*P[0])
    for q in P[1:]: c.line_to(*q)
    if close: c.close_path()

def fs(c, col, ow=8, alpha=1.0, line=OUT):
    """fill (preserve) + outline"""
    c.set_source_rgba(*col, alpha); c.fill_preserve(); c.set_source_rgba(*line, alpha); c.set_line_width(ow); c.stroke()

def circle(c, x, y, r, col, ow=8, alpha=1.0):
    if r <= 0: return
    c.new_path(); c.arc(x, y, r, 0, 2 * math.pi); fs(c, col, ow, alpha)

def blob(cx, cy, r, seed, amp=0.35, n=80):
    rng = np.random.default_rng(seed); ph = rng.uniform(0, 6, 4); a = np.linspace(0, 2 * np.pi, n)
    rr = r * (1 + sum(amp / (i + 1) * np.sin((i + 2) * a + ph[i]) for i in range(3)))
    return np.stack([cx + np.cos(a) * rr, cy + np.sin(a) * rr], 1)

def rrect(c, x, y, w, h, r):
    c.new_sub_path(); c.arc(x + w - r, y + r, r, -math.pi / 2, 0); c.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    c.arc(x + r, y + h - r, r, math.pi / 2, math.pi); c.arc(x + r, y + r, r, math.pi, 1.5 * math.pi); c.close_path()

def text(c, s, x, y, size, col=WHITE, outline=OUT, ow=None, alpha=1.0, anchor="c"):
    """Bold Inter text; y = baseline-ish centre. Returns width."""
    if alpha <= 0.01 or size < 2: return 0
    c.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(size)
    e = c.text_extents(s); x0 = x - e.x_advance / 2 if anchor == "c" else x; y0 = y + size * 0.36
    if outline:
        c.move_to(x0, y0); c.text_path(s); c.set_source_rgba(*outline, alpha); c.set_line_width(ow or max(6, size * 0.16))
        c.set_line_join(cairo.LINE_JOIN_ROUND); c.stroke()
    c.move_to(x0, y0); c.set_source_rgba(*col, alpha); c.show_text(s)
    return e.x_advance

def pop_text(c, s, x, y, size, p, col=WHITE, **kw):
    """text that pops in with overshoot (p = 0..1 progress)"""
    if p <= 0: return
    k = ease_back(p); c.save(); c.translate(x, y); c.scale(k, k); text(c, s, 0, 0, size, col, **kw); c.restore()

def label(c, s, x, y, size=44, bg=WHITE, fg=OUT, p=1.0):
    """pill label"""
    if p <= 0: return
    k = ease_back(p); c.save(); c.translate(x, y); c.scale(k, k)
    c.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(size)
    w = c.text_extents(s).x_advance + size * 1.0; h = size * 1.6
    rrect(c, -w / 2, -h / 2, w, h, h / 2); fs(c, bg, 6)
    text(c, s, 0, 0, size, fg, outline=None); c.restore()

def arrow(c, p0, p1, p=1.0, col=YEL, w=16, head=34):
    if p <= 0: return
    x0, y0 = p0; x1, y1 = lerp(x0, p1[0], ease_out(p)), lerp(y0, p1[1], ease_out(p))
    a = math.atan2(y1 - y0, x1 - x0)
    for lw, cc in ((w + 10, OUT), (w, col)):
        c.move_to(x0, y0); c.line_to(x1 - math.cos(a) * head * 0.6, y1 - math.sin(a) * head * 0.6)
        c.set_source_rgb(*cc); c.set_line_width(lw); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke()
    c.move_to(x1, y1); c.line_to(x1 - math.cos(a - 0.5) * head, y1 - math.sin(a - 0.5) * head)
    c.line_to(x1 - math.cos(a + 0.5) * head, y1 - math.sin(a + 0.5) * head); c.close_path(); fs(c, col, 6)

def dashed_circle(c, x, y, r, col=WHITE, w=7, alpha=0.85, t=0.0):
    c.save(); c.set_dash([22, 16], t * 40); c.new_path(); c.arc(x, y, r, 0, 2 * math.pi)
    c.set_source_rgba(*col, alpha); c.set_line_width(w); c.stroke(); c.restore()

def ring(c, x, y, r, col=WHITE, w=10, alpha=1.0):
    if r <= 0 or alpha <= 0: return
    c.new_path(); c.arc(x, y, r, 0, 2 * math.pi); c.set_source_rgba(*col, alpha); c.set_line_width(w); c.stroke()

def burst(c, x, y, lt, n=10, r0=40, r1=220, col=YEL, seed=0, size=16):
    """particles flying out (lt = seconds since burst)"""
    if lt < 0 or lt > 1.2: return
    rng = np.random.default_rng(seed); f = ease_out(lt / 1.0); al = 1 - clamp((lt - 0.5) / 0.7)
    for i in range(n):
        a = i * 2 * math.pi / n + rng.uniform(-0.3, 0.3); d = lerp(r0, r1 * rng.uniform(0.7, 1.2), f)
        circle(c, x + math.cos(a) * d, y + math.sin(a) * d, size * (1 - 0.5 * f), col, 4, al)

def star(c, x, y, r, col=YEL, ow=6, rot=0.0):
    P = [(x + math.cos(-math.pi / 2 + rot + i * math.pi / 5) * (r if i % 2 == 0 else r * 0.45),
          y + math.sin(-math.pi / 2 + rot + i * math.pi / 5) * (r if i % 2 == 0 else r * 0.45)) for i in range(10)]
    c.new_path(); path(c, P); fs(c, col, ow)

def counter(c, x, y, a, b, p, size=110, fmt="{:,.0f}", prefix="", suffix="", col=YEL):
    v = lerp(a, b, ease_out(p)); text(c, prefix + fmt.format(v) + suffix, x, y, size, col)

# ------------------------------------------------------------------ backgrounds (cached)
_BG = {}
def bg_space(c, t, seed=2, top="#0f1b4d", bot="#3a1f6b"):
    key = ("space", seed, top, bot)
    if key not in _BG:
        S = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); k = cairo.Context(S)
        g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, *rgb(top)); g.add_color_stop_rgb(1, *rgb(bot)); k.set_source(g); k.paint()
        rng = np.random.default_rng(seed)
        stars = [(rng.uniform(-200, W + 200), rng.uniform(-300, H + 300), rng.choice([1.5, 2, 3, 4]), rng.uniform(0, 6)) for _ in range(260)]
        _BG[key] = (S, stars)
    S, stars = _BG[key]
    c.save(); c.identity_matrix(); c.set_source_surface(S); c.paint(); c.restore()
    for x, y, r, ph in stars:
        a = 0.55 + 0.45 * math.sin(t * 2 + ph); c.new_path(); c.arc(x, y, r, 0, 2 * math.pi); c.set_source_rgba(1, 1, 0.9, a); c.fill()

def bg_sky(c, t, top="#59b7ff", bot="#c9ecff"):
    c.save(); c.identity_matrix()
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, *rgb(top)); g.add_color_stop_rgb(1, *rgb(bot)); c.set_source(g); c.paint(); c.restore()
    for i, (x, y, s) in enumerate([(200, 300, 1.0), (760, 220, 0.8), (520, 520, 0.6)]):
        cloud(c, (x + t * 12 * s) % (W + 400) - 200, y, 90 * s)

def bg_color(c, col):
    c.save(); c.identity_matrix(); c.set_source_rgb(*col); c.paint(); c.restore()

def cloud(c, x, y, r, col=WHITE, alpha=1.0):
    c.new_path()
    for dx, dy, k in ((-1.0, 0.2, 0.7), (-0.35, -0.25, 1.0), (0.45, -0.1, 0.85), (1.05, 0.25, 0.6)):
        c.new_sub_path(); c.arc(x + dx * r, y + dy * r, r * k, 0, 2 * math.pi)
    c.set_source_rgba(*col, alpha); c.fill()

# ------------------------------------------------------------------ space objects
def earth(c, cx, cy, r, spin=0.0, ow=10, atmosphere=True, bulge=0.0, bulge_ang=0.0, tilt=0.0, axis=False):
    """Cartoon Earth. spin shifts continents; bulge (0..1) stretches the ocean toward bulge_ang (radians)."""
    if atmosphere:
        g = cairo.RadialGradient(cx, cy, r * 0.95, cx, cy, r * 1.15); g.add_color_stop_rgba(0, 0.45, 0.8, 1, 0.55); g.add_color_stop_rgba(1, 0.45, 0.8, 1, 0)
        c.new_path(); c.arc(cx, cy, r * 1.15, 0, 2 * math.pi); c.set_source(g); c.fill()
    if bulge > 0:  # tidal ocean bulge drawn as a blue ellipse behind the planet
        c.save(); c.translate(cx, cy); c.rotate(bulge_ang); c.scale(1 + 0.22 * bulge, 1 - 0.04 * bulge)
        c.new_path(); c.arc(0, 0, r * 1.02, 0, 2 * math.pi); c.restore(); fs(c, rgb("#5aa9ff"), ow * 0.7)
    c.save(); c.translate(cx, cy); c.rotate(tilt)
    c.new_path(); c.arc(0, 0, r, 0, 2 * math.pi); c.set_source_rgb(*BLUE); c.fill_preserve(); c.save(); c.clip()
    sp = spin * r
    def wrap(x): return ((x + 1.3 * r) % (2.6 * r)) - 1.3 * r       # continents scroll around and come back
    for i, (dx, dy, rr) in enumerate([(-0.45, -0.35, 0.42), (0.35, -0.1, 0.38), (-0.1, 0.5, 0.33), (0.6, 0.55, 0.22), (-0.75, 0.3, 0.2), (1.0, -0.3, 0.3)]):
        x = wrap(dx * r + sp)
        for k in (-2.6, 0, 2.6):
            c.new_path(); path(c, blob(x + k * r, dy * r, rr * r, i + 3)); fs(c, GREEN, ow * 0.5, line=DKGREEN)
    for i in range(4):
        x = wrap((-0.6 + i * 0.4) * r + sp * 1.3)
        for k in (-2.6, 0, 2.6):
            c.new_path(); path(c, blob(x + k * r, (-0.55 + (i % 2) * 0.7) * r, r * 0.13, 20 + i, amp=0.25)); c.set_source_rgba(1, 1, 1, 0.85); c.fill()
    c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD); c.new_path(); c.arc(0, 0, r * 1.01, 0, 2 * math.pi); c.new_sub_path(); c.arc(-r * 0.18, -r * 0.18, r, 0, 2 * math.pi)
    c.set_source_rgba(0.05, 0.05, 0.25, 0.30); c.fill(); c.set_fill_rule(cairo.FILL_RULE_WINDING)
    c.new_path(); c.arc(-r * 0.4, -r * 0.45, r * 0.16, 0, 2 * math.pi); c.set_source_rgba(1, 1, 1, 0.25); c.fill()
    c.restore()
    c.new_path(); c.arc(0, 0, r, 0, 2 * math.pi); c.set_source_rgb(*OUT); c.set_line_width(ow); c.stroke()
    if axis:
        for lw, col in ((ow + 8, OUT), (ow, RED)):
            c.move_to(0, -r * 1.35); c.line_to(0, r * 1.35); c.set_source_rgb(*col); c.set_line_width(lw); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke()
    c.restore()

def moon(c, cx, cy, r, ow=8, face=None, t=0.0, alpha=1.0, crack=0.0):
    c.new_path(); c.arc(cx, cy, r, 0, 2 * math.pi); fs(c, rgb("#e6e6ef"), ow, alpha)
    for dx, dy, k in (((-0.35, -0.3, 0.22), (0.3, 0.1, 0.17), (-0.1, 0.45, 0.14), (0.45, -0.4, 0.1)) if not face else
                      ((-0.55, -0.5, 0.15), (0.58, -0.42, 0.12), (-0.66, 0.3, 0.11), (0.55, 0.55, 0.1))):
        c.new_path(); c.arc(cx + dx * r, cy + dy * r, k * r, 0, 2 * math.pi); fs(c, rgb("#c3c3d3"), ow * 0.4, alpha)
    if crack > 0:
        pts = [(cx - r * 0.1, cy - r), (cx + r * 0.1, cy - r * 0.4), (cx - r * 0.15, cy), (cx + r * 0.2, cy + r * 0.5), (cx, cy + r)]
        n = max(2, int(len(pts) * crack + 0.999)); c.new_path(); path(c, pts[:n], close=False)
        c.set_source_rgba(*OUT, alpha); c.set_line_width(ow * 0.9); c.stroke()
    if face: _face(c, cx, cy + r * 0.05, r * 0.9, face, t, alpha)

def sun(c, cx, cy, r, t=0.0, ow=8, face=None):
    for i in range(12):
        a = i * math.pi / 6 + t * 0.4; r1 = r * (1.45 + 0.08 * math.sin(t * 4 + i))
        c.new_path(); c.move_to(cx + math.cos(a - 0.13) * r * 1.05, cy + math.sin(a - 0.13) * r * 1.05)
        c.line_to(cx + math.cos(a) * r1, cy + math.sin(a) * r1); c.line_to(cx + math.cos(a + 0.13) * r * 1.05, cy + math.sin(a + 0.13) * r * 1.05)
        c.close_path(); fs(c, ORANGE, ow * 0.6)
    c.new_path(); c.arc(cx, cy, r, 0, 2 * math.pi); fs(c, YEL, ow)
    if face: _face(c, cx, cy, r * 0.9, face, t)

def planet(c, cx, cy, r, col, ow=8, ring_col=None, bands=None):
    c.new_path(); c.arc(cx, cy, r, 0, 2 * math.pi); c.set_source_rgb(*col); c.fill_preserve(); c.save(); c.clip()
    for i, b in enumerate(bands or []):
        c.rectangle(cx - r, cy - r + (i * 2 + 1) * r / (len(bands) * 2 + 1) * 2 * 0.95, 2 * r, r * 0.18); c.set_source_rgb(*b); c.fill()
    c.new_path(); c.arc(cx + r * 0.25, cy + r * 0.25, r * 1.05, 0, 2 * math.pi); c.new_sub_path(); c.arc(cx, cy, r * 1.3, 0, 2 * math.pi)
    c.restore(); c.new_path(); c.arc(cx, cy, r, 0, 2 * math.pi); c.set_source_rgb(*OUT); c.set_line_width(ow); c.stroke()
    if ring_col:
        c.save(); c.translate(cx, cy); c.scale(1, 0.28); c.new_path(); c.arc(0, 0, r * 1.7, 0, math.pi)
        c.set_source_rgb(*OUT); c.set_line_width(ow * 3); c.stroke(); c.new_path(); c.arc(0, 0, r * 1.7, 0, math.pi); c.set_source_rgb(*ring_col); c.set_line_width(ow * 2); c.stroke(); c.restore()

def _face(c, x, y, r, mood, t, alpha=1.0):
    """simple face for objects (moon/sun): happy / shock / sad / sleep"""
    blink = (t % 3.3) < 0.1
    for sx in (-1, 1):
        ex = x + sx * r * 0.32
        if blink or mood == "sleep":
            c.new_path(); c.arc(ex, y - r * 0.05, r * 0.11, 0.2, math.pi - 0.2); c.set_source_rgba(*OUT, alpha); c.set_line_width(r * 0.06); c.stroke()
        else:
            k = 1.4 if mood == "shock" else 1.0
            c.new_path(); c.arc(ex, y - r * 0.08, r * 0.09 * k, 0, 2 * math.pi); c.set_source_rgba(*OUT, alpha); c.fill()
    c.new_path()
    if mood == "shock": c.arc(x, y + r * 0.3, r * 0.12, 0, 2 * math.pi); c.set_source_rgba(*OUT, alpha); c.fill()
    elif mood == "sad": c.arc(x, y + r * 0.42, r * 0.18, math.pi * 1.15, math.pi * 1.85); c.set_source_rgba(*OUT, alpha); c.set_line_width(r * 0.06); c.stroke()
    else: c.arc(x, y + r * 0.15, r * 0.2, 0.3, math.pi - 0.3); c.set_source_rgba(*OUT, alpha); c.set_line_width(r * 0.06); c.stroke()
    for sx in (-1, 1):
        c.new_path(); c.arc(x + sx * r * 0.55, y + r * 0.15, r * 0.1, 0, 2 * math.pi); c.set_source_rgba(1, 0.4, 0.45, 0.35 * alpha); c.fill()

# ------------------------------------------------------------------ nature props
def wave_band(c, y, t, col=rgb("#3b8eea"), amp=14, wl=160, speed=2.0, x0=-50, x1=W + 50, bottom=H + 50, ow=8, foam=True):
    pts = [(x, y + math.sin(x / wl * 2 * math.pi + t * speed) * amp + math.sin(x / (wl * 0.53) + t * speed * 1.3) * amp * 0.35) for x in range(int(x0), int(x1) + 20, 20)]
    c.new_path(); path(c, pts + [(x1, bottom), (x0, bottom)]); fs(c, col, ow)
    if foam:
        c.new_path(); path(c, pts, close=False); c.set_source_rgba(1, 1, 1, 0.8); c.set_line_width(ow * 0.8); c.stroke()

def crab(c, x, y, s, t=0.0, mood="happy", walk=0.0):
    c.save(); c.translate(x, y); c.scale(s, s); RD = rgb("#ff5a4f")
    for sx in (-1, 1):
        for k in range(3):
            ph = math.sin(t * 10 * walk + k + (0 if sx < 0 else 2)) * 10 * walk
            c.new_path(); c.move_to(sx * 50, 10 + k * 14); c.line_to(sx * (95 + k * 8), 30 + k * 18 + ph); c.line_to(sx * (105 + k * 8), 70 + k * 10 + ph)
            c.set_source_rgb(*OUT); c.set_line_width(16); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke()
            c.new_path(); c.move_to(sx * 50, 10 + k * 14); c.line_to(sx * (95 + k * 8), 30 + k * 18 + ph); c.line_to(sx * (105 + k * 8), 70 + k * 10 + ph)
            c.set_source_rgb(*RD); c.set_line_width(8); c.stroke()
        c.new_path(); c.move_to(sx * 55, -20); c.line_to(sx * 110, -70); c.set_source_rgb(*OUT); c.set_line_width(20); c.stroke()
        c.new_path(); c.move_to(sx * 55, -20); c.line_to(sx * 110, -70); c.set_source_rgb(*RD); c.set_line_width(11); c.stroke()
        snap = 0.25 + 0.2 * math.sin(t * 6 + sx)
        c.new_path(); c.arc(sx * 125, -95, 34, -math.pi / 2 + snap if sx > 0 else math.pi / 2 + snap, math.pi * 1.5 - snap if sx > 0 else math.pi * 2.5 - snap)
        c.line_to(sx * 125, -95); c.close_path(); fs(c, RD, 7)
    c.save(); c.scale(1, 0.62); c.new_path(); c.arc(0, 0, 85, 0, 2 * math.pi); c.restore(); fs(c, RD, 8)
    for sx in (-1, 1):
        c.new_path(); c.move_to(sx * 22, -40); c.line_to(sx * 28, -85); c.set_source_rgb(*OUT); c.set_line_width(8); c.stroke()
        c.new_path(); c.arc(sx * 28, -95, 17, 0, 2 * math.pi); fs(c, WHITE, 6)
        c.new_path(); c.arc(sx * 28 + 3, -93, 8 * (1.3 if mood == "shock" else 1), 0, 2 * math.pi); c.set_source_rgb(*OUT); c.fill()
    c.new_path()
    if mood == "sad": c.arc(0, 18, 18, math.pi * 1.15, math.pi * 1.85)
    elif mood == "shock": c.arc(0, 10, 10, 0, 2 * math.pi)
    else: c.arc(0, 0, 18, 0.3, math.pi - 0.3)
    c.set_source_rgb(*OUT); c.set_line_width(6); c.stroke(); c.restore()

def coral(c, x, y, s, t=0.0, col=PINK, glow=0.0):
    c.save(); c.translate(x, y); c.scale(s, s)
    def br(x0, y0, a, L, d):
        if d == 0 or L < 12: return
        sw = math.sin(t * 1.5 + d + x0 * 0.01) * 0.06
        x1, y1 = x0 + math.cos(a + sw) * L, y0 + math.sin(a + sw) * L
        for lw, cc in ((L * 0.32 + 10, OUT), (L * 0.32, col)):
            c.new_path(); c.move_to(x0, y0); c.line_to(x1, y1); c.set_source_rgb(*cc); c.set_line_width(lw); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke()
        if d == 1:
            c.new_path(); c.arc(x1, y1, L * 0.22, 0, 2 * math.pi); fs(c, mix(col, WHITE, 0.4), 5)
        br(x1, y1, a - 0.45, L * 0.72, d - 1); br(x1, y1, a + 0.4, L * 0.72, d - 1)
    br(0, 0, -math.pi / 2, 110, 4)
    if glow > 0:
        for i in range(10):
            u = (t * 0.4 + i / 10) % 1
            c.new_path(); c.arc(math.sin(i * 2.3) * 160, -150 - u * 300, 9, 0, 2 * math.pi); c.set_source_rgba(1, 0.95, 0.7, glow * math.sin(math.pi * u)); c.fill()
    c.restore()

def snowflake(c, x, y, r, col=WHITE, ow=10):
    for k in range(3):
        a = k * math.pi / 3
        for lw, cc in ((ow + 8, OUT), (ow, col)):
            c.new_path(); c.move_to(x - math.cos(a) * r, y - math.sin(a) * r); c.line_to(x + math.cos(a) * r, y + math.sin(a) * r)
            c.set_source_rgb(*cc); c.set_line_width(lw); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke()

# ------------------------------------------------------------------ Leo (original character)
LEO_POSES = {  # (left shoulder, left elbow, right shoulder, right elbow) degrees; 0 = arm straight down, + = outward/up
    "idle": (15, 10, 15, 10), "point_up": (15, 10, 150, 10), "point_right": (15, 10, 95, 0), "point_left": (95, 0, 15, 10),
    "shock": (140, 40, 140, 40), "cheer": (165, -10, 165, -10), "think": (15, 10, 40, 140), "shrug": (60, -80, 60, -80),
    "wave": (15, 10, 150, 40 * 0), "cover": (40, 150, 40, 150),
}
LEO_FACES = {  # eye scale, pupil scale, brow lift (+ up), brow tilt (+ worried), mouth: (kind, size)
    "happy": (1.0, 1.0, 0, 0, ("smile", 1.0)), "shock": (1.25, 0.7, 18, 0, ("o", 1.3)), "curious": (1.0, 1.0, 12, -0.4, ("small", 1.0)),
    "scared": (1.25, 0.6, 14, 1.0, ("wobble", 1.0)), "sad": (0.95, 1.0, 0, 1.0, ("frown", 1.0)), "wow": (1.15, 1.1, 16, 0, ("grin", 1.2)),
    "smirk": (0.9, 1.0, 4, -0.6, ("smirk", 1.0)), "worried": (1.05, 0.9, 8, 0.8, ("flat", 1.0)),
}

def leo(c, x, y, s, pose="idle", face="happy", t=0.0, ow=8, look=(0, 0), bob=True, wave=False, colors=None, mirror=False):
    """Leo, an original curious kid: curly hair, brown skin, yellow hoodie with a white star. (x, y) = feet, s = scale (1 = ~720 px tall).
    colors=(skin, hoodie, hair) re-colours him into another kid (e.g. a friend); mirror=True flips left/right."""
    skin, hood, hair = colors or (rgb("#a86b45"), rgb("#ffc928"), rgb("#2b1a14"))
    lS, lE, rS, rE = LEO_POSES.get(pose, LEO_POSES["idle"])
    if wave: rE = 40 + 35 * math.sin(t * 9)
    by = -abs(math.sin(t * 2.2)) * 8 if bob else 0
    c.save(); c.translate(x, y + by); c.scale(-s if mirror else s, s); c.set_line_join(cairo.LINE_JOIN_ROUND); c.set_line_cap(cairo.LINE_CAP_ROUND)
    def fsl(col, lw=ow): fs(c, col, lw)
    for sx in (-1, 1):
        c.new_path(); c.rectangle(sx * 38 - 22, -175, 44, 150); fsl(rgb("#3b5bdb"))
        c.save(); c.translate(sx * 45, -22); c.scale(1.6, 1); c.new_path(); c.arc(0, 0, 26, 0, 2 * math.pi); c.restore(); fsl(RED)
    def arm(side, sh, el):
        p0 = (side * 82, -385); a1 = math.radians(sh); p1 = (p0[0] + side * math.sin(a1) * 120, p0[1] + math.cos(a1) * 120)
        a2 = math.radians(sh + el); p2 = (p1[0] + side * math.sin(a2) * 110, p1[1] + math.cos(a2) * 110)
        for lw, col in ((64, OUT), (46, hood)):
            c.new_path(); c.move_to(*p0); c.line_to(*p1); c.line_to(*p2); c.set_source_rgb(*col); c.set_line_width(lw); c.stroke()
        c.new_path(); c.arc(p2[0], p2[1], 27, 0, 2 * math.pi); fsl(skin)
    arm(-1, lS, lE)
    c.new_path(); c.move_to(-95, -420); c.curve_to(-122, -320, -116, -215, -102, -165); c.line_to(102, -165); c.curve_to(116, -215, 122, -320, 95, -420)
    c.curve_to(60, -450, -60, -450, -95, -420); c.close_path(); fsl(hood)
    star(c, 0, -300, 34, WHITE, 0)
    arm(1, rS, rE)
    hy = -585; lx, ly = look
    for i in range(11):
        a = math.pi + i * math.pi / 10; c.new_path(); c.arc(math.cos(a) * 150, hy - 20 + math.sin(a) * 140, 52, 0, 2 * math.pi); fsl(hair, ow * 0.8)
    c.save(); c.translate(0, hy); c.scale(1, 1.05); c.new_path(); c.arc(0, 0, 150, 0, 2 * math.pi); c.restore(); fsl(skin)
    for i in range(7):
        a = math.pi * 1.1 + i * math.pi * 0.8 / 6; c.new_path(); c.arc(math.cos(a) * 125, hy - 30 + math.sin(a) * 110, 42, 0, 2 * math.pi); c.set_source_rgb(*hair); c.fill()
    es, ps, bl, bt, (mk, msz) = LEO_FACES.get(face, LEO_FACES["happy"])
    blink = ((t + 1.3) % 3.4) < 0.1
    for sx in (-1, 1):
        c.new_path(); c.arc(sx * 152, hy + 10, 26, 0, 2 * math.pi); fsl(skin)
        ex = sx * 58
        if blink:
            c.new_path(); c.move_to(ex - 30, hy + 10); c.line_to(ex + 30, hy + 10); c.set_source_rgb(*OUT); c.set_line_width(ow * 1.2); c.stroke()
        else:
            c.save(); c.translate(ex, hy + 10); c.scale(es, 1.25 * es); c.new_path(); c.arc(0, 0, 40, 0, 2 * math.pi); c.restore(); fsl(WHITE, ow * 0.8)
            px, py = ex + 6 + lx * 16, hy - 4 + ly * 18
            c.new_path(); c.arc(px, py, 19 * ps, 0, 2 * math.pi); c.set_source_rgb(*OUT); c.fill()
            c.new_path(); c.arc(px - 6, py - 7, 7 * ps, 0, 2 * math.pi); c.set_source_rgb(1, 1, 1); c.fill()
        byy = hy - 72 - bl
        inner, outer = (ex - sx * 30, byy - bt * 14), (ex + sx * 34, byy + bt * 6)
        c.new_path(); c.move_to(*inner); c.curve_to(inner[0] + sx * 15, min(inner[1], outer[1]) - 22, outer[0] - sx * 15, min(inner[1], outer[1]) - 22, *outer)
        c.set_source_rgb(*OUT); c.set_line_width(ow * 1.4); c.stroke()
        c.new_path(); c.arc(sx * 95, hy + 75, 22, 0, 2 * math.pi); c.set_source_rgba(0.9, 0.35, 0.3, 0.35); c.fill()
    my = hy + 92; c.new_path()
    if mk == "o":
        c.save(); c.translate(0, my); c.scale(1, 1.3); c.arc(0, 0, 28 * msz, 0, 2 * math.pi); c.restore(); fsl(rgb("#5a1414"), ow * 0.8)
    elif mk == "grin":
        c.move_to(-55, my - 12); c.curve_to(-30, my + 50, 30, my + 50, 55, my - 12); c.close_path(); fsl(rgb("#5a1414"), ow * 0.8)
        c.new_path(); c.rectangle(-40, my - 10, 80, 14); c.set_source_rgb(1, 1, 1); c.fill()
    elif mk == "smile": c.arc(0, my - 25, 42, 0.35, math.pi - 0.35); c.set_source_rgb(*OUT); c.set_line_width(ow * 1.2); c.stroke()
    elif mk == "frown": c.arc(0, my + 30, 34, math.pi * 1.2, math.pi * 1.8); c.set_source_rgb(*OUT); c.set_line_width(ow * 1.2); c.stroke()
    elif mk == "wobble":
        c.move_to(-40, my); [c.line_to(-40 + i * 10, my + (6 if i % 2 else -6)) for i in range(9)]; c.set_source_rgb(*OUT); c.set_line_width(ow); c.stroke()
    elif mk == "smirk": c.move_to(-30, my + 4); c.curve_to(0, my + 14, 25, my + 5, 40, my - 14); c.set_source_rgb(*OUT); c.set_line_width(ow * 1.2); c.stroke()
    elif mk == "small": c.arc(0, my, 14, 0, 2 * math.pi); fsl(rgb("#5a1414"), ow * 0.7)
    else: c.move_to(-30, my); c.line_to(30, my); c.set_source_rgb(*OUT); c.set_line_width(ow * 1.2); c.stroke()
    if face in ("scared", "worried"):  # sweat drop
        u = (t * 0.8) % 1; dx, dy = 140, hy - 60 + u * 60
        c.new_path(); c.move_to(dx, dy - 26); c.curve_to(dx + 20, dy, dx + 14, dy + 16, dx, dy + 16); c.curve_to(dx - 14, dy + 16, dx - 20, dy, dx, dy - 26)
        fs(c, SKY, 5, 1 - u)
    c.restore()

# ------------------------------------------------------------------ captions
def caption(c, group, t, y=H * 0.72, size=84):
    c.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    p = ease_back((t - group[0][1]) / 0.18); sz = size * (0.85 + 0.15 * p); c.set_font_size(sz)
    ws = [w.upper() for w, _, _ in group]; sp = sz * 0.28; wid = [c.text_extents(w).x_advance for w in ws]
    tot = sum(wid) + sp * (len(ws) - 1)
    if tot > W * 0.9:
        k = W * 0.9 / tot; sz *= k; c.set_font_size(sz); sp *= k; wid = [w * k for w in wid]; tot *= k
    x = W / 2 - tot / 2
    for (w, s0, e0), ww, wd in zip(group, ws, wid):
        col = YEL if s0 <= t < e0 + 0.05 else WHITE
        c.move_to(x, y); c.text_path(ww); c.set_source_rgb(*OUT); c.set_line_width(sz * 0.2); c.set_line_join(cairo.LINE_JOIN_ROUND); c.stroke()
        c.move_to(x, y); c.set_source_rgb(*col); c.show_text(ww); x += wd + sp

# ------------------------------------------------------------------ audio
def _env(n, a, r): t = np.arange(n) / SR; return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / max(r, 1e-4))
def sfx_pop(f=600):
    n = int(0.18 * SR); t = np.arange(n) / SR; return (np.sin(2 * np.pi * (f + 900 * t / t[-1]) * t) * _env(n, 0.003, 0.05) * 0.6).astype(np.float32)
def sfx_whoosh(seed=1, dur=0.45):
    rng = np.random.default_rng(seed); n = int(dur * SR); nz = rng.standard_normal(n); k = 18; nz = np.convolve(nz, np.ones(k) / k, "same")
    return (nz * np.sin(np.pi * np.arange(n) / n) ** 2 * 0.9).astype(np.float32)
def sfx_boom(f=45, dur=1.6):
    n = int(dur * SR); t = np.arange(n) / SR; rng = np.random.default_rng(3)
    nz = np.convolve(rng.standard_normal(n), np.ones(40) / 40, "same")
    return ((np.sin(2 * np.pi * f * t * (1 - 0.35 * t)) * 0.9 + nz * 1.5) * np.exp(-t * 2.6)).astype(np.float32)
def sfx_ding(f=1320):
    n = int(0.9 * SR); t = np.arange(n) / SR; return ((np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.76 * t)) * _env(n, 0.002, 0.25) * 0.4).astype(np.float32)
def sfx_shatter(seed=4):
    rng = np.random.default_rng(seed); n = int(1.2 * SR); out = np.zeros(n, np.float32)
    for i in range(40):
        s0 = int(rng.uniform(0, 0.6) * SR); m = int(0.08 * SR); tt = np.arange(m) / SR; f = rng.uniform(2500, 6000)
        out[s0:s0 + m] += (np.sin(2 * np.pi * f * tt) * np.exp(-tt * 60) * rng.uniform(0.1, 0.35)).astype(np.float32)[:len(out[s0:s0 + m])]
    return out + sfx_boom(60, 1.2)[:n] * 0.5
def sfx_tick():
    n = int(0.05 * SR); t = np.arange(n) / SR; return (np.sin(2 * np.pi * 2200 * t) * np.exp(-t * 120) * 0.5).astype(np.float32)

def music(n, bpm=104, seed=0):
    """Light, curious synth bed: plucked arpeggio + soft pad + gentle kick (original)."""
    t = np.arange(n) / SR; out = np.zeros(n, np.float32)
    chords = [[220, 261.6, 329.6], [174.6, 220, 261.6], [196, 246.9, 293.7], [164.8, 207.7, 246.9]]
    beat = 60 / bpm; bar = int(4 * beat * SR); step = int(beat / 2 * SR)
    for i0 in range(0, n, bar):
        ch = chords[(i0 // bar) % 4]; L = min(bar, n - i0); tt = np.arange(L) / SR
        envp = np.minimum(1, tt / 0.6) * np.minimum(1, (L / SR - tt) / 0.4 + 0.05)
        for f in ch: out[i0:i0 + L] += (envp * np.sin(2 * np.pi * f * tt) * 0.05).astype(np.float32)
        for k in range(8):
            s0 = i0 + k * step
            if s0 >= n: break
            m = min(int(0.4 * SR), n - s0); ta = np.arange(m) / SR; f = ch[[0, 1, 2, 1][k % 4]] * 2
            out[s0:s0 + m] += (np.sin(2 * np.pi * f * ta) * np.exp(-ta * 7) * 0.09 + np.sin(2 * np.pi * f * 2 * ta) * np.exp(-ta * 12) * 0.03).astype(np.float32)
        for k in range(4):
            s0 = i0 + int(k * beat * SR); m = min(int(0.2 * SR), n - s0)
            if m > 0: ta = np.arange(m) / SR; out[s0:s0 + m] += (np.sin(2 * np.pi * 60 * ta * (1 - 2 * ta)) * np.exp(-ta * 20) * 0.22).astype(np.float32)
    return out

def place(buf, clip, t, gain=1.0):
    s0 = int(t * SR)
    if s0 >= len(buf) or s0 + len(clip) <= 0: return
    a = max(0, -s0); s0 = max(0, s0); m = min(len(clip) - a, len(buf) - s0)
    buf[s0:s0 + m] += clip[a:a + m] * gain

# ------------------------------------------------------------------ cinematic look
def glow(c, x, y, r, col=YEL, alpha=0.6):
    """soft light halo"""
    g = cairo.RadialGradient(x, y, 0, x, y, r); g.add_color_stop_rgba(0, *col, alpha); g.add_color_stop_rgba(0.35, *col, alpha * 0.35); g.add_color_stop_rgba(1, *col, 0)
    c.new_path(); c.arc(x, y, r, 0, 2 * math.pi); c.set_source(g); c.fill()

def god_rays(c, x, y, t, n=9, length=1600, col=(1, 0.92, 0.7), alpha=0.10, spread=1.2, ang=1.1):
    """volumetric light shafts fanning out from (x, y) around direction ang (radians)"""
    for i in range(n):
        a = ang - spread / 2 + spread * i / max(1, n - 1) + 0.03 * math.sin(t * 0.7 + i)
        w = 0.035 + 0.025 * math.sin(i * 2.1 + t * 0.5)
        g = cairo.LinearGradient(x, y, x + math.cos(a) * length, y + math.sin(a) * length)
        g.add_color_stop_rgba(0, *col, alpha * (0.7 + 0.3 * math.sin(i * 1.7 + t))); g.add_color_stop_rgba(1, *col, 0)
        c.new_path(); c.move_to(x, y); c.line_to(x + math.cos(a - w) * length, y + math.sin(a - w) * length)
        c.line_to(x + math.cos(a + w) * length, y + math.sin(a + w) * length); c.close_path(); c.set_source(g); c.fill()

def lens_flare(c, x, y, alpha=0.5):
    """flare ghosts along the line from the light through the screen centre"""
    dx, dy = W / 2 - x, H / 2 - y
    glow(c, x, y, 260, (1, 0.95, 0.8), alpha * 0.8)
    for k, r, col in ((0.5, 40, (1, 0.8, 0.4)), (0.9, 70, (0.5, 0.8, 1)), (1.3, 28, (1, 0.5, 0.8)), (1.7, 110, (0.6, 1, 0.8))):
        glow(c, x + dx * k, y + dy * k, r, col, alpha * 0.35)
    c.new_path(); c.move_to(x - 420, y); c.line_to(x + 420, y); c.set_source_rgba(1, 0.95, 0.85, alpha * 0.35); c.set_line_width(3); c.stroke()

def rim_light(c, cx, cy, r, ang=-2.4, col=(1, 0.95, 0.8), alpha=0.75, w=None):
    """bright rim on the lit side of a round object (light coming from direction ang)"""
    w = w or max(6, r * 0.06)
    c.new_path(); c.arc(cx, cy, r - w * 0.4, ang - 0.9, ang + 0.9); c.set_source_rgba(*col, alpha); c.set_line_width(w); c.stroke()
    glow(c, cx + math.cos(ang) * r, cy + math.sin(ang) * r, r * 0.6, col, alpha * 0.25)

_NEB = {}
def bg_cinema(c, t, seed=5, top="#03061a", bot="#0d0a2e", neb=(("#2c3fb8", 0.5), ("#0f7fa8", 0.4), ("#6b2fb0", 0.35))):
    """deep space with soft nebula clouds, depth-layered stars (near stars drift with parallax)"""
    key = (seed, top, bot)
    if key not in _NEB:
        from PIL import Image, ImageFilter
        S = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); k = cairo.Context(S)
        g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, *rgb(top)); g.add_color_stop_rgb(1, *rgb(bot)); k.set_source(g); k.paint()
        rng = np.random.default_rng(seed)
        for col, a in neb:
            for _ in range(5):
                k.new_path(); path(k, blob(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(200, 420), int(rng.integers(0, 99)), 0.45)); k.set_source_rgba(*rgb(col), a * 0.5); k.fill()
        for _ in range(900):
            k.new_path(); k.arc(rng.uniform(0, W), rng.uniform(0, H), rng.choice([0.6, 0.9, 1.2]), 0, 2 * math.pi); k.set_source_rgba(1, 1, 1, rng.uniform(0.3, 0.8)); k.fill()
        S.flush(); arr = np.ndarray((H, W, 4), np.uint8, S.get_data()).copy()
        im = Image.fromarray(arr[..., :3]).filter(ImageFilter.GaussianBlur(28))
        sharp = Image.fromarray(arr[..., :3]); blurred = np.asarray(im).astype(np.float32); st = np.asarray(sharp).astype(np.float32)
        out = np.maximum(blurred, st * (st.max(axis=2, keepdims=True) > 150))  # nebula blurred, tiny stars kept sharp
        rgba = np.dstack([out.clip(0, 255).astype(np.uint8), np.full((H, W), 255, np.uint8)])
        S2 = cairo.ImageSurface.create_for_data(bytearray(rgba.tobytes()), cairo.FORMAT_RGB24, W, H)
        stars = [(rng.uniform(-300, W + 300), rng.uniform(-300, H + 300), rng.choice([2, 2.5, 3.5]), rng.uniform(0, 6)) for _ in range(70)]
        _NEB[key] = (S2, stars)
    S2, stars = _NEB[key]
    c.save(); c.identity_matrix(); c.set_source_surface(S2); c.paint(); c.restore()
    for x, y, r, ph in stars:  # near stars (they move with the camera = parallax)
        a = 0.6 + 0.4 * math.sin(t * 1.7 + ph); glow(c, x, y, r * 5, (0.85, 0.9, 1), a * 0.35)
        c.new_path(); c.arc(x, y, r, 0, 2 * math.pi); c.set_source_rgba(1, 1, 1, a); c.fill()

def blurred(c, draw, radius=8):
    """draw something out of focus (depth of field): draw(ctx) is rendered with the current transform, then blurred"""
    from PIL import Image, ImageFilter
    S = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); k = cairo.Context(S); k.set_matrix(c.get_matrix()); draw(k); S.flush()
    a = np.ndarray((H, W, 4), np.uint8, S.get_data())
    im = Image.fromarray(a.copy(), "RGBA").resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(radius / 4)).resize((W, H), Image.BILINEAR)
    b = np.ascontiguousarray(np.asarray(im)); S2 = cairo.ImageSurface.create_for_data(bytearray(b.tobytes()), cairo.FORMAT_ARGB32, W, H)
    c.save(); c.identity_matrix(); c.set_source_surface(S2); c.paint(); c.restore()

class Post:
    """film look applied to every frame: bloom, split-tone grade, contrast, vignette, grain, impact flashes"""
    def __init__(self, strength=1.0):
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.sqrt(((x - W / 2) / (W * 0.62)) ** 2 + ((y - H / 2) / (H * 0.62)) ** 2)
        self.vig = (1 - 0.42 * np.clip(d - 0.35, 0, 1) ** 1.4)[..., None].astype(np.float32)
        rng = np.random.default_rng(1); self.grain = [rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32) for _ in range(6)]
        self.k = strength
    def __call__(self, img, t, flash=0.0):
        from PIL import Image, ImageFilter
        f = img.astype(np.float32) / 255
        br = np.clip((f - 0.62) * 2.2, 0, 1)
        small = Image.fromarray((br * 255).astype(np.uint8)).resize((W // 6, H // 6), Image.BILINEAR).filter(ImageFilter.GaussianBlur(5))
        bloom = np.asarray(small.resize((W, H), Image.BILINEAR)).astype(np.float32) / 255
        f = f + bloom * 0.5 * self.k
        l = f.mean(axis=2, keepdims=True)
        f = f + (1 - l) * np.array([-0.025, 0.005, 0.045], np.float32) * self.k + l * np.array([0.04, 0.015, -0.03], np.float32) * self.k
        f = 0.5 + (f - 0.5) * (1 + 0.10 * self.k)
        f = f * self.vig
        g = self.grain[int(t * 24) % 6]; f = f + np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None] * 0.018 * self.k
        if flash > 0: f = f + flash
        return (np.clip(f, 0, 1) * 255).astype(np.uint8)

def music_cine(n, impacts=(), seed=0):
    """Cinematic score: slow evolving pad + low drone + soft pulse; risers into, and 'braam' hits on, each impact."""
    t = np.arange(n) / SR; out = np.zeros(n, np.float32)
    chords = [[110, 164.8, 220, 261.6], [87.3, 130.8, 174.6, 220], [98, 146.8, 196, 246.9], [82.4, 123.5, 164.8, 207.7]]
    seg = int(SR * 5.0)
    for i0 in range(0, n, seg):
        ch = chords[(i0 // seg) % 4]; L = min(seg + int(SR), n - i0); tt = np.arange(L) / SR
        env = np.minimum(1, tt / 1.5) * np.minimum(1, np.maximum(0, (L / SR - tt)) / 1.5)
        for f in ch:
            for det in (-0.004, 0.0, 0.004):
                ph = 2 * np.pi * f * (1 + det) * tt
                out[i0:i0 + L] += (env * (np.sin(ph) + 0.25 * np.sin(2 * ph) + 0.1 * np.sin(3 * ph)) * 0.025).astype(np.float32)
    out += (np.sin(2 * np.pi * 41.2 * t) * 0.10 * (0.7 + 0.3 * np.sin(2 * np.pi * 0.1 * t))).astype(np.float32)
    for b in np.arange(0, n / SR, 60 / 70):  # soft heartbeat pulse
        s0 = int(b * SR); m = min(int(0.25 * SR), n - s0)
        if m > 0: ta = np.arange(m) / SR; out[s0:s0 + m] += (np.sin(2 * np.pi * 55 * ta) * np.exp(-ta * 14) * 0.18).astype(np.float32)
    rng = np.random.default_rng(seed)
    for ti in impacts:
        L = int(1.6 * SR); s0 = int((ti - 1.6) * SR)
        if s0 > 0:  # riser
            nz = rng.standard_normal(L).astype(np.float32); ramp = np.linspace(0, 1, L) ** 2.5
            hp = nz - np.convolve(nz, np.ones(30) / 30, "same")
            out[s0:s0 + L] += (hp * ramp * 0.22)[:len(out[s0:s0 + L])]
        L = int(3.0 * SR); s0 = int(ti * SR); tt = np.arange(min(L, n - s0)) / SR
        if len(tt):  # braam
            br = sum(np.tanh(3 * np.sin(2 * np.pi * f * tt)) for f in (55, 82.4, 110, 164.8)) * np.exp(-tt * 1.2) * np.minimum(1, tt / 0.02) * 0.10
            sub = np.sin(2 * np.pi * 38 * tt) * np.exp(-tt * 2) * 0.5
            out[s0:s0 + len(tt)] += (br + sub).astype(np.float32)
    return out

# ------------------------------------------------------------------ runner
class Scene:
    """What a scene draw function receives."""
    def __init__(s, t, t0, Wt, B): s.t, s.t0, s.lt, s.Wt, s.B = t, t0, t - t0, Wt, B
    def P(s, start, dur=0.4): return clamp((s.t - start) / max(dur, 1e-3))      # 0..1 progress from an absolute start time
    def W(s, beat, word=None, end=False): return s.Wt(beat, word, end)

def cam_at(t, keys):
    if t <= keys[0][0]: return keys[0][1:]
    for (t0, *a), (t1, *b) in zip(keys, keys[1:]):
        if t <= t1:
            f = ease((t - t0) / max(t1 - t0, 1e-3)); return tuple(x + (y - x) * f for x, y in zip(a, b))
    return keys[-1][1:]

def load_episode(path):
    spec = importlib.util.spec_from_file_location("episode", path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def build_timeline(ep, cache):
    import render
    key = json.dumps([ep.VOICE, ep.SPEED, ep.BEATS])
    if os.path.exists(cache + ".json"):
        meta = json.load(open(cache + ".json"))
        if meta.get("key") == key: return meta["beats"], np.load(cache + ".npy")
    t = 0.05; beats = []; clips = []
    for name, txt, pause in ep.BEATS:
        a = render.tts(txt, ep.VOICE, ep.SPEED); d = len(a) / SR
        beats.append({"name": name, "t0": t, "s0": t, "s1": t + d, "words": render.word_times(txt, t, d)}); clips.append((t, a))
        t += d + 0.22 + pause
    total = t + 0.2; vo = np.zeros(int(total * SR), np.float32)
    for t0, a in clips: place(vo, a, t0)
    for i, b in enumerate(beats): b["t1"] = beats[i + 1]["t0"] if i + 1 < len(beats) else total
    json.dump({"key": key, "beats": beats}, open(cache + ".json", "w")); np.save(cache + ".npy", vo)
    return beats, vo

def mk_W(beats):
    B = {b["name"]: b for b in beats}
    def Wt(beat, word=None, end=False):
        b = B[beat]
        if word is None: return b["t0"]
        for w, s, e in b["words"]:
            if w.lower().strip(".,?!…'\"").startswith(word.lower()): return e if end else s
        raise KeyError(f"word '{word}' not in beat '{beat}'")
    return Wt, B

def draw_frame(c, ep, t, beats, Wt, B, CAM):
    import render
    starts = [Wt(b) for b, _ in ep.SCENES]; starts[0] = -1.0
    idx = max(i for i, s in enumerate(starts) if t >= s)
    name, fn = ep.SCENES[idx]; st = starts[idx]
    c.identity_matrix()
    keys = CAM.get(name) or [(st, W / 2, H / 2, 1.0), (starts[idx + 1] if idx + 1 < len(starts) else st + 6, W / 2, H / 2, 1.04)]
    cx, cy, z = cam_at(t, keys)
    if idx > 0:  # punch-in on every cut
        z *= 1 + 0.07 * (1 - ease_out((t - st) / 0.3))
    for ti in getattr(ep, "_impacts", []):  # camera shake after impacts
        if 0 <= t - ti < 0.9:
            k = (1 - (t - ti) / 0.9) ** 2 * 26 / z; cx += math.sin(t * 71) * k; cy += math.cos(t * 59) * k
    c.save(); c.translate(W / 2, H / 2); c.scale(z, z); c.translate(-cx, -cy)
    fn(c, Scene(t, max(st, 0), Wt, B)); c.restore()
    hook = getattr(ep, "HOOK", None)
    if hook and t < B[ep.BEATS[1][0]]["t0"] + 0.2:
        al = 1 - clamp((t - B[ep.BEATS[1][0]]["t0"]) / 0.2); pulse = 1 + 0.025 * math.sin(t * 6)
        text(c, hook[0], W / 2, 200, 80, WHITE, alpha=al); text(c, hook[1], W / 2, 300, 104 * pulse, YEL, alpha=al)
    for b in beats:
        if b["s0"] - 0.05 <= t <= b["s1"] + 0.2:
            for g in render.build_groups([tuple(w) for w in b["words"]]):
                if g[0][1] <= t < g[-1][2] + 0.15: caption(c, g, t, getattr(ep, "CAPTION_Y", H * 0.72)); break

def build_audio(ep, beats, vo, Wt, B):
    n = len(vo); fx = np.zeros(n, np.float32)
    m = music_cine(n, getattr(ep, "_impacts", [])) * 1.1 if getattr(ep, "LOOK", "") == "cinematic" else music(n) * 0.9
    for i, (b, _) in enumerate(ep.SCENES):
        if i: place(fx, sfx_whoosh(i), Wt(b) - 0.2, 0.35)
    if hasattr(ep, "sfx"): ep.sfx(Wt, B, lambda clip, t, g=1.0: place(fx, clip, t, g))
    hop = 480; e = np.sqrt(np.convolve(vo ** 2, np.ones(hop) / hop, "same")); duck = np.convolve(1 - 0.5 * np.clip(e / 0.05, 0, 1), np.ones(4800) / 4800, "same")
    mix_ = vo + m * 0.28 * duck + fx * 0.6
    return (np.tanh(mix_ * 1.1) * 0.92).astype(np.float32)

def main():
    ep_path, out = sys.argv[1], sys.argv[2]; ep = load_episode(ep_path)
    work = os.path.join(ROOT, "out", "cartoon", ep.NAME); os.makedirs(work, exist_ok=True)
    beats, vo = build_timeline(ep, os.path.join(work, "vo")); Wt, B = mk_W(beats); total = len(vo) / SR
    CAM = ep.cams(Wt, B) if hasattr(ep, "cams") else {}
    ep._impacts = ep.impacts(Wt, B) if hasattr(ep, "impacts") else []
    post = Post() if getattr(ep, "LOOK", "") == "cinematic" else None
    S = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); c = cairo.Context(S)
    def frame(t):
        draw_frame(c, ep, t, beats, Wt, B, CAM); S.flush()
        img = np.ndarray((H, W, 4), np.uint8, S.get_data())[..., 2::-1]
        if post:
            fl = max([0.0] + [0.55 * (1 - (t - ti) / 0.35) for ti in ep._impacts if 0 <= t - ti < 0.35])
            img = post(img, t, fl)
        return img
    if "--stills" in sys.argv:
        from PIL import Image
        os.makedirs(out, exist_ok=True)
        for v in sys.argv[sys.argv.index("--stills") + 1:]:
            t = float(v); Image.fromarray(np.ascontiguousarray(frame(t))).resize((540, 960)).save(os.path.join(out, f"t{t:06.2f}.png"))
        print("beats:", [(b["name"], round(b["t0"], 2)) for b in beats], "total", round(total, 1)); return
    import soundfile as sf
    wav = os.path.join(work, "mix.wav"); sf.write(wav, build_audio(ep, beats, vo, Wt, B), SR)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                           "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    nf = int(total * FPS)
    for fi in range(nf):
        ff.stdin.write(np.ascontiguousarray(frame(fi / FPS)).tobytes())
        if fi % 300 == 0: print(f"{fi}/{nf}", flush=True)
    ff.stdin.close(); ff.wait()
    meta = {k: getattr(ep, k, None) for k in ("TITLE", "DESCRIPTION", "TAGS")}; meta.update(file=out, duration=round(total, 1))
    json.dump(meta, open(os.path.splitext(out)[0] + ".json", "w"), indent=2)
    print("DONE", out, round(total, 1))

if __name__ == "__main__":
    main()
