"""Parchment engine: an old ink manuscript that draws itself and comes alive (Dark History look).

Library used by per-episode scene files (e.g. engine/parch_dancing.py).
- Procedural aged parchment (fibres, stains, burnt edges, candle flicker)
- Tapered ink strokes that draw on, with hand-drawn "line boil"
- Hatching, sepia washes, red-ink accents, Cinzel stamps, ink captions
- Rigged ink figures (woman / man / skeleton) with a dance cycle
Rendering: cairo (antialiased) -> multiply onto parchment with numpy -> ffmpeg.
"""
import math, os
import numpy as np
import cairo

W, H, FPS = 1080, 1920, 30
PAPER = np.array([229, 207, 163], np.float32)
INK = (0.15, 0.09, 0.05)
RED = (0.62, 0.10, 0.06)
SEPIA = (0.62, 0.45, 0.26)
BOIL = [0]          # current boil frame (hand-drawn line jitter), set per frame
BOIL_AMP = 1.3

def clamp(v, a=0.0, b=1.0): return max(a, min(b, v))
def ease(p): p = clamp(p); return p * p * (3 - 2 * p)
def ease_out(p): return 1 - (1 - clamp(p)) ** 3

# ------------------------------------------------------------------ parchment
def _fbm(shape, seed, octaves=6, base=4):
    rng = np.random.default_rng(seed); h, w = shape; out = np.zeros(shape, np.float32); amp = 1.0; tot = 0
    from PIL import Image
    for o in range(octaves):
        n = base * 2 ** o
        g = rng.standard_normal((max(2, n * h // w), n)).astype(np.float32)
        im = Image.fromarray(g).resize((w, h), Image.BICUBIC)
        out += np.asarray(im) * amp; tot += amp; amp *= 0.55
    out /= tot
    return (out - out.mean()) / (out.std() + 1e-6)

def make_paper(seed=3):
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    f = _fbm((H, W), seed)
    col = PAPER[None, None, :] * (1 + 0.045 * f[..., None])
    blot = _fbm((H, W), seed + 1, 4, 3)
    col *= (1 - 0.06 * np.clip(blot, 0, 3)[..., None] * np.array([0.8, 1.0, 1.3]))
    # stains (coffee / water rings)
    for _ in range(7):
        cx, cy, r = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(60, 220)
        d = np.sqrt((x - cx) ** 2 + (y - cy) ** 2) / r
        ring = np.exp(-((d - 1) / 0.04) ** 2) * 0.045 + np.clip(1 - d, 0, 1) * 0.025
        col *= (1 - ring[..., None] * np.array([0.7, 1.0, 1.4]))
    # fibres
    fib = np.zeros((H, W), np.float32)
    for _ in range(2500):
        fx, fy = rng.integers(0, W), rng.integers(0, H); L = rng.integers(8, 40); a = rng.uniform(0, math.pi)
        xs = np.clip((fx + np.cos(a) * np.arange(L)).astype(int), 0, W - 1)
        ys = np.clip((fy + np.sin(a) * np.arange(L)).astype(int), 0, H - 1)
        fib[ys, xs] += rng.uniform(-1, 1)
    col *= (1 + 0.035 * np.clip(fib, -1, 1)[..., None])
    # burnt / aged edges
    e = np.minimum(np.minimum(x, W - 1 - x), np.minimum(y, H - 1 - y))
    en = e + _fbm((H, W), seed + 2, 5, 6) * 16
    burn = np.clip(1 - en / 60, 0, 1) ** 1.8
    col = col * (1 - burn[..., None] * np.array([0.55, 0.68, 0.82]))
    char = np.clip(1 - en / 12, 0, 1)
    col = col * (1 - char[..., None] * 0.85)
    v = np.sqrt(((x - W / 2) / (W * 0.62)) ** 2 + ((y - H * 0.45) / (H * 0.62)) ** 2)
    col *= (1 - 0.28 * np.clip(v - 0.45, 0, 1)[..., None])
    return np.clip(col, 0, 255).astype(np.float32)

def glow_map():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((x - W * 0.22) / W) ** 2 + ((y - H * 0.18) / H) ** 2)
    return np.exp(-d * d * 4).astype(np.float32)

# ------------------------------------------------------------------ geometry
def smooth(pts, k=8):
    """Catmull-Rom through control points -> dense polyline."""
    P = np.asarray(pts, np.float32)
    if len(P) < 3: return np.linspace(P[0], P[-1], max(2, k)) if len(P) == 2 else P
    P = np.vstack([P[0], P, P[-1]]); out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for s in np.linspace(0, 1, k, endpoint=False):
            s2, s3 = s * s, s * s * s
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * s + (2 * p0 - 5 * p1 + 4 * p2 - p3) * s2 + (-p0 + 3 * p1 - 3 * p2 + p3) * s3))
    out.append(P[-2]); return np.array(out, np.float32)

def boil(P):
    if BOIL_AMP <= 0: return P
    b = BOIL[0]
    dx = np.sin(P[:, 1] * 0.031 + b * 1.37 + P[:, 0] * 0.007) * BOIL_AMP
    dy = np.sin(P[:, 0] * 0.027 + b * 2.11 + P[:, 1] * 0.005) * BOIL_AMP
    return P + np.stack([dx, dy], 1)

def _cut(P, p):
    if p >= 1: return P
    seg = np.sqrt(((P[1:] - P[:-1]) ** 2).sum(1)); cum = np.concatenate([[0], np.cumsum(seg)])
    L = cum[-1] * p
    if L <= 0: return None
    i = np.searchsorted(cum, L) - 1; i = max(0, min(i, len(seg) - 1))
    f = (L - cum[i]) / (seg[i] + 1e-6)
    return np.vstack([P[:i + 1], P[i] + (P[i + 1] - P[i]) * f])

class Ink:
    def __init__(self):
        self.surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        self.ctx = cairo.Context(self.surf)
    def clear(self):
        c = self.ctx; c.save(); c.set_operator(cairo.OPERATOR_CLEAR); c.paint(); c.restore()
        c.identity_matrix(); c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)

    def stroke(self, pts, w=5, p=1.0, col=INK, alpha=1.0, taper=True, dense=True, k=8):
        if p <= 0 or alpha <= 0.01: return
        P = smooth(pts, k) if dense else np.asarray(pts, np.float32)
        P = boil(P); P = _cut(P, p)
        if P is None or len(P) < 2: return
        c = self.ctx; c.set_source_rgba(*col, alpha)
        if not taper or len(P) < 4:
            c.set_line_width(w); c.move_to(*P[0])
            for q in P[1:]: c.line_to(*q)
            c.stroke(); return
        d = np.gradient(P, axis=0); n = np.stack([-d[:, 1], d[:, 0]], 1); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-6
        s = np.linspace(0, 1, len(P)); ww = w * 0.5 * (0.35 + 0.65 * np.sin(np.pi * np.clip(s, 0.02, 0.98)) ** 0.6)
        A = P + n * ww[:, None]; B = P - n * ww[:, None]
        c.move_to(*A[0])
        for q in A[1:]: c.line_to(*q)
        for q in B[::-1]: c.line_to(*q)
        c.close_path(); c.fill()

    def line(self, a, b, w=5, p=1.0, col=INK, alpha=1.0):
        self.stroke([a, b], w, p, col, alpha, taper=True, dense=True, k=12)

    def circle(self, cx, cy, r, w=5, p=1.0, col=INK, alpha=1.0, start=-90, n=40):
        a = np.radians(np.linspace(start, start + 360, n)); pts = np.stack([cx + np.cos(a) * r, cy + np.sin(a) * r], 1)
        self.stroke(pts, w, p, col, alpha, taper=False, dense=False)

    def fill(self, pts, col=SEPIA, alpha=0.35, dense=False):
        if alpha <= 0.01: return
        P = boil(smooth(pts, 6) if dense else np.asarray(pts, np.float32))
        c = self.ctx; c.set_source_rgba(*col, alpha); c.move_to(*P[0])
        for q in P[1:]: c.line_to(*q)
        c.close_path(); c.fill()

    def dot(self, x, y, r, col=INK, alpha=1.0):
        if alpha <= 0.01: return
        c = self.ctx; c.set_source_rgba(*col, alpha); c.arc(x, y, r, 0, 2 * math.pi); c.fill()

    def hatch(self, poly, p=1.0, ang=35, gap=11, w=2.2, col=INK, alpha=0.8, dense=False):
        """Engraving hatch clipped to polygon; lines appear sweeping across with p."""
        if p <= 0 or alpha <= 0.01: return
        P = boil(smooth(poly, 6) if dense else np.asarray(poly, np.float32))
        c = self.ctx; c.save(); c.move_to(*P[0])
        for q in P[1:]: c.line_to(*q)
        c.close_path(); c.clip()
        x0, y0 = P.min(0); x1, y1 = P.max(0); cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; R = math.hypot(x1 - x0, y1 - y0) / 2 + 4
        a = math.radians(ang); ux, uy = math.cos(a), math.sin(a); vx, vy = -uy, ux
        nl = int(2 * R / gap) + 1; shown = int(nl * clamp(p) + 0.999)
        c.set_source_rgba(*col, alpha); c.set_line_width(w)
        for i in range(shown):
            o = -R + i * gap
            c.move_to(cx + vx * o - ux * R, cy + vy * o - uy * R); c.line_to(cx + vx * o + ux * R, cy + vy * o + uy * R)
        c.stroke(); c.restore()

    def text(self, s, x, y, size, col=INK, alpha=1.0, family="Cinzel", bold=True, p=1.0, anchor="c"):
        if p <= 0 or alpha <= 0.01: return 0
        c = self.ctx; c.select_font_face(family, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
        c.set_font_size(size); ext = c.text_extents(s); full = ext.x_advance
        n = int(round(len(s) * clamp(p))); s2 = s[:n]
        x0 = x - full / 2 if anchor == "c" else x
        c.set_source_rgba(*col, alpha); c.move_to(x0, y + size * 0.35); c.show_text(s2)
        return full

    def array(self):
        """premultiplied BGRA -> (rgb_pm float, alpha float) in 0..1"""
        self.surf.flush()
        a = np.ndarray((H, W, 4), np.uint8, self.surf.get_data()).astype(np.float32) / 255
        return a[..., 2::-1], a[..., 3:4]

class Reveal:
    """Hands out sequential sub-progress so a drawing's strokes are drawn one after another."""
    def __init__(self, p, n): self.p, self.n, self.i = p, max(1, n), 0
    def __call__(self):
        v = clamp(self.p * self.n - self.i); self.i += 1; return v

def composite(paper, glow, ink, t, flick=True):
    rgb_pm, a = ink.array()
    out = paper * (1 - a + rgb_pm)          # multiply ink onto paper (premultiplied)
    if flick:
        f = 0.965 + 0.035 * math.sin(t * 11.3) * math.sin(t * 5.7 + 1)
        out = out * f + glow[..., None] * np.array([28, 16, 4], np.float32) * f
    return np.clip(out, 0, 255).astype(np.uint8)

# ------------------------------------------------------------------ captions (ink + red current word)
def caption(ink, group, t, y=H * 0.79, size=78):
    c = ink.ctx; c.select_font_face("DejaVu Serif", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    p = ease_out((t - group[0][1]) / 0.2); sz = size * (0.9 + 0.1 * p)
    c.set_font_size(sz); sp = c.text_extents(" ").x_advance
    ws = [w for w, _, _ in group]; wid = [c.text_extents(w).x_advance for w in ws]
    tot = sum(wid) + sp * (len(ws) - 1)
    if tot > W * 0.86:
        sz *= W * 0.86 / tot; c.set_font_size(sz); sp = c.text_extents(" ").x_advance
        wid = [c.text_extents(w).x_advance for w in ws]; tot = sum(wid) + sp * (len(ws) - 1)
    # soft parchment halo so text reads over drawings
    c.set_source_rgba(0.93, 0.86, 0.70, 0.55 * p)
    _rr(c, W / 2 - tot / 2 - 34, y - sz * 0.95, tot + 68, sz * 1.5, 26); c.fill()
    x = W / 2 - tot / 2
    for (w, s, e), wd in zip(group, wid):
        col = RED if s <= t < e + 0.05 else INK
        c.set_source_rgba(*col, p); c.move_to(x, y + sz * 0.1); c.show_text(w); x += wd + sp

def _rr(c, x, y, w, h, r):
    c.new_sub_path(); c.arc(x + w - r, y + r, r, -math.pi / 2, 0); c.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    c.arc(x + r, y + h - r, r, math.pi / 2, math.pi); c.arc(x + r, y + r, r, math.pi, 1.5 * math.pi); c.close_path()

def stamp(ink, s, lt, y=H * 0.085, size=54, alpha=1.0):
    """Typewritten Cinzel heading with a red rule under it."""
    p = clamp(lt / 1.0); full = ink.text(s, W / 2, y, size, INK, alpha, p=p)
    if p >= 1: ink.line((W / 2 - full / 2, y + size * 0.85), (W / 2 + full / 2, y + size * 0.85), 5, clamp((lt - 1) / 0.4), RED, alpha)

# ------------------------------------------------------------------ figures
def _seg(o, ang, L):  # angle in degrees, 0 = straight down, positive = toward +x
    r = math.radians(ang); return (o[0] + math.sin(r) * L, o[1] + math.cos(r) * L)

def dance_pose(t, ph=0.0, energy=1.0, speed=1.0):
    w = 2 * math.pi * 1.6 * speed; s = math.sin(w * t + ph); c = math.cos(w * t + ph)
    e = energy
    return dict(bob=abs(s) * 0.035 * e, lean=7 * math.sin(w * t / 2 + ph) * e,
                aL=(-150 + 25 * s) * e + (1 - e) * -12, eL=(-25 - 25 * c) * e,
                aR=(140 + 30 * c) * e + (1 - e) * 12, eR=(30 + 25 * s) * e,
                hL=(-14 * max(0, s) - 4) * e, kL=(25 * max(0, s)) * e,
                hR=(14 * max(0, -s) + 4) * e, kR=(-25 * max(0, -s)) * e,
                head=8 * math.sin(w * t + ph + 1) * e, sway=10 * s * e)

STAND = dict(bob=0, lean=0, aL=-10, eL=-5, aR=10, eR=5, hL=-4, kL=0, hR=4, kR=0, head=0, sway=0)

def figure(ink, x, y, h, pose=STAND, p=1.0, kind="woman", alpha=1.0, rot=0.0, col=INK, shoes=None, wash=True, flip=False):
    """Ink person. y = feet. rot (deg) rotates around the feet (for collapsing)."""
    if p <= 0 or alpha <= 0.01: return
    c = ink.ctx; c.save(); c.translate(x, y); c.rotate(math.radians(rot + pose.get("lean", 0)))
    if flip: c.scale(-1, 1)
    R = Reveal(p, 12); lw = max(2.5, h * 0.016)
    by = -h * pose.get("bob", 0)
    hip = (0, -h * 0.47 + by); neck = (0, -h * 0.80 + by); hr = h * 0.075
    head = (math.sin(math.radians(pose.get("head", 0))) * hr * 0.5, neck[1] - hr * 1.1)
    sh = (0, neck[1] + h * 0.035); L1, L2 = h * 0.15, h * 0.14; T1, T2 = h * 0.24, h * 0.23
    # legs
    legs = []
    for side, hk, kk in ((-1, "hL", "kL"), (1, "hR", "kR")):
        hp = (hip[0] + side * h * 0.035, hip[1]); a = pose[hk]; k = _seg(hp, a, T1); f = _seg(k, a + pose[kk], T2)
        legs.append((hp, k, f))
    if kind == "skeleton":
        ink.stroke([neck, hip], lw * 0.8, R(), col, alpha, k=3)
        for i in range(4):  # ribs
            yy = neck[1] + h * (0.06 + i * 0.045); wdt = h * (0.085 - i * 0.008)
            ink.stroke([(-wdt, yy + h * 0.02), (-wdt * 0.6, yy - h * 0.012), (0, yy), (wdt * 0.6, yy - h * 0.012), (wdt, yy + h * 0.02)], lw * 0.6, R(), col, alpha)
        ink.stroke([(-h * 0.06, hip[1] - h * 0.02), (0, hip[1] + h * 0.03), (h * 0.06, hip[1] - h * 0.02)], lw * 0.8, R(), col, alpha)
        for hp, k, f in legs:
            ink.stroke([hp, k, f], lw * 0.7, R(), col, alpha, k=3); ink.dot(*k, lw * 0.8, col, alpha * R())
    else:
        dress = kind == "woman"
        if dress:  # visible shins under the hem
            for hp, k, f in legs:
                mid = ((k[0] + f[0]) / 2, (k[1] + f[1]) / 2)
                ink.stroke([mid, f], lw, R(), col, alpha, k=3)
        else:
            for hp, k, f in legs: ink.stroke([hp, k, f], lw * 1.1, R(), col, alpha, k=3)
        for hp, k, f in legs:  # shoes
            sc = shoes or col
            ink.stroke([(f[0] - h * 0.01, f[1]), (f[0] + h * 0.045, f[1] + 1)], lw * 1.8, R() if not shoes else 1, sc, alpha)
    # torso / dress
    sw = pose.get("sway", 0)
    if kind == "woman":
        hem = h * 0.11
        poly = [(-h * 0.06, sh[1]), (h * 0.06, sh[1]), (h * 0.075, hip[1] - h * 0.02), (h * 0.20 + sw * 0.6, -hem + by * 0.3),
                (h * 0.05 + sw * 0.3, -hem + h * 0.012 + by * 0.3), (-h * 0.08 + sw * 0.3, -hem - h * 0.01 + by * 0.3), (-h * 0.20 + sw * 0.6, -hem + by * 0.3), (-h * 0.075, hip[1] - h * 0.02)]
        pr = R()
        if wash: ink.fill(poly, SEPIA, 0.30 * alpha * pr)
        ink.hatch(poly, pr, 40, max(6, h * 0.022), lw * 0.45, col, 0.55 * alpha)
        ink.stroke(poly + [poly[0]], lw, pr, col, alpha, taper=False, dense=False)
        ink.stroke([(-h * 0.075, hip[1] - h * 0.02), (h * 0.075, hip[1] - h * 0.02)], lw * 0.8, R(), col, alpha)  # waist
    elif kind == "man":
        poly = [(-h * 0.07, sh[1]), (h * 0.07, sh[1]), (h * 0.085, hip[1] + h * 0.07 + by * 0.2), (-h * 0.085, hip[1] + h * 0.07 + by * 0.2)]
        pr = R()
        if wash: ink.fill(poly, SEPIA, 0.28 * alpha * pr)
        ink.hatch(poly, pr, -35, max(6, h * 0.024), lw * 0.45, col, 0.5 * alpha)
        ink.stroke(poly + [poly[0]], lw, pr, col, alpha, taper=False, dense=False)
        ink.stroke([(-h * 0.08, hip[1]), (h * 0.08, hip[1])], lw * 1.2, R(), col, alpha)  # belt
    # arms
    for side, ak, ek in ((-1, "aL", "eL"), (1, "aR", "eR")):
        so = (sh[0] + side * h * 0.06, sh[1]); a = pose[ak]; e = _seg(so, a, L1); hnd = _seg(e, a + pose[ek], L2)
        ink.stroke([so, e, hnd], lw * (0.7 if kind == "skeleton" else 1.0), R(), col, alpha, k=3)
        ink.dot(*hnd, lw * (0.9 if kind == "skeleton" else 1.1), col, alpha * min(1, p * 2))
    # head
    pr = R()
    if kind == "skeleton":
        ink.circle(head[0], head[1], hr, lw, pr, col, alpha)
        ink.stroke([(head[0] - hr * 0.6, head[1] + hr * 0.7), (head[0], head[1] + hr * 1.25), (head[0] + hr * 0.6, head[1] + hr * 0.7)], lw * 0.8, pr, col, alpha)
        for sx in (-0.38, 0.38): ink.dot(head[0] + sx * hr, head[1] - hr * 0.05, hr * 0.27, col, alpha * pr)
        ink.dot(head[0], head[1] + hr * 0.38, hr * 0.1, col, alpha * pr)
    else:
        ink.circle(head[0], head[1], hr, lw, pr, col, alpha)
        for sx in (-0.33, 0.33): ink.dot(head[0] + sx * hr, head[1] - hr * 0.05, hr * 0.11, col, alpha * pr)
        ink.stroke([(head[0] - hr * 0.3, head[1] + hr * 0.45), (head[0] + hr * 0.3, head[1] + hr * 0.45)], lw * 0.6, pr, col, alpha)
        if kind == "woman":  # coif / headscarf
            ink.stroke([(head[0] - hr * 1.15, head[1] + hr * 0.5), (head[0] - hr * 1.05, head[1] - hr * 0.8), (head[0], head[1] - hr * 1.3),
                        (head[0] + hr * 1.05, head[1] - hr * 0.8), (head[0] + hr * 1.15, head[1] + hr * 0.5)], lw, R(), col, alpha)
        else:  # pointed hood
            ink.stroke([(head[0] - hr * 1.1, head[1] + hr * 0.4), (head[0] - hr * 0.9, head[1] - hr * 0.9), (head[0] + hr * 0.6, head[1] - hr * 2.0),
                        (head[0] + hr * 1.0, head[1] - hr * 0.7), (head[0] + hr * 1.1, head[1] + hr * 0.4)], lw, R(), col, alpha)
    c.restore()

# ------------------------------------------------------------------ scenery
def ground(ink, y, p, x0=60, x1=W - 60, alpha=1.0, cobbles=True):
    ink.stroke([(x0, y), ((x0 + x1) / 2, y + 4), (x1, y - 2)], 5, p, INK, alpha)
    if cobbles:
        rng = np.random.default_rng(int(y))
        for i in range(28):
            cx, cy = rng.uniform(x0 + 20, x1 - 20), y + rng.uniform(16, 90); r = rng.uniform(10, 22)
            ink.stroke([(cx - r, cy), (cx - r * 0.6, cy - r * 0.35), (cx + r * 0.6, cy - r * 0.35), (cx + r, cy)], 2.4, clamp(p * 1.5 - i / 40), INK, alpha * 0.7)

def house(ink, x, y, w, h, p, alpha=1.0, seed=0):
    """Half-timbered gabled house; (x,y) = bottom-left."""
    R = Reveal(p, 9); rh = w * 0.75
    body = [(x, y), (x, y - h), (x + w, y - h), (x + w, y)]
    roof = [(x - w * 0.06, y - h), (x + w / 2, y - h - rh), (x + w * 1.06, y - h)]
    pr = R(); ink.fill(roof + [(x + w * 1.06, y - h)], SEPIA, 0.45 * alpha * pr)
    ink.hatch(roof, pr, 70, 9, 1.8, INK, 0.6 * alpha)
    ink.stroke(body, 4, R(), INK, alpha, taper=False, dense=False)
    ink.stroke(roof, 4.5, R(), INK, alpha, taper=False, dense=False)
    ink.stroke([(x, y - h * 0.5), (x + w, y - h * 0.5)], 3, R(), INK, alpha)  # timber beam
    pr = R()
    for i in range(3):  # cross beams
        a = x + w * i / 3; b = x + w * (i + 1) / 3
        ink.stroke([(a, y - h * 0.5), (b, y - h)], 2.4, pr, INK, alpha * 0.85)
        ink.stroke([(b, y - h * 0.5), (a, y - h)], 2.4, pr, INK, alpha * 0.85)
    pr = R()
    ink.stroke([(x + w * 0.4, y), (x + w * 0.4, y - h * 0.32), (x + w * 0.6, y - h * 0.32), (x + w * 0.6, y)], 3, pr, INK, alpha, taper=False, dense=False)
    ink.fill([(x + w * 0.4, y), (x + w * 0.4, y - h * 0.32), (x + w * 0.6, y - h * 0.32), (x + w * 0.6, y)], INK, 0.35 * alpha * pr)
    pr = R()
    for wx in (0.12, 0.72):
        ink.stroke([(x + w * wx, y - h * 0.38), (x + w * wx, y - h * 0.18), (x + w * (wx + 0.16), y - h * 0.18), (x + w * (wx + 0.16), y - h * 0.38), (x + w * wx, y - h * 0.38)], 2.4, pr, INK, alpha, taper=False, dense=False)
    ink.stroke([(x + w * 0.42, y - h - rh * 0.45), (x + w * 0.58, y - h - rh * 0.45), (x + w * 0.58, y - h - rh * 0.2), (x + w * 0.42, y - h - rh * 0.2), (x + w * 0.42, y - h - rh * 0.45)], 2.4, R(), INK, alpha, taper=False, dense=False)

def cathedral(ink, x, y, s, p, alpha=1.0):
    """Gothic cathedral with one tall spire (x = centre of tower, y = ground)."""
    R = Reveal(p, 7)
    tw = 110 * s; th = 430 * s
    tower = [(x - tw / 2, y), (x - tw / 2, y - th), (x + tw / 2, y - th), (x + tw / 2, y)]
    pr = R(); ink.fill(tower, SEPIA, 0.25 * alpha * pr); ink.hatch(tower, pr, 90, 10, 1.6, INK, 0.45 * alpha)
    ink.stroke(tower, 4, pr, INK, alpha, taper=False, dense=False)
    sp = [(x - tw * 0.38, y - th), (x, y - th - 330 * s), (x + tw * 0.38, y - th)]
    pr = R(); ink.fill(sp, SEPIA, 0.4 * alpha * pr); ink.stroke(sp, 4, pr, INK, alpha, taper=False, dense=False)
    for i in range(1, 6):
        yy = y - th - 330 * s * i / 6; ww = tw * 0.38 * (1 - i / 6)
        ink.stroke([(x - ww, yy), (x + ww, yy)], 2, pr, INK, alpha * 0.7)
    pr = R(); ink.line((x, y - th - 330 * s), (x, y - th - 380 * s), 3, pr, INK, alpha)
    ink.line((x - 16 * s, y - th - 360 * s), (x + 16 * s, y - th - 360 * s), 3, pr, INK, alpha)
    nave = [(x + tw / 2, y), (x + tw / 2, y - 210 * s), (x + tw / 2 + 260 * s, y - 210 * s), (x + tw / 2 + 260 * s, y)]
    pr = R(); ink.fill(nave, SEPIA, 0.2 * alpha * pr); ink.stroke(nave, 4, pr, INK, alpha, taper=False, dense=False)
    pr = R()
    for i in range(4):  # lancet windows
        wx = x + tw / 2 + 40 * s + i * 58 * s
        ink.stroke([(wx, y - 50 * s), (wx, y - 140 * s), (wx + 14 * s, y - 165 * s), (wx + 28 * s, y - 140 * s), (wx + 28 * s, y - 50 * s)], 2.4, pr, INK, alpha)
    pr = R(); ink.circle(x, y - th * 0.62, 30 * s, 3, pr, INK, alpha)  # rose window
    for k in range(6):
        a = k * math.pi / 3; ink.line((x, y - th * 0.62), (x + math.cos(a) * 30 * s, y - th * 0.62 + math.sin(a) * 30 * s), 1.6, pr, INK, alpha)
    ink.stroke([(x - 22 * s, y), (x - 22 * s, y - 90 * s), (x, y - 120 * s), (x + 22 * s, y - 90 * s), (x + 22 * s, y)], 3, R(), INK, alpha)

def sun(ink, x, y, r, p, t, alpha=1.0, col=INK, face=True):
    R = Reveal(p, 3); pr = R()
    ink.fill([(x + math.cos(a) * r, y + math.sin(a) * r) for a in np.linspace(0, 2 * math.pi, 30)], (0.85, 0.55, 0.15), 0.35 * alpha * pr)
    ink.circle(x, y, r, 4, pr, col, alpha)
    pr = R()
    for i in range(12):
        a = i * math.pi / 6 + t * 0.2; r0 = r * 1.2; r1 = r * (1.75 if i % 2 else 1.5)
        pts = [(x + math.cos(a) * (r0 + (r1 - r0) * s) + math.cos(a + math.pi / 2) * math.sin(s * 9 + t * 4) * 5,
                y + math.sin(a) * (r0 + (r1 - r0) * s) + math.sin(a + math.pi / 2) * math.sin(s * 9 + t * 4) * 5) for s in np.linspace(0, 1, 6)]
        ink.stroke(pts, 3.2, pr, col, alpha)
    if face:
        pr = R()
        for sx in (-0.35, 0.35): ink.dot(x + sx * r, y - r * 0.15, r * 0.08, col, alpha * pr)
        ink.stroke([(x - r * 0.3, y + r * 0.35), (x, y + r * 0.42), (x + r * 0.3, y + r * 0.35)], 3, pr, col, alpha)

def moon(ink, x, y, r, p, alpha=1.0):
    a1 = np.radians(np.linspace(-110, 110, 24)); a2 = np.radians(np.linspace(80, -80, 24))
    pts = list(zip(x + np.cos(a1) * r, y + np.sin(a1) * r)) + list(zip(x + r * 0.35 + np.cos(a2) * r * 0.8, y + np.sin(a2) * r * 0.95))
    ink.fill(pts, SEPIA, 0.35 * alpha * p); ink.stroke(pts, 3.5, p, INK, alpha, taper=False, dense=False)

def note(ink, x, y, s, p, alpha=1.0, col=INK):
    ink.dot(x, y, 9 * s, col, alpha * p); ink.line((x + 8 * s, y), (x + 8 * s, y - 42 * s), 3 * s, p, col, alpha)
    ink.stroke([(x + 8 * s, y - 42 * s), (x + 22 * s, y - 32 * s), (x + 24 * s, y - 20 * s)], 3 * s, p, col, alpha)

def tally(ink, x, y, n, p, size=70, col=INK, alpha=1.0):
    """n tally marks (groups of five with a strike)."""
    k = 0
    for i in range(n):
        g, j = divmod(i, 5); pr = clamp(p * n - i)
        if j < 4:
            xx = x + g * size * 1.25 + j * size * 0.22
            ink.stroke([(xx, y - size / 2), (xx + 3, y + size / 2)], 6, pr, col, alpha)
        else:
            xx = x + g * size * 1.25
            ink.stroke([(xx - 12, y + size * 0.3), (xx + size * 0.8, y - size * 0.3)], 6, pr, col, alpha)

def mountain(ink, x0, x1, y, peaks, p, alpha=1.0):
    pts = [(x0, y)] + peaks + [(x1, y)]
    pr = clamp(p * 1.4); ink.fill(pts, SEPIA, 0.22 * alpha * pr)
    ink.hatch(pts, pr, 60, 13, 1.6, INK, 0.4 * alpha); ink.stroke(pts, 4.5, p, INK, alpha, taper=False, dense=False)

def chapel(ink, x, y, s, p, alpha=1.0):
    R = Reveal(p, 4); w, h = 120 * s, 90 * s
    body = [(x - w / 2, y), (x - w / 2, y - h), (x + w / 2, y - h), (x + w / 2, y)]
    roof = [(x - w * 0.6, y - h), (x, y - h - 70 * s), (x + w * 0.6, y - h)]
    pr = R(); ink.fill(body, SEPIA, 0.3 * alpha * pr); ink.stroke(body, 3.5, pr, INK, alpha, taper=False, dense=False)
    pr = R(); ink.fill(roof, SEPIA, 0.5 * alpha * pr); ink.stroke(roof, 3.5, pr, INK, alpha, taper=False, dense=False)
    pr = R(); ink.line((x, y - h - 70 * s), (x, y - h - 130 * s), 4, pr, INK, alpha); ink.line((x - 20 * s, y - h - 108 * s), (x + 20 * s, y - h - 108 * s), 4, pr, INK, alpha)
    ink.stroke([(x - 14 * s, y), (x - 14 * s, y - 40 * s), (x, y - 52 * s), (x + 14 * s, y - 40 * s), (x + 14 * s, y)], 3, R(), INK, alpha)

def shoe(ink, x, y, s, p, alpha=1.0):
    """Medieval pointed shoe in red ink with a holy cross."""
    pts = [(x - 90 * s, y), (x - 95 * s, y - 50 * s), (x - 55 * s, y - 70 * s), (x - 10 * s, y - 45 * s), (x + 60 * s, y - 25 * s), (x + 120 * s, y - 8 * s), (x + 60 * s, y + 6 * s)]
    R = Reveal(p, 3); pr = R()
    ink.fill(pts, RED, 0.45 * alpha * pr); ink.stroke(pts + [pts[0]], 4, pr, INK, alpha, taper=False)
    pr = R(); ink.line((x - 55 * s, y - 52 * s), (x - 55 * s, y - 12 * s), 5, pr, (0.95, 0.85, 0.6), alpha)
    ink.line((x - 72 * s, y - 36 * s), (x - 38 * s, y - 36 * s), 5, pr, (0.95, 0.85, 0.6), alpha)

def wheat(ink, x, y, s, p, alpha=1.0, droop=0.0):
    R = Reveal(p, 3)
    for i, dx in enumerate((-22, 0, 22)):
        pr = R(); top = (x + dx * s + droop * 60 * s * (1 if dx >= 0 else -1), y - 230 * s + droop * 70 * s)
        ink.stroke([(x, y), (x + dx * s * 0.4, y - 110 * s), top], 3, pr, INK, alpha)
        for k in range(5):
            f = 0.55 + k * 0.09; gx = x + (top[0] - x) * f; gy = y + (top[1] - y) * f
            ink.stroke([(gx, gy), (gx - 14 * s, gy - 18 * s)], 3, pr, INK, alpha); ink.stroke([(gx, gy), (gx + 14 * s, gy - 18 * s)], 3, pr, INK, alpha)

def skull(ink, x, y, r, p, alpha=1.0, col=INK):
    R = Reveal(p, 3); pr = R()
    ink.circle(x, y, r, 4, pr, col, alpha)
    ink.stroke([(x - r * 0.6, y + r * 0.7), (x - r * 0.5, y + r * 1.25), (x + r * 0.5, y + r * 1.25), (x + r * 0.6, y + r * 0.7)], 4, R(), col, alpha)
    pr = R()
    for sx in (-0.38, 0.38): ink.dot(x + sx * r, y - r * 0.05, r * 0.25, col, alpha * pr)
    ink.dot(x, y + r * 0.4, r * 0.1, col, alpha * pr)
    for k in range(-2, 3): ink.line((x + k * r * 0.18, y + r * 0.95), (x + k * r * 0.18, y + r * 1.22), 2, pr, col, alpha)

def eye(ink, x, y, s, p, alpha=1.0, t=0.0):
    R = Reveal(p, 3)
    up = [(x - 110 * s, y), (x, y - 60 * s), (x + 110 * s, y)]; dn = [(x - 110 * s, y), (x, y + 60 * s), (x + 110 * s, y)]
    ink.stroke(up, 4, R(), INK, alpha); ink.stroke(dn, 4, R(), INK, alpha)
    pr = R(); jx = math.sin(t * 23) * 6 * s
    ink.circle(x + jx, y, 34 * s, 3.5, pr, INK, alpha); ink.dot(x + jx, y, 15 * s, INK, alpha * pr)

def drip(ink, x, y, L, p, alpha=1.0):
    q = clamp(p); yy = y + L * ease_out(q)
    ink.stroke([(x, y), (x, yy)], 7, 1, RED, alpha * (q > 0)); ink.dot(x, yy, 7 + 4 * q, RED, alpha * (q > 0))

# ------------------------------------------------------------------ audio (24 kHz)
SR = 24000
def _env(n, a, r):
    t = np.arange(n) / SR; return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / max(r, 1e-4))

def quill(dur, seed=0):
    rng = np.random.default_rng(seed); n = int(dur * SR); nz = rng.standard_normal(n).astype(np.float32)
    hp = np.diff(nz, prepend=0)                                  # brighter scratch
    am = np.abs(np.sin(np.cumsum(rng.uniform(15, 40, n) / SR) * 2 * np.pi)) ** 3
    fade = np.minimum(1, np.minimum(np.arange(n), n - np.arange(n)) / (0.05 * SR))
    return (hp * am * fade * 0.25).astype(np.float32)

def page_whoosh(seed=1):
    rng = np.random.default_rng(seed); n = int(0.6 * SR); nz = rng.standard_normal(n)
    k = 30; nz = np.convolve(nz, np.ones(k) / k, "same"); t = np.arange(n) / n
    return (nz * np.sin(np.pi * t) ** 2 * 1.2).astype(np.float32)

def thud(f=48, dur=1.4):
    n = int(dur * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * t * (1 - 0.3 * t)) * np.exp(-t * 3) * 0.9).astype(np.float32)

def bell(f=196, dur=4.0):
    n = int(dur * SR); t = np.arange(n) / SR; out = np.zeros(n)
    for m, a, d in ((0.5, 0.5, 1.2), (1, 1, 0.8), (1.19, 0.6, 0.6), (1.5, 0.4, 0.5), (2.0, 0.35, 0.4), (2.74, 0.2, 0.25)):
        out += a * np.sin(2 * np.pi * f * m * t) * np.exp(-t / (d * dur * 0.4))
    return (out * np.minimum(1, t / 0.005) * 0.35).astype(np.float32)

def drone(n, seed=7):
    t = np.arange(n) / SR; rng = np.random.default_rng(seed)
    out = (np.sin(2 * np.pi * 55 * t) + np.sin(2 * np.pi * 55.3 * t) + 0.5 * np.sin(2 * np.pi * 82.4 * t) + 0.25 * np.sin(2 * np.pi * 110.2 * t)) * 0.12
    nz = rng.standard_normal(n); k = int(SR * 0.01); wind = np.convolve(nz, np.ones(k) / k, "same")
    out += wind * (0.6 + 0.4 * np.sin(2 * np.pi * 0.09 * t)) * 0.45
    return out.astype(np.float32)

def jig(n, detune_curve=None, bpm=138):
    """Eerie medieval dance tune: hurdy-gurdy-like melody in D dorian over a buzzing drone + tabor."""
    t = np.arange(n) / SR; out = np.zeros(n, np.float32)
    D = 146.83; sc = [0, 2, 3, 5, 7, 9, 10, 12, 14]
    mel = [0, 2, 4, 2, 0, 2, 4, 5, 4, 2, 4, 2, 1, 0, 1, 2, 4, 5, 7, 5, 4, 2, 1, 2, 0, 2, 4, 2, 1, 0, -1, 0]
    beat = 60 / bpm / 2; dt = detune_curve if detune_curve is not None else np.zeros(n)
    def tone(f0, i0, m):
        tt = np.arange(m) / SR; vib = 1 + 0.004 * np.sin(2 * np.pi * 5.5 * tt)
        ph = 2 * np.pi * np.cumsum(f0 * vib * (1 + dt[i0:i0 + m])) / SR
        w = sum(np.sin(k * ph) / k ** 1.2 for k in range(1, 7))
        return w * np.minimum(1, tt / 0.015) * np.minimum(1, (m / SR - tt) / 0.03)
    step = int(beat * SR); i = 0
    for j, s0 in enumerate(range(0, n, step)):
        m = min(step, n - s0); deg = mel[j % len(mel)]
        semi = sc[deg] if deg >= 0 else -2
        out[s0:s0 + m] += tone(D * 2 ** (semi / 12), s0, m) * 0.16
        if j % 2 == 0:  # tabor
            mm = min(int(0.18 * SR), n - s0); tt = np.arange(mm) / SR
            out[s0:s0 + mm] += (np.sin(2 * np.pi * 90 * tt) * np.exp(-tt * 22) * (0.5 if j % 4 == 0 else 0.3)).astype(np.float32)
    ph = 2 * np.pi * np.cumsum(73.4 * (1 + dt)) / SR; ph2 = 2 * np.pi * np.cumsum(110 * (1 + dt * 1.3)) / SR
    out += (np.tanh(np.sin(ph) * 2.5) * 0.05 + np.tanh(np.sin(ph2) * 2.5) * 0.035).astype(np.float32)
    return out

def place(buf, clip, t, gain=1.0):
    s0 = int(t * SR)
    if s0 >= len(buf) or s0 + len(clip) <= 0: return
    a = max(0, -s0); s0 = max(0, s0); m = min(len(clip) - a, len(buf) - s0)
    buf[s0:s0 + m] += clip[a:a + m] * gain
