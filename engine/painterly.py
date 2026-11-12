"""Painterly cinematic 2D: layered parallax scene with depth-of-field, fog, moon glow, god rays,
fireflies, wind-blown character with a glowing lantern. Demo: Leo on a forest hill looking at the Moon.

python engine/painterly.py out.mp4
"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render
from render import W, H, FPS, SR

PW, PH = int(W * 1.25), int(H * 1.12)   # oversized plates for parallax / camera moves
rng = np.random.default_rng(21)

def grad(h, w, top, bot):
    y = np.linspace(0, 1, h)[:, None, None]
    return (np.array(top) * (1 - y) + np.array(bot) * y).repeat(w, 1).astype(np.uint8)

def radial(size, color, power=2.0, alpha=255):
    y, x = np.mgrid[0:size, 0:size].astype(np.float32); c = size / 2
    a = np.clip(1 - np.sqrt((x - c) ** 2 + (y - c) ** 2) / c, 0, 1) ** power * alpha
    rgb = np.empty((size, size, 3), np.float32); rgb[:] = color
    return Image.fromarray(np.dstack([rgb, a]).astype(np.uint8), "RGBA")

def trunk_layer(n, color, wmin, wmax, blur, seed, ytop=-50, sway=0, avoid=None, edges=False):
    r = np.random.default_rng(seed); im = Image.new("RGBA", (PW, PH), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for i in range(n):
        x = r.uniform(-50, PW + 50); w = r.uniform(wmin, wmax); lean = r.uniform(-30, 30)
        if edges: x = r.choice([r.uniform(-120, PW * 0.08), r.uniform(PW * 0.92, PW + 120)])
        if avoid and avoid[0] < x < avoid[1]: continue
        pts = [(x - w / 2, ytop), (x + w / 2, ytop), (x + w / 2 * 1.15 + lean, PH), (x - w / 2 * 1.15 + lean, PH)]
        d.polygon(pts, fill=color)
        for k in range(3):  # branches
            by = r.uniform(PH * 0.1, PH * 0.5); s = r.choice([-1, 1])
            d.polygon([(x, by), (x + s * r.uniform(80, 200), by - r.uniform(60, 140)), (x + s * 10, by + 30)], fill=color)
    return im.filter(ImageFilter.GaussianBlur(blur)) if blur else im

def foliage_layer(color, blur, seed, y0, count, size):
    r = np.random.default_rng(seed); im = Image.new("RGBA", (PW, PH), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for i in range(count):
        x = r.uniform(0, PW); y = y0 + r.uniform(-40, 120); s = r.uniform(size * 0.6, size * 1.3)
        for k in range(7):  # fern / leaf fan
            a = math.radians(-160 + k * 23 + r.uniform(-8, 8)); L = s * r.uniform(0.7, 1.1)
            tx, ty = x + math.cos(a) * L, y + math.sin(a) * L
            nx, ny = -math.sin(a) * s * 0.12, math.cos(a) * s * 0.12
            d.polygon([(x, y), ((x + tx) / 2 + nx, (y + ty) / 2 + ny), (tx, ty), ((x + tx) / 2 - nx, (y + ty) / 2 - ny)], fill=color)
    d.rectangle((0, y0 + 60, PW, PH), fill=color)
    return im.filter(ImageFilter.GaussianBlur(blur)) if blur else im

def hill_layer(color, y0, amp, blur, seed):
    r = np.random.default_rng(seed); im = Image.new("RGBA", (PW, PH), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    ph = r.uniform(0, 6, 3)
    pts = [(x, y0 - amp * (0.6 * math.sin(x / PW * 3 + ph[0]) + 0.4 * math.sin(x / PW * 7 + ph[1]))) for x in range(0, PW + 20, 20)]
    d.polygon(pts + [(PW, PH), (0, PH)], fill=color)
    return im.filter(ImageFilter.GaussianBlur(blur)) if blur else im

def fog_band(y, h, color, alpha):
    a = np.zeros((PH, PW), np.float32); yy = np.arange(PH)[:, None]
    a[:] = np.exp(-((yy - y) / h) ** 2) * alpha
    rgb = np.empty((PH, PW, 3), np.float32); rgb[:] = color
    return Image.fromarray(np.dstack([rgb, a]).astype(np.uint8), "RGBA")

# ------------------------------------------------------------------ character (painterly Leo)
SKIN = (238, 214, 192); HAIR = (40, 26, 22); CAPE = (236, 138, 36); CAPE_DK = (176, 88, 26); CAPE_LT = (255, 186, 80)

def draw_leo(t, h=440, look_up=0.0):
    U = h * 2 / 100; S = int(110 * U); im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cx, foot = S * 0.55, S - 4 * U
    wind = lambda k, f=1.0: math.sin(t * 3.2 * f + k)
    # legs
    for s in (-1, 1):
        d.line((cx + s * 4 * U, foot - 22 * U, cx + s * 5 * U, foot - 1 * U), fill=SKIN, width=int(3.2 * U))
        d.ellipse((cx + s * 5 * U - 3 * U, foot - 3 * U, cx + s * 5 * U + 3 * U, foot + 1 * U), fill=(50, 34, 30))
    # cape: shoulders -> wavy hem blown to the left
    sh_y = foot - 60 * U; hem_y = foot - 20 * U
    pts = [(cx - 9 * U, sh_y), (cx + 9 * U, sh_y)]
    pts.append((cx + 20 * U, hem_y - 2 * U + wind(0) * U))
    for i in range(9):
        k = i / 8; x = cx + 20 * U - k * 62 * U - (k ** 1.6) * 14 * U * (0.8 + 0.2 * wind(1.3))
        y = hem_y + (math.sin(k * 9 - t * 6) * 3.2 * U) - k * k * 14 * U + wind(k * 3) * 2 * U * k
        pts.append((x, y))
    pts.append((cx - 13 * U, sh_y + 6 * U))
    d.polygon(pts, fill=CAPE)
    d.polygon([(cx + 2 * U, sh_y + 2 * U), (cx + 9 * U, sh_y), (cx + 20 * U, hem_y - 2 * U + wind(0) * U), (cx + 6 * U, hem_y + 1 * U)], fill=CAPE_DK)
    for i in range(3):  # fabric folds
        x0 = cx - 4 * U - i * 9 * U
        d.line((x0 + 6 * U, sh_y + 8 * U, x0 - 6 * U - i * 3 * U, hem_y - i * 4 * U + wind(i) * U), fill=CAPE_DK, width=int(1.4 * U))
    # arm holding the lantern out to the left
    hx, hy = cx - 24 * U, sh_y + 16 * U
    d.line((cx - 7 * U, sh_y + 6 * U, cx - 16 * U, sh_y + 14 * U, hx, hy), fill=CAPE, width=int(5 * U), joint="curve")
    d.ellipse((hx - 2.4 * U, hy - 2.4 * U, hx + 2.4 * U, hy + 2.4 * U), fill=SKIN)
    sw = math.sin(t * 2.4) * 2 * U
    lx, ly = hx + sw * 0.4, hy + 9 * U
    d.line((hx, hy, lx, ly - 4 * U), fill=(60, 40, 30), width=int(0.9 * U))
    d.rounded_rectangle((lx - 3.5 * U, ly - 4 * U, lx + 3.5 * U, ly + 5 * U), int(1.5 * U), fill=(255, 214, 120), outline=(70, 46, 30), width=int(0.9 * U))
    d.rectangle((lx - 4 * U, ly - 5 * U, lx + 4 * U, ly - 3.6 * U), fill=(70, 46, 30))
    # head (tilts up toward the moon)
    hcx, hcy = cx + 1 * U, sh_y - 11 * U
    hd = Image.new("RGBA", (int(40 * U), int(40 * U)), (0, 0, 0, 0)); hdd = ImageDraw.Draw(hd); c = 20 * U
    # wind-blown curls behind
    for i in range(7):
        k = i / 6; bx = c + 6 * U - k * 26 * U - wind(k * 4, 1.4) * 2.5 * U * k; by = c - 6 * U + k * 6 * U + wind(k * 5) * 1.5 * U
        r = (7 - 3 * k) * U; hdd.ellipse((bx - r, by - r, bx + r, by + r), fill=HAIR)
    hdd.ellipse((c - 11 * U, c - 12 * U, c + 11 * U, c + 12 * U), fill=SKIN)
    for i in range(8):  # curly top
        a = math.radians(170 + i * 24); r = 5.5 * U
        bx, by = c + math.cos(a) * 11 * U, c + math.sin(a) * 11.5 * U - 1 * U
        hdd.ellipse((bx - r, by - r, bx + r, by + r), fill=HAIR)
    ey = c + 1 * U - look_up * 1.5 * U
    for s in (-1, 1):
        ex = c + s * 4.4 * U + 1 * U + look_up * 1.8 * U
        hdd.ellipse((ex - 1.3 * U, ey - 1.7 * U, ex + 1.3 * U, ey + 1.7 * U), fill=(30, 20, 20))
        hdd.ellipse((ex - 0.6 * U + 0.4 * U, ey - 1.2 * U, ex + 0.1 * U + 0.4 * U, ey - 0.4 * U), fill=(255, 255, 255))
        hdd.ellipse((ex - 2.4 * U, ey + 3 * U, ex + 1.6 * U, ey + 5 * U), fill=(240, 150, 140))
    hdd.ellipse((c - 1.2 * U + 1 * U, c + 6.5 * U, c + 1.2 * U + 1 * U, c + 8.5 * U), fill=(150, 60, 60))
    hd = hd.rotate(10 * look_up + math.sin(t * 1.1) * 2, resample=Image.BICUBIC, center=(c, c + 10 * U))
    im.alpha_composite(hd, (int(hcx - c), int(hcy - c)))
    d.ellipse((cx - 7 * U, sh_y - 3 * U, cx + 7 * U, sh_y + 4 * U), fill=CAPE_LT)  # collar
    im = im.resize((S // 2, S // 2), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.6))
    return im, (lx / 2, ly / 2), (cx / 2, foot / 2)

# ------------------------------------------------------------------ build plates once
def build_plates():
    sky = Image.fromarray(grad(PH, PW, (10, 30, 48), (22, 62, 74)), "RGB").convert("RGBA")
    d = ImageDraw.Draw(sky)
    for _ in range(260):
        x, y, b = rng.uniform(0, PW), rng.uniform(0, PH * 0.5), int(rng.uniform(80, 220))
        r = rng.choice([1, 1, 2]); d.ellipse((x - r, y - r, x + r, y + r), fill=(b, b, min(255, b + 20), 255))
    mx, my = PW * 0.66, PH * 0.24
    for size, col, p, a in ((1300, (120, 190, 200), 2.2, 120), (600, (200, 230, 220), 2.0, 160), (330, (240, 250, 235), 1.2, 255)):
        g = radial(size, col, p, a); sky.alpha_composite(g, (int(mx - size / 2), int(my - size / 2)))
    moon = Image.new("RGBA", (300, 300), (0, 0, 0, 0)); md = ImageDraw.Draw(moon)
    md.ellipse((40, 40, 260, 260), fill=(250, 248, 232, 255))
    for ox, oy, r in ((110, 120, 26), (175, 165, 18), (140, 205, 14), (190, 100, 12)):
        md.ellipse((ox - r, oy - r, ox + r, oy + r), fill=(226, 224, 205, 255))
    sky.alpha_composite(moon.filter(ImageFilter.GaussianBlur(1.2)), (int(mx - 150), int(my - 150)))
    rays = Image.new("L", (PW, PH), 0); rd = ImageDraw.Draw(rays)
    for i in range(6):
        a = math.radians(105 + i * 9); L = PH * 1.2; w = 40 + i * 15
        rd.polygon([(mx, my), (mx + math.cos(a - 0.03) * L, my + math.sin(a - 0.03) * L), (mx + math.cos(a + 0.03) * L, my + math.sin(a + 0.03) * L)], fill=40)
    rays = rays.filter(ImageFilter.GaussianBlur(30))
    rays = Image.merge("RGBA", (*[Image.new("L", (PW, PH), 230)] * 3, rays))
    plates = {
        "sky": sky,
        "far_hills": hill_layer((24, 66, 78, 255), PH * 0.52, 90, 6, 1),
        "far_trees": trunk_layer(22, (20, 52, 64, 255), 30, 60, 8, 2, avoid=(PW * 0.42, PW * 0.95)),
        "fog1": fog_band(PH * 0.60, 180, (90, 150, 160), 90),
        "mid_trees": trunk_layer(12, (12, 34, 44, 255), 70, 130, 3, 3, avoid=(PW * 0.38, PW * 0.98)),
        "fog2": fog_band(PH * 0.72, 120, (70, 130, 140), 70),
        "hill": hill_layer((8, 22, 30, 255), PH * 0.70, 40, 1, 4),
        "near_trees": trunk_layer(3, (4, 12, 18, 255), 160, 220, 14, 5, edges=True),
        "fg": foliage_layer((3, 10, 14, 255), 16, 6, PH * 0.86, 9, 340),
    }
    return plates, rays

DEPTH = {"sky": 0.05, "far_hills": 0.12, "far_trees": 0.2, "fog1": 0.25, "mid_trees": 0.4, "fog2": 0.5,
         "hill": 0.55, "near_trees": 0.9, "fg": 1.2}

def frame(plates, rays, t, total, fire, cam):
    z, px = cam
    fr = Image.new("RGBA", (PW, PH))
    char, lantern, feet = draw_leo(t, 540, look_up=min(1, t / 3))
    for name in DEPTH:
        dx = int(px * DEPTH[name] * 120)
        lay = plates[name]
        if dx: lay = ImageChops.offset(lay, dx, 0)
        fr.alpha_composite(lay)
        if name == "fog2":
            fr.alpha_composite(rays)
        if name == "hill":
            cx, cy = PW * 0.40 + int(px * DEPTH["hill"] * 120), PH * 0.70 + 10
            ox, oy = int(cx - feet[0]), int(cy - feet[1])
            lx, ly = ox + lantern[0], oy + lantern[1]
            fl = 0.85 + 0.15 * math.sin(t * 11) * math.sin(t * 7.3)
            for size, col, a in ((1300, (255, 140, 40), int(85 * fl)), (520, (255, 185, 90), int(150 * fl))):
                g = radial(size, col, 2.0, a); fr.alpha_composite(g, (int(lx - size / 2), int(ly - size / 2)))
            fr.alpha_composite(char, (ox, oy))
            g = radial(90, (255, 240, 180), 1.5, int(255 * fl)); fr.alpha_composite(g, (int(lx - 45), int(ly - 45)))
            for f in fire:  # fireflies + drifting embers
                fx = (f[0] * PW + math.sin(t * f[2] + f[3]) * 60 + t * 15) % PW
                fy = f[1] * PH + math.cos(t * f[2] * 0.8 + f[3]) * 50
                tw = 0.5 + 0.5 * math.sin(t * 4 + f[3] * 3)
                g = radial(40, (255, 220, 120), 2, int(220 * tw)); fr.alpha_composite(g, (int(fx - 20), int(fy - 20)))
    # camera crop (slow push-in)
    cw, ch = W / z * (PW / W) / 1.25 * 1.25, H / z
    cw = PW / 1.25 / z * 1.0; ch = PH / 1.12 / z
    cx, cy = PW / 2, PH * 0.5
    out = fr.convert("RGB").resize((W, H), Image.BICUBIC, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))
    return out

def grade(fr, t):
    a = np.asarray(fr).astype(np.float32) / 255
    y, x = np.ogrid[0:H, 0:W]
    v = np.clip(1 - 0.55 * (((x - W / 2) / (W * 0.75)) ** 2 + ((y - H * 0.5) / (H * 0.6)) ** 2), 0.35, 1)[..., None]
    a = a * v
    g = np.random.default_rng(int(t * 24)).normal(0, 0.018, (H // 2, W // 2, 1)).repeat(2, 0).repeat(2, 1)
    return Image.fromarray((np.clip(a + g, 0, 1) * 255).astype(np.uint8))

def main(out):
    lines = ["Leo had one question he just couldn't stop asking.",
             "What would happen... if the Moon disappeared?"]
    voice, speed = render.CHANNELS["whatif"]["voices"]["N"]
    t = 0.8; parts, words = [], []
    for ln in lines:
        a = render.tts(ln, voice, speed); parts.append((t, a)); words += render.word_times(ln, t, len(a) / SR); t += len(a) / SR + 0.6
    total = max(t + 1.0, 9.0); n = int(total * SR)
    vo = np.zeros(n, np.float32)
    for t0, a in parts: vo[int(t0 * SR):int(t0 * SR) + len(a)] += a
    mix = vo + render.synth_music("whatif", n) * 0.10; mix = (mix / np.abs(mix).max() * 0.9).astype(np.float32)
    import soundfile as sf; wav = out[:-4] + ".wav"; sf.write(wav, mix, SR)
    plates, rays = build_plates()
    fire = rng.uniform(0, 1, (24, 4)); fire[:, 1] = 0.45 + fire[:, 1] * 0.4; fire[:, 2] = 0.5 + fire[:, 2]; fire[:, 3] *= 10
    groups = render.build_groups(words)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-i", wav, "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                           "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for fi in range(int(total * FPS)):
        t = fi / FPS; k = t / total
        z = 1.0 + 0.10 * (k * k * (3 - 2 * k)); px = -0.6 + 1.2 * k
        fr = grade(frame(plates, rays, t, total, fire, (z, px)), t)
        for g in groups:
            if g[0][1] <= t < g[-1][2] + 0.15: render.draw_caption(fr, g, t, "whatif", None, 0.80); break
        if t < 0.8: fr = Image.blend(Image.new("RGB", (W, H)), fr, t / 0.8)
        ff.stdin.write(fr.tobytes())
    ff.stdin.close(); ff.wait(); os.remove(wav); print("OK", out, round(total, 1))

if __name__ == "__main__":
    main(sys.argv[1])
