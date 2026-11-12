"""Story scene kits: reusable animated mini-scenes that ACT OUT the narration.

A script scene uses one with  "scene": "<kit name>", "p": {params}.
Numeric params can be a constant (0.5) or a ramp [from, to] (eased over the scene,
or over "<param>_t": [start_frac, end_frac] of the scene).
Kits draw on a 2x supersampled RGBA layer (smooth edges) and may return extra emoji to draw on top.
"""
import functools, math
import numpy as np
from PIL import Image, ImageDraw

W, H, Z = 1080, 1920, 2

def _ease(p): p = max(0.0, min(1.0, p)); return p * p * (3 - 2 * p)
def lerp(a, b, k): return a + (b - a) * k
def mix(c1, c2, k): return tuple(int(lerp(a, b, k)) for a, b in zip(c1, c2))

class Params:
    def __init__(self, p, lt, sd): self.p, self.lt, self.sd = p or {}, lt, sd
    def __call__(self, name, default=0.0):
        v = self.p.get(name, default)
        if isinstance(v, list) and len(v) == 2 and all(isinstance(x, (int, float)) for x in v):
            a, b = self.p.get(name + "_t", [0.0, 0.85])
            k = _ease((self.lt / max(self.sd, 0.01) - a) / max(b - a, 0.01))
            return lerp(v[0], v[1], k)
        return v

def z(*xs): return [x * Z for x in xs]

def vgrad(d, x0, y0, x1, y1, ctop, cbot, bands=96):
    for i in range(bands):
        ya, yb = lerp(y0, y1, i / bands), lerp(y0, y1, (i + 1) / bands) + 1
        d.rectangle(z(x0, ya, x1, yb), fill=mix(ctop, cbot, i / (bands - 1)))

@functools.lru_cache(maxsize=32)
def glow_sprite(r, color, strength=160):
    s = int(r * 2 * Z); y, x = np.mgrid[0:s, 0:s].astype(np.float32); c = s / 2
    a = np.clip(1 - np.sqrt((x - c) ** 2 + (y - c) ** 2) / c, 0, 1) ** 2 * strength
    rgb = np.empty((s, s, 3), np.float32); rgb[:] = color
    return Image.fromarray(np.dstack([rgb, a]).astype(np.uint8), "RGBA")

def glow(layer, x, y, r, color, strength=160):
    g = glow_sprite(int(r), tuple(color), strength); layer.alpha_composite(g, (int(x * Z - g.width / 2), int(y * Z - g.height / 2)))

def disc(d, x, y, r, fill, outline=None, w=0):
    d.ellipse(z(x - r, y - r, x + r, y + r), fill=fill, outline=outline, width=w * Z)

def moon_disc(layer, d, x, y, r, a=1.0):
    if a <= 0.01: return
    glow(layer, x, y, r * 3.2, (200, 210, 255), int(110 * a))
    c = mix((10, 12, 30), (232, 232, 222), a)
    disc(d, x, y, r, c)
    for ox, oy, rr in ((-0.3, -0.2, 0.22), (0.25, 0.15, 0.17), (-0.05, 0.4, 0.12), (0.35, -0.35, 0.1)):
        disc(d, x + ox * r, y + oy * r, rr * r, mix((10, 12, 30), (200, 200, 190), a))

def stars(d, t, alpha, seed=3, n=160, ymax=0.6):
    if alpha <= 0.02: return
    rng = np.random.default_rng(seed)
    for i in range(n):
        x, y, s = rng.uniform(0, W), rng.uniform(0, H * ymax), rng.uniform(1.5, 4)
        tw = 0.6 + 0.4 * math.sin(t * 3 + i)
        v = int(255 * alpha * tw); disc(d, x, y, s, (v, v, min(255, v + 10)))

def planet_sprite(kind, r):
    from render import planet_img
    return planet_img(kind, r)

def paste_sprite(layer, im, x, y, scale=Z):
    im = im.resize((int(im.width * scale), int(im.height * scale)), Image.BILINEAR) if scale != 1 else im
    layer.alpha_composite(im, (int(x * Z - im.width / 2), int(y * Z - im.height / 2)))

# ------------------------------------------------------------------ kits
def k_orbit(layer, d, P, t):
    """Earth with ocean tidal bulge pointing at an orbiting Moon. p: moon (0-1 visibility), bulge (0-1), speed."""
    ex, ey, er = W / 2, H * 0.38, 170
    moon, bulge = P("moon", 1.0), P("bulge", 1.0)
    ang = t * P("speed", 0.9) + 0.6
    d.ellipse(z(ex - 340, ey - 340, ex + 340, ey + 340), outline=(90, 100, 160), width=2 * Z)
    k = 0.04 + 0.13 * bulge; pts = []
    for i in range(72):
        a = 2 * math.pi * i / 72; rr = er * (1.02 + k * math.cos(a) ** 2)
        pts.append(((ex + rr * math.cos(a + ang)) * Z, (ey + rr * math.sin(a + ang)) * Z))
    d.polygon(pts, fill=(90, 170, 255), outline=(190, 225, 255), width=3 * Z)
    paste_sprite(layer, planet_sprite("earth", er), ex, ey, 1.0 * Z)
    mx, my = ex + 340 * math.cos(ang), ey + 340 * math.sin(ang)
    moon_disc(layer, d, mx, my, 55, moon)
    return []

def k_night(layer, d, P, t):
    """Moonlit countryside; p: moon 1->0 darkens everything."""
    m = P("moon", 1.0)
    vgrad(d, 0, 0, W, H, mix((2, 3, 10), (24, 40, 96), m), mix((6, 8, 18), (70, 90, 150), m))
    stars(d, t, 1.0 - 0.5 * m)
    moon_disc(layer, d, W * 0.68, H * 0.17, 90 * (0.6 + 0.4 * m), m)
    for base, amp, col in ((0.50, 60, (40, 60, 70)), (0.56, 45, (25, 40, 45))):
        c = mix((6, 8, 10), col, m)
        pts = [(x * Z, (H * base - amp * math.sin(x / W * 5 + base * 9)) * Z) for x in range(0, W + 40, 40)]
        d.polygon(pts + [(W * Z, H * Z), (0, H * Z)], fill=c)
    hx, hy = W * 0.28, H * 0.50; hc = mix((10, 10, 12), (90, 70, 60), m)
    d.rectangle(z(hx - 70, hy - 90, hx + 70, hy), fill=hc)
    d.polygon(z(hx - 90, hy - 90, hx, hy - 160, hx + 90, hy - 90), fill=mix((8, 8, 8), (120, 50, 40), m))
    d.rectangle(z(hx - 22, hy - 62, hx + 22, hy - 22), fill=(255, 210, 90))
    return []

def k_beach(layer, d, P, t):
    """Side view of a shore. Tide rises/falls with the Moon crossing the sky. p: amp (1 = normal tides), moon, gauge."""
    amp, moon = P("amp", 1.0), P("moon", 1.0)
    vgrad(d, 0, 0, W, H, (16, 22, 60), (90, 70, 130))
    stars(d, t, 0.6, n=90, ymax=0.4)
    ph = t * P("speed", 1.5)
    mx, my = W * (0.5 + 0.42 * math.cos(ph)), H * (0.22 - 0.08 * math.sin(ph))
    moon_disc(layer, d, mx, my, 60, moon)
    tide = amp * (0.5 + 0.5 * math.sin(ph)) + (1 - amp) * 0.5  # 0 low .. 1 high
    sand = lambda x: H * 0.72 - H * 0.36 * (x / W)
    yw = lerp(H * 0.64, H * 0.43, tide)
    # wet-sand band shows how far normal tides reach
    d.polygon([(x * Z, (sand(x) - 6) * Z) for x in range(0, W + 1, 30)] + [(W * Z, H * Z), (0, H * Z)], fill=(150, 120, 80))
    wave = [(x * Z, (yw + 10 * math.sin(x / 70 + t * 4)) * Z) for x in range(0, W + 30, 30)]
    d.polygon(wave + [(W * Z, H * Z), (0, H * Z)], fill=(40, 110, 200))
    d.line(wave, fill=(200, 230, 255), width=6 * Z)
    dry = [(x * Z, max(sand(x), H * 0.44 if x > W * 0.3 else 0) * Z) for x in range(0, W + 1, 30)]
    d.polygon([(x * Z, sand(x) * Z) for x in range(0, W + 1, 30)] + [(W * Z, H * Z), (0, H * Z)], fill=(225, 190, 130))
    # show the water over the sand where tide is above the beach line (redraw water in front)
    front = []
    for x in range(0, W + 30, 30):
        yy = yw + 10 * math.sin(x / 70 + t * 4)
        front.append((x, min(yy, sand(x))))
    d.polygon([(x * Z, y * Z) for x, y in front] + [(x * Z, sand(x) * Z) for x, _ in reversed(front)], fill=(40, 110, 200))
    d.line([(x * Z, y * Z) for x, y in front if y < sand(x) - 2], fill=(200, 230, 255), width=6 * Z) if any(y < sand(x) - 2 for x, y in front) else None
    if P("gauge", 1):  # tide range meter
        gx, gy, gh = W * 0.86, H * 0.08, H * 0.22
        d.rounded_rectangle(z(gx - 34, gy, gx + 34, gy + gh), 20 * Z, fill=(20, 20, 30), outline=(240, 240, 240), width=4 * Z)
        fh = gh * amp
        d.rounded_rectangle(z(gx - 24, gy + gh - fh + 10, gx + 24, gy + gh - 10), 14 * Z, fill=mix((255, 80, 80), (90, 200, 255), amp))
    return [{"emoji": "🌴", "x": W * 0.80, "y": H * 0.36, "s": 230}] + (
        [{"text": f"TIDES {int(amp * 100)}%", "x": W * 0.86, "y": H * 0.32, "size": 50}] if P("gauge", 1) else [])

def k_tidepool(layer, d, P, t):
    """Rock pool drying under the sun. p: water 1->0, heat 0->1."""
    water, heat = P("water", 1.0), P("heat", 0.0)
    vgrad(d, 0, 0, W, H, mix((120, 190, 255), (255, 170, 90), heat), mix((200, 230, 255), (255, 220, 160), heat))
    sx, sy = W * 0.78, H * 0.14
    glow(layer, sx, sy, 220, (255, 220, 120), 200)
    for i in range(12):
        a = i * math.pi / 6 + t * 0.6
        d.line(z(sx + 110 * math.cos(a), sy + 110 * math.sin(a), sx + (150 + 20 * heat) * math.cos(a), sy + (150 + 20 * heat) * math.sin(a)), fill=(255, 200, 60), width=10 * Z)
    disc(d, sx, sy, 90, (255, 210, 70))
    d.rectangle(z(0, H * 0.40, W, H), fill=(110, 105, 100))
    for i, (x, y, r) in enumerate(((120, 0.40, 160), (950, 0.41, 190), (540, 0.66, 260), (300, 0.70, 140), (820, 0.70, 170))):
        d.ellipse(z(x - r, H * y - r * 0.55, x + r, H * y + r * 0.55), fill=(135 - i * 6, 128 - i * 6, 120 - i * 6))
    px, py = W * 0.5, H * 0.48
    d.ellipse(z(px - 330, py - 110, px + 330, py + 110), fill=(150, 130, 100))
    if water > 0.02:
        rw, rh = 320 * math.sqrt(water), 100 * math.sqrt(water)
        d.ellipse(z(px - rw, py - rh, px + rw, py + rh), fill=(60, 140, 210))
        d.arc(z(px - rw * 0.7, py - rh * 0.6, px + rw * 0.2, py + rh * 0.2), 200, 300, fill=(200, 235, 255), width=6 * Z)
    out = [{"emoji": "🦀", "x": px - 160 + 30 * math.sin(t * 3), "y": py - 70 - abs(math.sin(t * 6)) * 14, "s": 170}]
    if water < 0.55: out.append({"emoji": "💦", "x": px - 70, "y": py - 170 - 10 * math.sin(t * 5), "s": 80})
    out.append({"emoji": "🐚", "x": px + 200, "y": py + 10, "s": 100})
    return out

def k_coral(layer, d, P, t):
    """Underwater reef under a full moon; p: moon 1->0, spawn 0..1 particles."""
    moon, spawn = P("moon", 1.0), P("spawn", 1.0)
    vgrad(d, 0, 0, W, H, (20, 60, 120), (4, 16, 40))
    moon_disc(layer, d, W * 0.5 + 8 * math.sin(t * 2), H * 0.11, 70, moon * 0.85)
    for i in range(5):
        x = W * (0.15 + 0.18 * i) + 30 * math.sin(t * 0.5 + i)
        d.polygon(z(x - 30, 0, x + 30, 0, x + 140, H * 0.6, x + 60, H * 0.6), fill=(40, 90, 150))
    d.rectangle(z(0, H * 0.56, W, H), fill=(194, 170, 120))
    rng = np.random.default_rng(5)
    for i in range(70 if spawn > 0.05 else 0):
        x0, sp, ph = rng.uniform(0.1, 0.9) * W, rng.uniform(40, 110), rng.uniform(0, 10)
        y = H * 0.52 - ((t * sp + ph * 80) % (H * 0.45))
        if rng.uniform() < spawn: disc(d, x0 + 12 * math.sin(t * 2 + ph), y, 6, (255, 190, 210))
    for i in range(12):
        x, sp = (i * 97) % W, 60 + (i * 37) % 80
        disc(d, x, H * 0.55 - ((t * sp + i * 160) % (H * 0.5)), 5 + i % 4, None, (180, 220, 255), 2)
    return [{"emoji": "🪸", "x": W * x, "y": H * 0.53, "s": s} for x, s in ((0.18, 240), (0.5, 300), (0.82, 240))] + \
           [{"emoji": "🐠", "x": (t * 120) % (W + 200) - 100, "y": H * 0.32, "s": 110}]

@functools.lru_cache(maxsize=4)
def earth_with_caps(r, ice):
    im = planet_sprite("earth", r).copy(); d = ImageDraw.Draw(im); c = im.width / 2
    h = r * (0.18 + 0.5 * ice)
    for top in (True, False):
        y0 = c - r if top else c + r - h
        msk = Image.new("L", im.size, 0); ImageDraw.Draw(msk).ellipse((c - r, c - r, c + r, c + r), fill=255)
        cap = Image.new("L", im.size, 0); ImageDraw.Draw(cap).rectangle((0, y0, im.width, y0 + h), fill=235)
        from PIL import ImageChops
        im.paste((240, 248, 255), (0, 0), ImageChops.multiply(msk, cap))
    return im

def k_tilt(layer, d, P, t):
    """Earth's axis tilt; p: wobble amplitude in degrees (0 -> 30), ice 0..1."""
    wob = P("wobble", 0.0); ex, ey, r = W / 2, H * 0.38, 210
    tilt = 23.4 + wob * math.sin(t * 2.4)
    d.line(z(ex, ey - 330, ex, ey + 330), fill=(120, 120, 160), width=3 * Z)
    a = math.radians(tilt)
    im = earth_with_caps(r, round(P("ice", 0.0), 1)).rotate(-tilt, resample=Image.BICUBIC, expand=True)
    paste_sprite(layer, im, ex, ey)
    dx, dy = math.sin(a) * 300, -math.cos(a) * 300
    d.line(z(ex - dx, ey - dy, ex + dx, ey + dy), fill=(255, 90, 90), width=7 * Z)
    return [{"text": f"TILT {tilt:4.1f}°", "x": ex, "y": ey + 290, "size": 70, "color": "#ffd600"}]

def k_chaos(layer, d, P, t):
    """Frozen half / burning half Earth with a swinging thermometer."""
    d.rectangle(z(0, 0, W / 2, H), fill=(150, 200, 240)); d.rectangle(z(W / 2, 0, W, H), fill=(200, 60, 30))
    ex, ey, r = W / 2, H * 0.36, 230
    paste_sprite(layer, planet_sprite("earth", r), ex, ey)
    tint = Image.new("RGBA", (W * Z, H * Z), (0, 0, 0, 0)); td = ImageDraw.Draw(tint)
    td.pieslice(z(ex - r, ey - r, ex + r, ey + r), 90, 270, fill=(235, 245, 255, 170))
    td.pieslice(z(ex - r, ey - r, ex + r, ey + r), 270, 450, fill=(255, 80, 20, 120))
    layer.alpha_composite(tint)
    k = 0.5 + 0.5 * math.sin(t * 2.5)
    tx, ty = W * 0.86, H * 0.10
    d.rounded_rectangle(z(tx - 40, ty - 10, tx + 40, ty + 160), 40 * Z, fill=(240, 240, 240), outline=(30, 30, 30), width=5 * Z)
    d.rounded_rectangle(z(tx - 24, ty + 150 - 140 * k, tx + 24, ty + 150), 24 * Z, fill=mix((60, 140, 255), (255, 40, 30), k))
    out = []
    for i in range(7):
        out.append({"emoji": "❄️", "x": 80 + (i * 67) % 420, "y": (t * (90 + i * 13) + i * 300) % H, "s": 70})
    for i in range(4):
        out.append({"emoji": "🔥", "x": W * 0.6 + i * 110, "y": H * 0.80 - abs(math.sin(t * 7 + i)) * 20, "s": 130})
    return out

KITS = {"orbit": k_orbit, "night": k_night, "beach": k_beach, "tidepool": k_tidepool,
        "coral": k_coral, "tilt": k_tilt, "chaos": k_chaos}

def draw_scene(frame, scene, lt, sd, t):
    """Render a kit onto `frame` (1x RGB). Returns overlay emoji/text dicts in absolute pixels."""
    if scene["scene"] not in KITS:
        import mograph  # noqa: registers mg_* kits
    kit = KITS[scene["scene"]]
    layer = Image.new("RGBA", (W * Z, H * Z), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    extra = kit(layer, d, Params(scene.get("p"), lt, sd), t) or []
    layer = layer.reduce(Z); frame.paste(layer, (0, 0), layer)
    return extra
