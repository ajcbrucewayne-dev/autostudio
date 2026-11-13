"""AutoStudio renderer: turns a JSON script into a finished vertical Short (1080x1920 mp4).

Usage:  python engine/render.py scripts/whatif/001.json [out_dir]
Everything is free and offline: Kokoro TTS voice, procedural animation, procedural music.
"""
import json, math, os, random, subprocess, sys, functools
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scenes
from kid import draw_kid
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H, FPS, SR = 1080, 1920, 30, 24000
FONT_SANS = os.path.join(ROOT, "fonts", "Inter-ExtraBold.otf")
FONT_SERIF = os.path.join(ROOT, "fonts", "DejaVuSerif-Bold.ttf")
FONT_EMOJI = os.path.join(ROOT, "fonts", "NotoColorEmoji.ttf")

CHANNELS = {
    "whatif": {"voices": {"N": ("am_michael", 1.05)}, "font": FONT_SANS, "hi": (255, 214, 0)},
    "skits": {"voices": {"A": ("am_puck", 1.1), "B": ("af_bella", 1.08), "N": ("am_michael", 1.1)},
              "font": FONT_SANS, "hi": (255, 214, 0)},
    "darkhistory": {"voices": {"N": ("bm_george", 0.95)}, "font": FONT_SERIF, "hi": (220, 40, 40)},
}

# ---------------------------------------------------------------- utils
def clamp(v, a=0.0, b=1.0): return max(a, min(b, v))
def ease_out(p): return 1 - (1 - clamp(p)) ** 3
def ease_back(p):
    p = clamp(p); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (p - 1) ** 3 + c1 * (p - 1) ** 2
def hexrgb(h): h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

@functools.lru_cache(maxsize=64)
def font(path, size): return ImageFont.truetype(path, size)

@functools.lru_cache(maxsize=512)
def emoji_img(ch, size, tint=None):
    f = ImageFont.truetype(FONT_EMOJI, 109)
    im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((80, 80), ch, font=f, embedded_color=True, anchor="mm")
    im = im.crop(im.getbbox() or (0, 0, 1, 1))
    s = size / max(im.size)
    im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    if tint == "sepia":
        a = np.asarray(im).astype(np.float32)
        g = a[..., :3] @ np.array([0.3, 0.59, 0.11])
        g = (g - 128) * 1.35 + 110
        out = np.stack([g * 1.07, g * 0.86, g * 0.62], -1).clip(0, 255)
        im = Image.fromarray(np.dstack([out, a[..., 3]]).astype(np.uint8), "RGBA")
    return im

def with_alpha(im, a):
    if a >= 0.999: return im
    im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * a))); return im

def paste_center(frame, im, x, y):
    frame.paste(im, (int(x - im.width / 2), int(y - im.height / 2)), im)

# ---------------------------------------------------------------- voice
_kokoro = None
def tts(text, voice, speed):
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        _kokoro = Kokoro(os.path.join(ROOT, "models", "kokoro-v1.0.int8.onnx"),
                         os.path.join(ROOT, "models", "voices-v1.0.bin"))
    s, sr = _kokoro.create(text, voice=voice, speed=speed, lang="en-gb" if voice.startswith("b") else "en-us")
    s = np.asarray(s, dtype=np.float32)
    idx = np.where(np.abs(s) > 0.02)[0]
    if len(idx): s = s[max(0, idx[0] - 600): idx[-1] + 1200]
    return s

def word_times(text, t0, dur):
    words = text.split()
    wts = [len(w) + 2 + (4 if w[-1] in ",.?!;:" else 0) for w in words]
    tot = sum(wts); out = []; t = t0
    for w, k in zip(words, wts):
        d = dur * k / tot; out.append((w, t, t + d)); t += d
    return out

# ---------------------------------------------------------------- music & sfx
def synth_music(kind, n):
    t = np.arange(n) / SR; out = np.zeros(n, np.float32); rng = np.random.default_rng(7)
    if kind == "whatif":
        chords = [[220, 261.6, 329.6], [174.6, 220, 261.6], [261.6, 329.6, 392], [196, 246.9, 293.7]]
        seg = int(SR * 4)
        for i in range(0, n, seg):
            ch = chords[(i // seg) % 4]; L = min(seg, n - i); tt = np.arange(L) / SR
            env = np.minimum(1, tt / 1.2) * np.minimum(1, (L / SR - tt) / 1.0 + 0.05)
            for f in ch:
                out[i:i + L] += env * (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * f * 2.003 * tt)) * 0.12
            for k in range(8):  # soft arpeggio
                s0 = int(k * SR * 0.5)
                if s0 >= L: break
                f = ch[k % 3] * 2; m = min(int(SR * 0.45), L - s0); ta = np.arange(m) / SR
                out[i + s0:i + s0 + m] += np.sin(2 * np.pi * f * ta) * np.exp(-ta * 6) * 0.07
    elif kind == "darkhistory":
        out += (np.sin(2 * np.pi * 55 * t) + np.sin(2 * np.pi * 55.4 * t) + 0.5 * np.sin(2 * np.pi * 82.4 * t)) * 0.12
        noise = rng.standard_normal(n).astype(np.float32)
        k = int(SR * 0.01); wind = np.convolve(noise, np.ones(k) / k, "same")
        out += wind * (0.6 + 0.4 * np.sin(2 * np.pi * 0.11 * t)) * 0.5
        for b in np.arange(0.5, n / SR, 1.6):  # slow heartbeat
            for off, a in ((0, 1.0), (0.28, 0.7)):
                s0 = int((b + off) * SR); m = min(int(SR * 0.2), n - s0)
                if m > 0:
                    ta = np.arange(m) / SR; out[s0:s0 + m] += np.sin(2 * np.pi * 50 * ta) * np.exp(-ta * 25) * 0.5 * a
    else:  # skits: bouncy pluck loop
        notes = [261.6, 329.6, 392, 329.6, 293.7, 349.2, 440, 349.2]
        step = int(SR * 0.25)
        for i, s0 in enumerate(range(0, n, step)):
            f = notes[i % 8]; m = min(step, n - s0); ta = np.arange(m) / SR
            out[s0:s0 + m] += (np.sin(2 * np.pi * f * ta) + 0.4 * np.sin(4 * np.pi * f * ta)) * np.exp(-ta * 12) * 0.18
            if i % 2 == 0:
                out[s0:s0 + m] += np.sin(2 * np.pi * f / 2 * ta) * np.exp(-ta * 8) * 0.15
    return out / (np.abs(out).max() + 1e-6)

def whoosh(kind):
    m = int(SR * (0.12 if kind == "skits" else 0.45)); ta = np.arange(m) / SR
    if kind == "skits":
        return (np.sin(2 * np.pi * (500 + 1200 * ta / ta[-1]) * ta) * np.exp(-ta * 25)).astype(np.float32)
    rng = np.random.default_rng(1); nz = rng.standard_normal(m)
    k = 12; nz = np.convolve(nz, np.ones(k) / k, "same")
    return (nz * np.sin(np.pi * ta / ta[-1]) ** 2 * 0.8).astype(np.float32)

# ---------------------------------------------------------------- planets
@functools.lru_cache(maxsize=64)
def planet_img(kind, r):
    pal = {"earth": ("#2f6fd6", "#3ea84a"), "moon": ("#9a9a9a", "#6e6e6e"), "sun": ("#ffb52e", "#ffd76b"),
           "mars": ("#c1440e", "#8a2f0a"), "jupiter": ("#d8b48a", "#a0643c"), "venus": ("#e3c27a", "#c99a4b")}
    c1, c2 = pal.get(kind, (kind if kind.startswith("#") else "#7a5cff", "#4b39b0"))
    c1, c2 = np.array(hexrgb(c1), np.float32), np.array(hexrgb(c2), np.float32)
    S = 2 * r + 2; pad = int(r * 0.6) if kind == "sun" else 4; T = S + 2 * pad
    y, x = np.mgrid[0:T, 0:T].astype(np.float32); cx = cy = T / 2
    dx, dy = (x - cx) / r, (y - cy) / r; d2 = dx * dx + dy * dy; inside = d2 <= 1
    z = np.sqrt(np.clip(1 - d2, 0, 1))
    rng = np.random.default_rng(abs(hash(kind)) % 999)
    ph = rng.uniform(0, 6, 6)
    feat = (np.sin(dx * 3.1 + ph[0]) * np.sin(dy * 2.7 + ph[1]) + 0.6 * np.sin(dx * 7 + dy * 5 + ph[2])
            + 0.3 * np.sin(dx * 13 - dy * 11 + ph[3]))
    if kind == "jupiter": mask = (np.sin(dy * 14 + np.sin(dx * 3) * 0.6) > 0.1)
    elif kind == "moon":
        mask = np.zeros_like(inside)
        for _ in range(14):
            px, py, pr = rng.uniform(-0.8, 0.8), rng.uniform(-0.8, 0.8), rng.uniform(0.06, 0.2)
            mask |= (dx - px) ** 2 + (dy - py) ** 2 < pr * pr
    else: mask = feat > 0.45
    col = np.where(mask[..., None], c2, c1)
    light = np.clip(0.25 + 0.85 * (-0.5 * dx - 0.55 * dy + 0.67 * z), 0.15, 1.15)
    if kind == "sun": light = 0.9 + 0.2 * z
    rgb = np.clip(col * light[..., None], 0, 255)
    a = np.clip((1 - np.sqrt(d2)) * r, 0, 1) * 255
    if kind == "sun":
        glow = np.clip(1.6 - np.sqrt(d2), 0, 1) ** 2 * 200
        a = np.maximum(a, glow); rgb = np.where(inside[..., None], rgb, np.array([255, 190, 60]))
    return Image.fromarray(np.dstack([rgb, a]).astype(np.uint8), "RGBA")

# ---------------------------------------------------------------- blob character (mascots)
def draw_blob(frame, cx, cy, size, color, mood="happy", mouth=0.0, blink=False, look=0, t=0.0, squash=0.0):
    S = 2; bw, bh = int(size * 1.4), int(size * 1.5)
    im = Image.new("RGBA", (bw * S, bh * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    ox, oy, R = bw * S / 2, bh * S * 0.55, size * S / 2
    pts = []
    for k in range(64):
        a = 2 * math.pi * k / 64
        rr = R * (1 + 0.03 * math.sin(3 * a + t * 3) + 0.02 * math.sin(5 * a - t * 2))
        sx, sy = 1 + squash * 0.15, 1 - squash * 0.15
        yy = math.sin(a) * rr * sy * (1.0 if math.sin(a) < 0 else 0.92)
        pts.append((ox + math.cos(a) * rr * sx, oy + yy))
    c = hexrgb(color); dark = tuple(int(v * 0.55) for v in c)
    d.polygon(pts, fill=c, outline=dark, width=10)
    d.ellipse((ox - R * 0.55, oy - R * 0.7, ox - R * 0.15, oy - R * 0.45), fill=tuple(min(255, v + 60) for v in c))
    ex, ey, er = R * 0.33, oy - R * 0.18, R * 0.2
    for sgn in (-1, 1):
        x0 = ox + sgn * ex
        if blink: d.line((x0 - er, ey, x0 + er, ey), fill=(30, 30, 30), width=10)
        else:
            eh = er * (1.35 if mood == "shock" else 1.0)
            d.ellipse((x0 - er, ey - eh, x0 + er, ey + eh), fill="white", outline=(30, 30, 30), width=6)
            pr = er * (0.35 if mood == "shock" else 0.5)
            px = x0 + look * er * 0.4
            d.ellipse((px - pr, ey - pr + er * 0.1, px + pr, ey + pr + er * 0.1), fill=(25, 25, 25))
        by = ey - er * 1.5
        if mood == "angry": d.line((x0 - sgn * er, by - 8, x0 + sgn * er * 0.6, by + 22), fill=(30, 30, 30), width=14)
        elif mood == "sad": d.line((x0 - sgn * er, by + 18, x0 + sgn * er * 0.6, by - 6), fill=(30, 30, 30), width=12)
        elif mood == "smug": d.line((x0 - er, by + (0 if sgn < 0 else 14), x0 + er, by + (6 if sgn < 0 else 14)), fill=(30, 30, 30), width=12)
        elif mood == "shock": d.arc((x0 - er, by - 30, x0 + er, by + 10), 200, 340, fill=(30, 30, 30), width=12)
    my, mw = oy + R * 0.3, R * 0.32
    mo = clamp(mouth)
    if mood == "shock": d.ellipse((ox - mw * 0.5, my - mw * 0.4, ox + mw * 0.5, my + mw * (0.6 + mo * 0.5)), fill=(60, 20, 20))
    elif mo > 0.08:
        d.chord((ox - mw, my - mw * 0.3, ox + mw, my + mw * (0.3 + mo * 0.9)), 0, 180, fill=(60, 20, 20), outline=(30, 30, 30), width=6)
    elif mood in ("sad", "angry"): d.arc((ox - mw * 0.8, my, ox + mw * 0.8, my + mw), 200, 340, fill=(30, 30, 30), width=10)
    elif mood == "smug": d.arc((ox - mw * 0.4, my - mw * 0.6, ox + mw, my + mw * 0.4), 20, 120, fill=(30, 30, 30), width=10)
    else: d.arc((ox - mw * 0.8, my - mw * 0.6, ox + mw * 0.8, my + mw * 0.4), 20, 160, fill=(30, 30, 30), width=10)
    im = im.resize((bw, bh), Image.LANCZOS)
    frame.paste(im, (int(cx - bw / 2), int(cy - bh * 0.55)), im)

# ---------------------------------------------------------------- items (shared visual vocabulary)
def anim_state(anims, lt, sd, t):
    dx = dy = rot = 0.0; sc = al = 1.0
    for a in anims:
        if a == "pop": sc *= max(0.01, ease_back(lt / 0.35))
        elif a == "float": dy += math.sin(t * 2.2) * 14
        elif a == "spin": rot += lt * 35
        elif a == "shake": dx += math.sin(t * 55) * 12; dy += math.cos(t * 47) * 8
        elif a == "zoom": sc *= 1 + 0.18 * lt / max(sd, 0.1)
        elif a == "grow": sc *= max(0.01, ease_out(lt / max(sd * 0.8, 0.1)))
        elif a == "pulse": sc *= 1 + 0.07 * math.sin(t * 8)
        elif a == "slide_l": dx -= (1 - ease_out(lt / 0.5)) * W
        elif a == "slide_r": dx += (1 - ease_out(lt / 0.5)) * W
        elif a == "fall": dy -= (1 - ease_out(lt / 0.6)) * H * 0.7
        elif a == "fade_in": al *= clamp(lt / 0.6)
        elif a == "fade_out": al *= clamp(1 - lt / max(sd, 0.1))
        elif a == "boom": p = clamp(lt / 0.7); sc *= 1 + 1.8 * p; al *= 1 - p
        elif a == "shrink": sc *= max(0.01, 1 - ease_out(lt / max(sd, 0.1)))
        elif a == "drift": dx += (lt / max(sd, 0.1) - 0.5) * 120
    return dx, dy, sc, rot, al

def draw_item(frame, it, lt, sd, t, style):
    lt = lt - it.get("delay", 0)
    if lt < 0: return
    anims = it.get("anim", "pop").split("+")
    dx, dy, sc, rot, al = anim_state(anims, lt, sd, t)
    if al <= 0.01 or sc <= 0.01: return
    x, y = it.get("x", 0.5) * W + dx, it.get("y", 0.4) * H + dy
    if "emoji" in it:
        size = max(8, int(it.get("s", 420) * sc) // 6 * 6)
        im = emoji_img(it["emoji"], size, "sepia" if style == "darkhistory" else None)
        if it.get("flip"): im = im.transpose(Image.FLIP_LEFT_RIGHT)
        if rot: im = im.rotate(rot, expand=True, resample=Image.BICUBIC)
        paste_center(frame, with_alpha(im, al), x, y)
    elif "planet" in it:
        r = it.get("r", 260)
        im = planet_img(it["planet"], r)
        if sc != 1: im = im.resize((max(2, int(im.width * sc)), max(2, int(im.height * sc))), Image.BILINEAR)
        if rot: im = im.rotate(rot, resample=Image.BICUBIC)
        paste_center(frame, with_alpha(im, al), x, y)
        if it.get("label"):
            draw_text(frame, it["label"], x, y + r * sc + 60, 54, style, al)
    elif "text" in it or "counter" in it:
        if "counter" in it:
            a, b = it["counter"]; p = ease_out(lt / max(it.get("dur", sd * 0.8), 0.1))
            txt = f"{int(a + (b - a) * p):,}{it.get('suffix', '')}"
            if it.get("prefix"): txt = it["prefix"] + txt
        else: txt = it["text"]
        draw_text(frame, txt, x, y, int(it.get("size", 110) * sc), style, al, it.get("color"))

def draw_text(frame, txt, x, y, size, style, al=1.0, color=None):
    f = font(FONT_SERIF if style == "darkhistory" else FONT_SANS, max(10, size))
    lay = Image.new("RGBA", (W, int(size * 1.6 * (txt.count("\n") + 1)) + 40), (0, 0, 0, 0))
    col = hexrgb(color) if color else ((235, 220, 190) if style == "darkhistory" else (255, 255, 255))
    ImageDraw.Draw(lay).multiline_text((W / 2, lay.height / 2), txt, font=f, fill=col, anchor="mm", align="center",
                                       stroke_width=max(3, size // 12), stroke_fill=(10, 10, 10))
    paste_center(frame, with_alpha(lay, al), x, y)

# ---------------------------------------------------------------- backgrounds
class Backgrounds:
    def __init__(self, style, seed):
        self.style = style; rng = np.random.default_rng(seed); self.rng = rng
        if style == "whatif":
            y = np.linspace(0, 1, H * 2)[:, None, None]
            top, bot = np.array([8, 10, 32]), np.array([40, 14, 60])
            base = (top * (1 - np.abs(np.sin(y * math.pi * 2))) + bot * np.abs(np.sin(y * math.pi * 2)))
            base = np.repeat(base, W, 1).astype(np.uint8)
            img = Image.fromarray(base, "RGB"); d = ImageDraw.Draw(img)
            for _ in range(900):
                sx, sy = rng.integers(0, W), rng.integers(0, H * 2); b = int(rng.integers(90, 255)); r = rng.choice([1, 1, 2, 2, 3])
                d.ellipse((sx - r, sy - r, sx + r, sy + r), fill=(b, b, min(255, b + 20)))
            self.sky = img
        elif style == "darkhistory":
            y, x = np.mgrid[0:H, 0:W].astype(np.float32)
            v = 1 - np.clip(np.sqrt(((x - W / 2) / (W * 0.75)) ** 2 + ((y - H * 0.42) / (H * 0.6)) ** 2), 0, 1)
            base = np.stack([30 + 40 * v, 20 + 26 * v, 14 + 14 * v], -1)
            self.base = Image.fromarray(base.clip(0, 255).astype(np.uint8), "RGB")
            self.vig = Image.fromarray((np.clip(1 - v * 1.4, 0, 1) * 230).astype(np.uint8), "L")
            self.grain = [Image.fromarray(rng.integers(0, 50, (H // 2, W // 2), dtype=np.uint8), "L").resize((W, H)) for _ in range(4)]
            self.dust = rng.uniform(0, 1, (60, 3))

    def draw(self, t, scene):
        if self.style == "whatif":
            off = int(t * 25) % H
            return self.sky.crop((0, off, W, off + H)).copy()
        if self.style == "darkhistory":
            fl = 0.88 + 0.12 * math.sin(t * 13) * math.sin(t * 7.3)
            fr = Image.eval(self.base, lambda v: int(v * fl)); d = ImageDraw.Draw(fr)
            for dx_, dy_, s_ in self.dust:
                px = (dx_ * W + math.sin(t + s_ * 10) * 30) % W; py = (dy_ * H - t * 40 * (0.5 + s_)) % H
                d.ellipse((px - 2, py - 2, px + 2, py + 2), fill=(180, 160, 120))
            return fr
        # skits: room set
        sets = {"bedroom": ("#bfe0ff", "#c99a6a", ["🛏️", "🪟"]), "office": ("#e4e7eb", "#8f9aa6", ["💻", "🪴"]),
                "kitchen": ("#fff1c9", "#d9b48a", ["🍳", "🧊"]), "school": ("#d7f5d0", "#a9876a", ["📚", "🕒"]),
                "street": ("#ffd7c2", "#7d7d7d", ["🏢", "🌳"]), "phone": ("#e9ddff", "#b9a6e6", ["📱", "💬"]),
                "store": ("#ffe3ec", "#c9a0b0", ["🛒", "🏷️"]), "gym": ("#d8f3ff", "#7aa6b8", ["🏋️", "💪"])}
        wall, floor_, dec = sets.get(scene.get("set", "bedroom"), sets["bedroom"])
        fr = Image.new("RGB", (W, H), hexrgb(wall)); d = ImageDraw.Draw(fr)
        d.rectangle((0, int(H * 0.68), W, H), fill=hexrgb(floor_))
        d.line((0, int(H * 0.68), W, int(H * 0.68)), fill=(60, 60, 60), width=6)
        paste_center(fr, emoji_img(dec[0], 230), W * 0.18, H * 0.30)
        paste_center(fr, emoji_img(dec[1], 200), W * 0.84, H * 0.27)
        return fr

    def overlay(self, fr, t):
        if self.style == "darkhistory":
            dark = Image.new("RGB", (W, H), (0, 0, 0)); fr = Image.composite(dark, fr, self.vig)
            g = self.grain[int(t * 12) % 4]
            fr = Image.blend(fr, Image.merge("RGB", (g, g, g)), 0.06)
        return fr

# ---------------------------------------------------------------- captions
def build_groups(words, maxw=3, maxc=13):
    groups, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= maxw or sum(len(x[0]) for x in cur) > maxc or w[0][-1] in ".?!,;:":
            groups.append(cur); cur = []
    if cur: groups.append(cur)
    return groups

def draw_caption(frame, group, t, style, spk_color=None, yfrac=None):
    g0 = group[0][1]; p = ease_back((t - g0) / 0.18)
    size = int((110 if style != "darkhistory" else 92) * (0.85 + 0.15 * p))
    f = font(FONT_SERIF if style == "darkhistory" else FONT_SANS, size)
    hi = CHANNELS[style]["hi"]; base = spk_color or ((240, 225, 200) if style == "darkhistory" else (255, 255, 255))
    words = [(w if style == "darkhistory" else w.upper(), s, e) for w, s, e in group]
    sp = f.getlength(" "); widths = [f.getlength(w) for w, _, _ in words]
    total = sum(widths) + sp * (len(words) - 1)
    if total > W * 0.9:  # shrink to fit
        k = W * 0.9 / total; f = font(f.path, int(size * k)); sp *= k; widths = [w * k for w in widths]; total *= k
    d = ImageDraw.Draw(frame); x = (W - total) / 2; y = H * (yfrac or (0.62 if style != "skits" else 0.745))
    for (w, s, e), wd in zip(words, widths):
        col = hi if s <= t < e + 0.05 else base
        d.text((x, y), w, font=f, fill=col, anchor="lm", stroke_width=10, stroke_fill=(0, 0, 0))
        x += wd + sp

# ---------------------------------------------------------------- story character + thought bubbles
def draw_kid_scene(fr, k, lt, t):
    pose = k.get("pose", "idle")
    for at, p2 in k.get("then", []):
        if lt >= at: pose = p2
    x = k.get("x", 0.5) + k.get("move", 0) * min(1, lt / max(k.get("move_dur", 3.0), 0.1))
    draw_kid(fr, W * x, H * k.get("y", 0.7), k.get("h", 460), pose, t, facing=k.get("facing", 1))

def draw_bubble(fr, b, bt):
    p = max(0.01, ease_back(bt / 0.35)); f = font(FONT_SANS, max(6, int(50 * p)))
    x, y = W * b.get("x", 0.5), H * b.get("y", 0.3); d = ImageDraw.Draw(fr)
    bb = d.multiline_textbbox((x, y), b["text"], font=f, anchor="mm", align="center")
    pw, ph = (bb[2] - bb[0]) / 2 + 50 * p, (bb[3] - bb[1]) / 2 + 40 * p
    for ox, oy, k in ((-0.7, -0.5, 0.6), (0.7, -0.5, 0.6), (-0.7, 0.5, 0.55), (0.7, 0.5, 0.55), (0, -0.8, 0.6), (0, 0.8, 0.5)):
        r = min(pw, ph) * k
        d.ellipse((x + ox * pw - r, y + oy * ph - r, x + ox * pw + r, y + oy * ph + r), fill="white", outline=(40, 30, 30), width=5)
    d.rounded_rectangle((x - pw, y - ph, x + pw, y + ph), int(ph), fill="white", outline=(40, 30, 30), width=5)
    for ox, oy, k in ((-0.6, 0.8, 0.6), (-0.75, 0.62, 0.0)):
        pass
    tx, ty = W * b.get("tail_x", b.get("x", 0.5)), H * b.get("tail_y", b.get("y", 0.3) + 0.08)
    for i, r in enumerate((16, 11, 7)):
        k = (i + 1) / 4; cx_, cy_ = x + (tx - x) * (0.55 + k * 0.5), y + ph + (ty - y - ph) * k
        d.ellipse((cx_ - r * p, cy_ - r * p, cx_ + r * p, cy_ + r * p), fill="white", outline=(40, 30, 30), width=4)
    d.multiline_text((x, y), b["text"], font=f, fill=(40, 30, 60), anchor="mm", align="center")

# ---------------------------------------------------------------- main render
def render(script_path, out_dir=None):
    sc = json.load(open(script_path)); style = sc["channel"]; cfg = CHANNELS[style]
    out_dir = out_dir or os.path.join(ROOT, "out", style); os.makedirs(out_dir, exist_ok=True)
    name = os.path.splitext(os.path.basename(script_path))[0]
    gap = 0.12 if style == "skits" else 0.22
    # 1) voice + timeline
    voice = []; t = 0.35; timeline = []
    for s in sc["scenes"]:
        spk = s.get("speaker", "N"); vname, speed = cfg["voices"].get(spk, cfg["voices"]["N"])
        if "voice" in sc: vname, speed = sc["voice"]
        if s.get("say"):
            a = tts(s["say"], vname, speed * s.get("speed", 1.0))
        else:
            a = np.zeros(int(SR * s.get("hold", 1.0)), np.float32)
        dur = len(a) / SR + gap + s.get("pause", 0)
        timeline.append({"scene": s, "t0": t, "t1": t + dur, "speech": (t, t + len(a) / SR), "audio": a,
                         "words": word_times(s["say"], t, len(a) / SR) if s.get("say") else [], "spk": spk})
        t += dur
    total = t + 0.4; n = int(total * SR)
    vo = np.zeros(n, np.float32); sfx = np.zeros(n, np.float32); wh = whoosh(style)
    for i, seg in enumerate(timeline):
        s0 = int(seg["speech"][0] * SR); vo[s0:s0 + len(seg["audio"])] += seg["audio"]
        if i > 0 or style != "skits":
            w0 = max(0, int(seg["t0"] * SR) - len(wh) // 2); m = min(len(wh), n - w0); sfx[w0:w0 + m] += wh[:m]
    music = synth_music(style, n)
    mix = vo + music * {"whatif": 0.10, "darkhistory": 0.14, "skits": 0.07}[style] + sfx * 0.18
    mix = (mix / (np.abs(mix).max() + 1e-6) * 0.9).astype(np.float32)
    wav = os.path.join(out_dir, name + ".wav")
    import soundfile as sf; sf.write(wav, mix, SR)
    nf = int(total * FPS); hop = SR // FPS
    env = np.array([np.sqrt(np.mean(vo[i * hop:(i + 1) * hop] ** 2)) for i in range(nf)])
    env = np.clip(env / (np.percentile(env[env > 0], 90) + 1e-6 if (env > 0).any() else 1), 0, 1)
    # 2) frames -> ffmpeg
    mp4 = os.path.join(out_dir, name + ".mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", mp4],
                          stdin=subprocess.PIPE)
    bgs = Backgrounds(style, abs(hash(name)) % 1000)
    groups = [(seg, g) for seg in timeline for g in build_groups(seg["words"])]
    spk_col = {"A": (255, 236, 120), "B": (255, 170, 210), "N": (255, 255, 255)}
    for fi in range(nf):
        t = fi / FPS
        seg = next((s for s in timeline if s["t0"] <= t < s["t1"]), timeline[-1])
        s = seg["scene"]; lt = t - seg["t0"]; sd = seg["t1"] - seg["t0"]; amp = env[fi]
        fr = bgs.draw(t, s)
        # camera shake / flash effects
        fx = s.get("fx", "")
        if s.get("scene"):
            for e in scenes.draw_scene(fr, s, lt, sd, t):
                e = dict(e, x=e["x"] / W, y=e["y"] / H, anim="none"); draw_item(fr, e, 1.0, sd, t, style)
        for it in s.get("items", []): draw_item(fr, it, lt, sd, t, style)
        if s.get("kid"):
            draw_kid_scene(fr, s["kid"], lt, t)
        if s.get("bubble") and lt >= s["bubble"].get("delay", 0.3):
            draw_bubble(fr, s["bubble"], lt - s["bubble"].get("delay", 0.3))
        if style == "whatif" and sc.get("host", True):  # host mascot "Blip"
            draw_blob(fr, W * 0.15, H * 0.13, 150, "#38d6c4", s.get("mood", "happy"), amp, (t % 3.7) < 0.12, 0.5, t)
        if style == "skits":
            moods = s.get("mood", {})
            for who, x0, colr, look in (("A", 0.29, "#ffd23f", 1), ("B", 0.71, "#ff7eb6", -1)):
                if who not in s.get("cast", "AB"): continue
                talking = seg["spk"] == who and seg["speech"][0] <= t <= seg["speech"][1]
                bob = math.sin(t * 14) * 10 if talking else math.sin(t * 2 + x0 * 9) * 4
                draw_blob(fr, W * x0, H * 0.53 + bob, 380, colr, moods.get(who, "happy"), amp if talking else 0,
                          ((t + x0) % 4.1) < 0.12, look, t, (amp * 0.5 if talking else 0))
            for it in s.get("props", []): draw_item(fr, it, lt, sd, t, style)
            if s.get("banner"):
                dd = ImageDraw.Draw(fr); f = font(FONT_SANS, 64)
                bb = dd.multiline_textbbox((W / 2, H * 0.14), s["banner"], font=f, anchor="mm", align="center")
                dd.rounded_rectangle((bb[0] - 40, bb[1] - 30, bb[2] + 40, bb[3] + 30), 30, fill=(20, 20, 20))
                dd.multiline_text((W / 2, H * 0.14), s["banner"], font=f, fill="white", anchor="mm", align="center")
        if style == "darkhistory" and s.get("stamp"):
            n_ch = int(clamp(lt / 1.2) * len(s["stamp"]))
            dd = ImageDraw.Draw(fr); f = font(FONT_SERIF, 60)
            dd.text((W / 2, H * 0.13), s["stamp"][:n_ch], font=f, fill=(235, 220, 190), anchor="mm")
            if n_ch == len(s["stamp"]):
                L = f.getlength(s["stamp"]) / 2; dd.line((W / 2 - L, H * 0.13 + 50, W / 2 + L, H * 0.13 + 50), fill=(190, 30, 30), width=6)
        fr = bgs.overlay(fr, t)
        for gseg, g in groups:
            end = g[-1][2] + 0.15
            if g[0][1] <= t < end and gseg is seg:
                draw_caption(fr, g, t, style, spk_col.get(gseg["spk"]) if style == "skits" else None, sc.get("caption_y")); break
        if "flash" in fx and lt < 0.25:
            fr = Image.blend(fr, Image.new("RGB", (W, H), (255, 255, 255) if style != "darkhistory" else (160, 0, 0)), 0.7 * (1 - lt / 0.25))
        if "shake" in fx:
            ox, oy = int(math.sin(t * 60) * 14), int(math.cos(t * 50) * 14)
            fr = fr.transform(fr.size, Image.AFFINE, (1, 0, ox, 0, 1, oy))
        ff.stdin.write(fr.tobytes())
    ff.stdin.close(); ff.wait(); os.remove(wav)
    meta = {k: sc.get(k) for k in ("title", "description", "tags")}
    meta["file"] = mp4; meta["duration"] = round(total, 1)
    json.dump(meta, open(os.path.join(out_dir, name + ".json"), "w"), indent=2)
    print(f"OK {mp4} ({total:.1f}s)")
    return mp4

if __name__ == "__main__":
    render(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
