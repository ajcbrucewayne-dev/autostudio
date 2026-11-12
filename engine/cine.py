"""Cinematic painterly story renderer (Option 1 style).

python engine/cine.py scripts/cine/moon.json out.mp4
Environments: forest, beach, tidepool, space, chaos.  Shot params:
  {"env": "forest", "say": "...", "moon": 1 or [1,0], "tide": 1 or [1,0.33], "water": [1,0.1], "wobble": [0,30],
   "leo": {"x": 0.4, "y": 0.70, "h": 540, "look_up": 1, "wide": 0, "down": 0, "lantern": true, "float": false, "facing": 1},
   "zoom": [1.0, 1.1], "pan": [-0.3, 0.3]}
Uses the original narrator voice + background music.
"""
import functools, json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render
from render import W, H, FPS, SR
from painterly import (PW, PH, grad, radial, trunk_layer, foliage_layer, hill_layer, fog_band, draw_leo)

def ramp(v, k):
    if isinstance(v, list): e = k * k * (3 - 2 * k); return v[0] + (v[1] - v[0]) * e
    return v

def stars_layer(n, seed, ymax=0.6, bright=(70, 230)):
    r = np.random.default_rng(seed); im = Image.new("RGBA", (PW, PH), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for _ in range(n):
        x, y, b = r.uniform(0, PW), r.uniform(0, PH * ymax), int(r.uniform(*bright)); s = r.choice([1, 1, 1.5, 2.5])
        d.ellipse((x - s, y - s, x + s, y + s), fill=(b, b, min(255, b + 25), 255))
    return im

@functools.lru_cache(maxsize=4)
def moon_layer(mx, my, scale=1.0):
    im = Image.new("RGBA", (PW, PH), (0, 0, 0, 0))
    for size, col, p, a in ((1300, (120, 190, 200), 2.2, 120), (600, (200, 230, 220), 2.0, 160), (330, (240, 250, 235), 1.2, 255)):
        size = int(size * scale); g = radial(size, col, p, a); im.alpha_composite(g, (int(mx - size / 2), int(my - size / 2)))
    m = Image.new("RGBA", (300, 300), (0, 0, 0, 0)); md = ImageDraw.Draw(m)
    md.ellipse((40, 40, 260, 260), fill=(250, 248, 232, 255))
    for ox, oy, r in ((110, 120, 26), (175, 165, 18), (140, 205, 14), (190, 100, 12)):
        md.ellipse((ox - r, oy - r, ox + r, oy + r), fill=(226, 224, 205, 255))
    m = m.filter(ImageFilter.GaussianBlur(1.2))
    if scale != 1: m = m.resize((int(300 * scale), int(300 * scale)), Image.LANCZOS)
    im.alpha_composite(m, (int(mx - m.width / 2), int(my - m.height / 2)))
    rays = Image.new("L", (PW, PH), 0); rd = ImageDraw.Draw(rays)
    for i in range(6):
        a = math.radians(105 + i * 9); L = PH * 1.2
        rd.polygon([(mx, my), (mx + math.cos(a - 0.03) * L, my + math.sin(a - 0.03) * L), (mx + math.cos(a + 0.03) * L, my + math.sin(a + 0.03) * L)], fill=34)
    rays = Image.merge("RGBA", (*[Image.new("L", (PW, PH), 230)] * 3, rays.filter(ImageFilter.GaussianBlur(30))))
    im.alpha_composite(rays)
    return im

def fade(im, a):
    if a >= 0.999: return im
    im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * max(0, a)))); return im

def offset(im, dx): return ImageChops.offset(im, int(dx), 0) if int(dx) else im

# ------------------------------------------------------------------ environments: static plates (cached) + dynamic draw
@functools.lru_cache(maxsize=1)
def forest_plates():
    return [("sky", Image.fromarray(grad(PH, PW, (10, 30, 48), (22, 62, 74)), "RGB").convert("RGBA"), 0.05),
            ("stars", stars_layer(240, 1, 0.5), 0.05), ("MOON", None, 0.06),
            ("far_hills", hill_layer((24, 66, 78, 255), PH * 0.52, 90, 6, 1), 0.12),
            ("far_trees", trunk_layer(22, (20, 52, 64, 255), 30, 60, 8, 2, avoid=(PW * 0.42, PW * 0.95)), 0.2),
            ("fog1", fog_band(PH * 0.60, 180, (90, 150, 160), 90), 0.25),
            ("mid_trees", trunk_layer(12, (12, 34, 44, 255), 70, 130, 3, 3, avoid=(PW * 0.38, PW * 0.98)), 0.4),
            ("fog2", fog_band(PH * 0.72, 120, (70, 130, 140), 70), 0.5),
            ("hill", hill_layer((8, 22, 30, 255), PH * 0.70, 40, 1, 4), 0.55), ("LEO", None, 0.55),
            ("near_trees", trunk_layer(3, (4, 12, 18, 255), 160, 220, 14, 5, edges=True), 0.9),
            ("fg", foliage_layer((3, 10, 14, 255), 16, 6, PH * 0.86, 9, 340), 1.2)]

@functools.lru_cache(maxsize=1)
def beach_plates():
    hz = PH * 0.42
    sky = Image.fromarray(grad(PH, PW, (8, 22, 40), (34, 76, 90)), "RGB").convert("RGBA")
    sea = Image.new("RGBA", (PW, PH), (0, 0, 0, 0)); sea.paste(Image.fromarray(grad(int(PH - hz), PW, (26, 70, 84), (8, 26, 36)), "RGB"), (0, int(hz)))
    hl = Image.new("RGBA", (PW, PH), (0, 0, 0, 0)); d = ImageDraw.Draw(hl)
    d.polygon([(0, hz + 4)] + [(x, hz - 30 - 26 * math.sin(x / 140) - 18 * math.sin(x / 47)) for x in range(0, int(PW * 0.35), 20)] + [(PW * 0.35, hz + 4)], fill=(14, 36, 48, 255))
    rocks = Image.new("RGBA", (PW, PH), (0, 0, 0, 0)); d = ImageDraw.Draw(rocks)
    for x, y, r in ((PW * 0.05, PH * 0.98, 260), (PW * 0.22, PH * 1.02, 200), (PW * 0.95, PH * 1.0, 230)):
        d.ellipse((x - r * 1.3, y - r, x + r * 1.3, y + r), fill=(5, 12, 16, 255))
    return [("sky", sky, 0.05), ("stars", stars_layer(200, 7, 0.38), 0.05), ("MOON", None, 0.06), ("sea", sea, 0.15),
            ("headland", hl.filter(ImageFilter.GaussianBlur(3)), 0.15), ("fog", fog_band(hz, 40, (120, 170, 180), 70), 0.15),
            ("DYN", None, 0.4), ("LEO", None, 0.5), ("rocks", rocks.filter(ImageFilter.GaussianBlur(14)), 1.1)]

def beach_dynamic(fr, t, m, tide, dx):
    hz = PH * 0.42; lay = Image.new("RGBA", (PW, PH), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    mx = PW * 0.62 + dx * 0.06
    for i in range(46):  # moonlight path on the water
        k = i / 45; y = hz + 8 + (PH * 0.30) * k ** 1.4; w = 16 + 170 * k
        x = mx + math.sin(t * 2 + i * 1.7) * w * 0.6
        a = int(150 * m * (0.5 + 0.5 * math.sin(t * 5 + i * 2.3)))
        d.ellipse((x - w * 0.5, y - 2 - 3 * k, x + w * 0.5, y + 2 + 3 * k), fill=(230, 240, 220, a))
    # shoreline: diagonal beach, swash moves with the tide
    sand = lambda x: PH * 0.98 - (x - PW * 0.18) * 0.62
    swash = 40 + 170 * tide * (0.5 + 0.5 * math.sin(t * 1.5)) + 30 * (1 - tide)
    xs = list(range(int(PW * 0.15), PW + 40, 30))
    d.polygon([(x, sand(x)) for x in xs] + [(PW, PH), (PW * 0.15, PH)], fill=(52, 46, 44, 255))
    wet = [(x, sand(x) + swash * 0.62 + 6 * math.sin(x / 50 + t * 3)) for x in xs]
    d.polygon([(x, sand(x) - 2) for x in xs] + list(reversed(wet)), fill=(20, 54, 66, 235))
    d.line(wet, fill=(200, 225, 230, int(170 + 60 * math.sin(t * 3))), width=6)
    lay = lay.filter(ImageFilter.GaussianBlur(1.2))
    fr.alpha_composite(offset(lay, dx * 0.4))

@functools.lru_cache(maxsize=1)
def pool_plates():
    sky = Image.fromarray(grad(PH, PW, (46, 52, 96), (248, 160, 110)), "RGB").convert("RGBA")
    sun = radial(900, (255, 200, 120), 2.0, 200); sky.alpha_composite(sun, (int(PW * 0.72 - 450), int(PH * 0.30 - 450)))
    sky.alpha_composite(radial(160, (255, 240, 200), 1.0, 255), (int(PW * 0.72 - 80), int(PH * 0.30 - 80)))
    sea = Image.new("RGBA", (PW, PH), (0, 0, 0, 0)); ImageDraw.Draw(sea).rectangle((0, PH * 0.36, PW, PH * 0.46), fill=(120, 110, 140, 255))
    rocks = Image.new("RGBA", (PW, PH), (0, 0, 0, 0)); d = ImageDraw.Draw(rocks)
    d.rectangle((0, PH * 0.44, PW, PH), fill=(70, 48, 52, 255))
    r = np.random.default_rng(3)
    for _ in range(18):
        x, y, rr = r.uniform(0, PW), r.uniform(PH * 0.44, PH), r.uniform(60, 200)
        c = int(r.uniform(50, 95)); d.ellipse((x - rr * 1.4, y - rr * 0.6, x + rr * 1.4, y + rr * 0.6), fill=(c, int(c * 0.72), int(c * 0.72), 255))
    near = Image.new("RGBA", (PW, PH), (0, 0, 0, 0)); ImageDraw.Draw(near).ellipse((-200, PH * 0.88, PW * 0.6, PH * 1.3), fill=(30, 20, 24, 255))
    return [("sky", sky, 0.05), ("sea", sea.filter(ImageFilter.GaussianBlur(4)), 0.1), ("rocks", rocks.filter(ImageFilter.GaussianBlur(2.5)), 0.3),
            ("DYN", None, 0.35), ("LEO", None, 0.45), ("near", near.filter(ImageFilter.GaussianBlur(16)), 1.0)]

def pool_dynamic(fr, t, water, dx):
    lay = Image.new("RGBA", (PW, PH), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    px, py = PW * 0.42, PH * 0.62
    d.ellipse((px - 380, py - 120, px + 380, py + 120), fill=(96, 70, 66, 255))
    if water > 0.03:
        rw, rh = 360 * math.sqrt(water), 108 * math.sqrt(water)
        d.ellipse((px - rw, py - rh, px + rw, py + rh), fill=(150, 130, 170, 255))
        d.ellipse((px - rw * 0.8, py - rh * 0.7, px + rw * 0.5, py + rh * 0.1), fill=(230, 170, 150, 160))
    cx, cy = px - 180 + 40 * math.sin(t * 1.6), py - 20 - abs(math.sin(t * 7)) * 8  # little crab
    d.ellipse((cx - 38, cy - 24, cx + 38, cy + 24), fill=(222, 92, 52, 255))
    for s in (-1, 1):
        d.line((cx + s * 30, cy - 10, cx + s * 56, cy - 40), fill=(222, 92, 52, 255), width=10)
        d.ellipse((cx + s * 56 - 16, cy - 56, cx + s * 56 + 16, cy - 28), fill=(232, 102, 62, 255))
        for k in range(3): d.line((cx + s * 24, cy + 6 + k * 6, cx + s * 52, cy + 22 + k * 8), fill=(190, 70, 40, 255), width=6)
        d.line((cx + s * 10, cy - 20, cx + s * 14, cy - 40), fill=(40, 20, 20, 255), width=5)
        d.ellipse((cx + s * 14 - 7, cy - 48, cx + s * 14 + 7, cy - 34), fill=(250, 250, 250, 255))
    if water < 0.5:
        for i in range(2):
            dy = (t * 40 + i * 30) % 60; d.ellipse((cx + 50 + i * 20 - 7, cy - 70 - dy - 10, cx + 50 + i * 20 + 7, cy - 70 - dy + 10), fill=(140, 200, 255, 200))
    fr.alpha_composite(offset(lay.filter(ImageFilter.GaussianBlur(1.0)), dx * 0.35))

@functools.lru_cache(maxsize=1)
def space_plates():
    sky = Image.fromarray(grad(PH, PW, (6, 8, 24), (16, 20, 48)), "RGB").convert("RGBA")
    for x, y, s, c in ((0.2, 0.25, 1300, (90, 50, 140)), (0.85, 0.7, 1500, (30, 110, 140)), (0.5, 0.9, 1100, (120, 40, 90))):
        sky.alpha_composite(radial(s, c, 2.0, 110), (int(PW * x - s / 2), int(PH * y - s / 2)))
    return [("sky", sky, 0.03), ("stars", stars_layer(600, 9, 1.0, (60, 255)), 0.06), ("DYN", None, 0.15), ("LEO", None, 0.6)]

@functools.lru_cache(maxsize=8)
def earth_img(r, ice):
    im = render.planet_img("earth", r).copy()
    if ice:
        from PIL import ImageChops as C
        c = im.width / 2; msk = Image.new("L", im.size, 0); ImageDraw.Draw(msk).ellipse((c - r, c - r, c + r, c + r), fill=255)
        cap = Image.new("L", im.size, 0); cd = ImageDraw.Draw(cap)
        cd.rectangle((0, 0, im.width, c - r * 0.82), fill=235); cd.rectangle((0, c + r * 0.85, im.width, im.height), fill=235)
        im.paste((240, 248, 255), (0, 0), C.multiply(msk, cap.filter(ImageFilter.GaussianBlur(10))))
    halo = radial(int(r * 2.6), (90, 170, 255), 2.4, 170)
    out = Image.new("RGBA", halo.size, (0, 0, 0, 0)); out.alpha_composite(halo); out.alpha_composite(im, ((halo.width - im.width) // 2,) * 2)
    return out

def space_dynamic(fr, t, wobble, chaos, dx):
    ex, ey = PW * 0.5 + dx * 0.15, PH * 0.36
    tilt = 23.4 + wobble * math.sin(t * 2.2)
    e = earth_img(300, 1).rotate(-tilt, resample=Image.BICUBIC)
    lay = Image.new("RGBA", (PW, PH), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    a = math.radians(tilt); L = 470
    d.line((ex - math.sin(a) * L, ey - math.cos(a) * L * -1 * -1, ex + math.sin(a) * L, ey + math.cos(a) * L), fill=(255, 120, 110, 140), width=6)
    fr.alpha_composite(lay)
    if chaos > 0:
        fr.alpha_composite(radial(1500, (90, 170, 255), 2.0, int(120 * chaos)), (int(ex - 1050), int(ey - 750)))
        fr.alpha_composite(radial(1500, (255, 110, 40), 2.0, int(140 * chaos)), (int(ex - 450), int(ey - 750)))
    fr.alpha_composite(e, (int(ex - e.width / 2), int(ey - e.height / 2)))
    if chaos > 0:
        tint = Image.new("RGBA", (PW, PH), (0, 0, 0, 0)); td = ImageDraw.Draw(tint); r = 300
        td.pieslice((ex - r, ey - r, ex + r, ey + r), 90, 270, fill=(235, 245, 255, int(150 * chaos)))
        td.pieslice((ex - r, ey - r, ex + r, ey + r), 270, 450, fill=(255, 90, 20, int(120 * chaos)))
        fr.alpha_composite(tint.filter(ImageFilter.GaussianBlur(6)))
        rng = np.random.default_rng(5); sd = ImageDraw.Draw(fr)
        for i in range(40):
            x0, sp = rng.uniform(0, 1), rng.uniform(60, 160)
            if x0 < 0.5: x, y, c = PW * x0, (t * sp + i * 97) % PH, (230, 240, 255)
            else: x, y, c = PW * x0, PH - (t * sp + i * 97) % PH, (255, 170, 60)
            sd.ellipse((x - 5, y - 5, x + 5, y + 5), fill=c)

ENVS = {"forest": forest_plates, "beach": beach_plates, "tidepool": pool_plates, "space": space_plates, "chaos": space_plates}

def render_frame(sh, t, k, fire):
    env = sh["env"]; plates = ENVS[env]()
    px = ramp(sh.get("pan", [-0.4, 0.4]), k); z = ramp(sh.get("zoom", [1.0, 1.08]), k)
    m = ramp(sh.get("moon", 1), k); dxu = px * 120
    fr = Image.new("RGBA", (PW, PH), (0, 0, 0, 255))
    lv = sh.get("leo")
    for name, img, depth in plates:
        dx = dxu * depth
        if name == "MOON":
            if m > 0.01: fr.alpha_composite(offset(fade(moon_layer(PW * (0.66 if env == "forest" else 0.62), PH * (0.24 if env == "forest" else 0.18), 1.0), m), dx))
        elif name == "DYN":
            if env == "beach": beach_dynamic(fr, t, m, ramp(sh.get("tide", 1), k), dxu)
            elif env == "tidepool": pool_dynamic(fr, t, ramp(sh.get("water", 1), k), dxu)
            else: space_dynamic(fr, t, ramp(sh.get("wobble", 0), k), 1.0 if env == "chaos" else 0.0, dxu)
        elif name == "LEO":
            if lv: draw_leo_in(fr, lv, t, k, dx)
        else:
            fr.alpha_composite(offset(img, dx))
        if name == "LEO" and env == "forest":  # fireflies
            for f in fire:
                fx = (f[0] * PW + math.sin(t * f[2] + f[3]) * 60 + t * 15) % PW
                fy = f[1] * PH + math.cos(t * f[2] * 0.8 + f[3]) * 50; tw = 0.5 + 0.5 * math.sin(t * 4 + f[3] * 3)
                fr.alpha_composite(radial(40, (255, 220, 120), 2, int(220 * tw)), (int(fx - 20), int(fy - 20)))
    cw, ch = W / z, H / z; cx, cy = PW / 2, PH * 0.5
    out = fr.convert("RGB").resize((W, H), Image.BICUBIC, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))
    if env in ("forest", "beach"):  # the whole night darkens without the Moon
        out = Image.eval(out, lambda v, s=0.62 + 0.38 * m: int(v * s))
    return out

def draw_leo_in(fr, lv, t, k, dx):
    h = lv.get("h", 540); fl = lv.get("float", False)
    char, lantern, feet = draw_leo(t, h, look_up=ramp(lv.get("look_up", 0), k), wide=ramp(lv.get("wide", 0), k),
                                   down=ramp(lv.get("down", 0), k), lantern=lv.get("lantern", True))
    if lv.get("facing", 1) < 0:
        char = char.transpose(Image.FLIP_LEFT_RIGHT); lantern = (char.width - lantern[0], lantern[1]); feet = (char.width - feet[0], feet[1])
    if fl: char = char.rotate(8 * math.sin(t * 0.9), resample=Image.BICUBIC, center=feet)
    cx = PW * lv.get("x", 0.4) + dx; cy = PH * lv.get("y", 0.70) + (math.sin(t * 1.3) * 18 if fl else 0)
    ox, oy = int(cx - feet[0]), int(cy - feet[1]); lx, ly = ox + lantern[0], oy + lantern[1]
    on = lv.get("lantern", True); fl_ = 0.85 + 0.15 * math.sin(t * 11) * math.sin(t * 7.3)
    if on:
        for size, col, a in ((1300, (255, 140, 40), int(85 * fl_)), (520, (255, 185, 90), int(150 * fl_))):
            fr.alpha_composite(radial(size, col, 2.0, a), (int(lx - size / 2), int(ly - size / 2)))
    fr.alpha_composite(char, (ox, oy))
    if on: fr.alpha_composite(radial(90, (255, 240, 180), 1.5, int(255 * fl_)), (int(lx - 45), int(ly - 45)))

VIG = None
def grade(fr, t):
    global VIG
    if VIG is None:
        y, x = np.ogrid[0:H, 0:W]
        VIG = np.clip(1 - 0.55 * (((x - W / 2) / (W * 0.75)) ** 2 + ((y - H * 0.5) / (H * 0.6)) ** 2), 0.35, 1)[..., None].astype(np.float32)
    a = np.asarray(fr).astype(np.float32) / 255 * VIG
    g = np.random.default_rng(int(t * 24)).normal(0, 0.018, (H // 2, W // 2, 1)).astype(np.float32).repeat(2, 0).repeat(2, 1)
    return Image.fromarray((np.clip(a + g, 0, 1) * 255).astype(np.uint8))

def build(script, out):
    sc = json.load(open(script)); voice, speed = render.CHANNELS["whatif"]["voices"]["N"]
    t = 0.6; shots = []; parts = []
    for s in sc["shots"]:
        a = render.tts(s["say"], voice, speed); t0 = t + 0.25
        parts.append((t0, a)); dur = 0.25 + len(a) / SR + s.get("pause", 0.45)
        shots.append(dict(s, t0=t, t1=t + dur, words=render.word_times(s["say"], t0, len(a) / SR))); t += dur
    total = t + 0.6; n = int(total * SR); vo = np.zeros(n, np.float32)
    for t0, a in parts: vo[int(t0 * SR):int(t0 * SR) + len(a)] += a
    wh = render.whoosh("whatif"); sfx = np.zeros(n, np.float32)
    for s in shots[1:]:
        w0 = max(0, int(s["t0"] * SR) - len(wh) // 2); sfx[w0:w0 + len(wh)] += wh[:n - w0]
    mix = vo + render.synth_music("whatif", n) * 0.10 + sfx * 0.12
    mix = (mix / np.abs(mix).max() * 0.9).astype(np.float32)
    import soundfile as sf; wav = out[:-4] + ".wav"; sf.write(wav, mix, SR)
    rng = np.random.default_rng(21); fire = rng.uniform(0, 1, (24, 4)); fire[:, 1] = 0.45 + fire[:, 1] * 0.4; fire[:, 2] = 0.5 + fire[:, 2]; fire[:, 3] *= 10
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-i", wav, "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                           "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for fi in range(int(total * FPS)):
        t = fi / FPS
        sh = next((s for s in shots if s["t0"] <= t < s["t1"]), shots[-1]); k = min(1, (t - sh["t0"]) / (sh["t1"] - sh["t0"]))
        fr = grade(render_frame(sh, t, k, fire), t)
        for g in render.build_groups(sh["words"]):
            if g[0][1] <= t < g[-1][2] + 0.15: render.draw_caption(fr, g, t, "whatif", None, 0.80); break
        lt, ld = t - sh["t0"], sh["t1"] - t
        a = min(1, lt / 0.3, ld / 0.25 if sh is not shots[-1] else 1, t / 0.8)
        if a < 1: fr = Image.blend(Image.new("RGB", (W, H)), fr, max(0, a))
        ff.stdin.write(fr.tobytes())
    ff.stdin.close(); ff.wait(); os.remove(wav); print("OK", out, round(total, 1))

if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
