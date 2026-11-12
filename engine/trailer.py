"""Movie-trailer style renderer: cinematic title cards, deep narrator, BRAAAM hits, letterbox, grade, grain,
story scenes (scene kits) starring Blip 2.0.

python engine/trailer.py scripts/trailer/moon.json
Shot types:  {"card": "ONE NIGHT...", "say": "...", "hit": true}
             {"scene": "night", "p": {...}, "blip": {"x":0.3,"y":0.62,"size":260,"pose":"look_up"}, "say": "...", "zoom": [1.0,1.12]}
"say" may contain "|" to insert dramatic pauses.
"""
import json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render, scenes
from character import draw_blip
from render import W, H, FPS, SR

CINZEL = os.path.join(render.ROOT, "fonts", "Cinzel.ttf")
_fc = {}
def cinzel(size, weight="Black"):
    k = (size, weight)
    if k not in _fc:
        f = ImageFont.truetype(CINZEL, size); f.set_variation_by_name(weight); _fc[k] = f
    return _fc[k]

# ------------------------------------------------------------------ audio design
def reverb(x, secs=1.8, mixamt=0.35):
    n = int(SR * secs); rng = np.random.default_rng(0)
    ir = rng.standard_normal(n) * np.exp(-np.arange(n) / SR * 3.5); ir /= np.abs(ir).sum() / 6
    L = len(x) + n; nfft = 1 << (L - 1).bit_length()
    wet = np.fft.irfft(np.fft.rfft(x, nfft) * np.fft.rfft(ir, nfft), nfft)[:len(x)]
    return x * (1 - mixamt) + wet * mixamt

def braam(dur=2.6):
    t = np.arange(int(SR * dur)) / SR; env = np.minimum(1, t / 0.04) * np.exp(-t * 1.3)
    s = sum(np.sign(np.sin(2 * np.pi * f * t)) * 0.3 + np.sin(2 * np.pi * f * t) for f in (41.2, 41.6, 61.7, 82.4))
    k = 30; s = np.convolve(s, np.ones(k) / k, "same")
    return np.tanh(s * 1.5) * env

def boom(dur=1.8):
    t = np.arange(int(SR * dur)) / SR
    f = 110 * np.exp(-t * 4) + 38; ph = 2 * np.pi * np.cumsum(f) / SR
    nz = np.random.default_rng(1).standard_normal(len(t)) * np.exp(-t * 30) * 0.6
    return (np.sin(ph) * np.exp(-t * 2.2) + nz) * 0.9

def riser(dur=2.0):
    t = np.arange(int(SR * dur)) / SR; f = 150 * (12 ** (t / dur)); ph = 2 * np.pi * np.cumsum(f) / SR
    nz = np.random.default_rng(2).standard_normal(len(t)); nz = np.convolve(nz, np.ones(6) / 6, "same")
    return (np.sin(ph) * 0.5 + nz * 0.5) * (t / dur) ** 2

def score(n, hits, risers):
    t = np.arange(n) / SR; out = np.zeros(n)
    # dark string pad that swells over the trailer
    swell = np.clip(t / (n / SR), 0, 1) ** 1.5
    for f in (55, 65.4, 82.4, 110, 130.8):
        saw = 2 * ((t * f * 1.003) % 1) - 1 + 2 * ((t * f) % 1) - 1
        out += saw * 0.05
    k = 40; out = np.convolve(out, np.ones(k) / k, "same") * (0.25 + 0.75 * swell)
    # ticking pulse (heartbeat of the trailer)
    for b in np.arange(0.0, n / SR, 0.5):
        s0 = int(b * SR); m = min(int(SR * 0.08), n - s0); tt = np.arange(m) / SR
        out[s0:s0 + m] += np.sin(2 * np.pi * 1800 * tt) * np.exp(-tt * 90) * 0.12
    for h in hits:
        for snd, g in ((braam(), 0.9), (boom(), 0.8)):
            s0 = int(h * SR); m = min(len(snd), n - s0)
            if m > 0: out[s0:s0 + m] += snd[:m] * g
    for r in risers:
        snd = riser(); s0 = int(r * SR) - len(snd); s0 = max(0, s0); m = min(len(snd), n - s0)
        out[s0:s0 + m] += snd[:m] * 0.5
    return reverb(out)

# ------------------------------------------------------------------ visuals
_grain = None
def grain():
    global _grain
    if _grain is None:
        rng = np.random.default_rng(9)
        _grain = [Image.fromarray(rng.integers(0, 255, (H // 3, W // 3), dtype=np.uint8)).resize((W, H)) for _ in range(5)]
    return _grain

y_, x_ = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = np.clip(1 - 0.45 * (((x_ - W / 2) / (W * 0.8)) ** 2 + ((y_ - H / 2) / (H * 0.62)) ** 2), 0.5, 1)[..., None]
del y_, x_

def grade(fr, t):
    a = np.asarray(fr).astype(np.float32) / 255
    lum = a @ np.array([0.3, 0.59, 0.11], np.float32)
    shadows = (1 - lum)[..., None]; hi = lum[..., None]
    a = a + shadows * np.array([-0.03, 0.02, 0.06]) * 0.8 + hi * np.array([0.05, 0.015, -0.04]) * 0.8  # teal/orange
    a = (a - 0.5) * 1.08 + 0.52
    a = a * VIG
    g = np.asarray(grain()[int(t * 24) % 5], np.float32)[..., None] / 255 - 0.5
    a = a + g * 0.05
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))

def camera(fr, zoom, pan=(0, 0)):
    if zoom <= 1.001 and pan == (0, 0): return fr
    cw, ch = W / zoom, H / zoom
    cx, cy = W / 2 + pan[0] * (W - cw) / 2, H / 2 + pan[1] * (H - ch) / 2
    return fr.resize((W, H), Image.BICUBIC, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))

def letterbox(fr, k=1.0):
    d = ImageDraw.Draw(fr); b = int(H * 0.075 * k)
    d.rectangle((0, 0, W, b), fill=0); d.rectangle((0, H - b, W, H), fill=0)

def card(text, lt, sub=None):
    fr = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(fr)
    k = min(1, lt / 0.45); sc = 1.0 + 0.04 * lt
    big = "\n" not in text and len(text) <= 9
    f = cinzel(int((150 if big else 96) * sc))
    col = tuple(int(c * k) for c in (240, 200, 120))
    d.multiline_text((W / 2, H * 0.45), text, font=f, fill=col, anchor="mm", align="center", spacing=30)
    if sub: d.text((W / 2, H * 0.56), sub, font=cinzel(52, "Bold"), fill=tuple(int(c * k) for c in (200, 200, 210)), anchor="mm")
    # light sweep across the title
    sx = (lt / 1.6) * W * 1.6 - W * 0.3
    if 0 < lt < 1.6:
        glow = Image.new("L", (W, H), 0); ImageDraw.Draw(glow).polygon([(sx, 0), (sx + 120, 0), (sx - 280, H), (sx - 400, H)], fill=60)
        fr = Image.composite(Image.new("RGB", (W, H), (255, 240, 200)), fr, glow.point(lambda v: v) if False else glow.point(lambda v: v // 3))
    return fr

def caption(fr, words, t):
    for g in render.build_groups(words, maxw=3, maxc=16):
        if g[0][1] <= t < g[-1][2] + 0.1:
            txt = " ".join(w for w, _, _ in g).upper()
            d = ImageDraw.Draw(fr); f = cinzel(66, "Bold")
            d.text((W / 2, H * 0.83), txt, font=f, fill=(250, 240, 220), anchor="mm", stroke_width=6, stroke_fill=(0, 0, 0))
            return

# ------------------------------------------------------------------ main
STARS = render.Backgrounds("whatif", 11)

def build(script, out):
    sc = json.load(open(script)); voice, speed = sc.get("voice", "am_onyx"), sc.get("speed", 0.88)
    t = 0.3; shots = []; vo_parts = []; hits = []; risers = []
    for s in sc["shots"]:
        words = []; start = t
        if s.get("hit"): hits.append(t); risers.append(t)
        cur = t + (0.5 if s.get("hit") else 0.15)
        if s.get("say"):
            for chunk in [c.strip() for c in s["say"].split("|") if c.strip()]:
                a = render.tts(chunk, voice, speed * s.get("speed", 1)); vo_parts.append((cur, a))
                words += render.word_times(chunk, cur, len(a) / SR); cur += len(a) / SR + 0.32
        dur = max(cur - t + 0.25, s.get("min", 1.6))
        shots.append(dict(s, t0=t, t1=t + dur, words=words)); t += dur
    total = t + 0.8; n = int(total * SR)
    vo = np.zeros(n)
    for t0, a in vo_parts: s0 = int(t0 * SR); vo[s0:s0 + len(a)] += a
    vo = reverb(vo, 1.2, 0.12)
    mus = score(n, hits, risers)
    mix = vo * 1.0 + mus / (np.abs(mus).max() + 1e-6) * 0.42
    mix = np.tanh(mix * 1.1) * 0.95
    import soundfile as sf; wav = out[:-4] + ".wav"; sf.write(wav, mix.astype(np.float32), SR)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-i", wav, "-c:v", "libx264", "-crf", "19", "-preset", "medium", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for fi in range(int(total * FPS)):
        t = fi / FPS
        sh = next((s for s in shots if s["t0"] <= t < s["t1"]), shots[-1]); lt = t - sh["t0"]; sd = sh["t1"] - sh["t0"]
        if "card" in sh:
            fr = card(sh["card"], lt, sh.get("sub"))
        else:
            fr = STARS.draw(t, sh)
            for e in scenes.draw_scene(fr, sh, lt, sd, t):
                render.draw_item(fr, dict(e, x=e["x"] / W, y=e["y"] / H, anim="none"), 1, sd, t, "whatif")
            for it in sh.get("items", []): render.draw_item(fr, it, lt, sd, t, "whatif")
            b = sh.get("blip")
            if b:
                pose = b["pose"]
                for k, p2 in b.get("then", []):
                    if lt >= k: pose = p2
                bx = b["x"] + (b.get("move", 0) * min(1, lt / max(sd, 0.1)))
                draw_blip(fr, W * bx, H * b["y"], b.get("size", 260), pose, t, look=tuple(b.get("look", (0, 0))), facing=b.get("facing", 1))
            z0, z1 = sh.get("zoom", [1.0, 1.08])
            fr = camera(fr, z0 + (z1 - z0) * lt / sd, tuple(sh.get("pan", (0, 0))))
            if sh.get("shake"):
                fr = fr.transform(fr.size, Image.AFFINE, (1, 0, math.sin(t * 50) * 10, 0, 1, math.cos(t * 43) * 10))
            fr = grade(fr, t)
        caption(fr, sh["words"], t)
        letterbox(fr)
        # dip-to-black in/out of every shot + white flash on hits
        k = min(1, lt / 0.18, (sd - lt) / 0.14)
        if k < 1: fr = Image.blend(Image.new("RGB", (W, H)), fr, max(0, k))
        if sh.get("hit") and lt < 0.12: fr = Image.blend(fr, Image.new("RGB", (W, H), (255, 245, 230)), 0.8 * (1 - lt / 0.12))
        ff.stdin.write(fr.tobytes())
    ff.stdin.close(); ff.wait(); os.remove(wav); print("OK", out, round(total, 1), "s")

if __name__ == "__main__":
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(render.ROOT, "out", "trailer.mp4")
    build(sys.argv[1], out)
