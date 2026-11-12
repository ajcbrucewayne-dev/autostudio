"""Style reel: the same moment ("the Moon pulls the ocean") in 8 animation styles. Output: out/style_reel.mp4"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render, scenes
from render import W, H, FPS, font, FONT_SANS, emoji_img, paste_center, hexrgb, ease_back, ease_out

SEC = 5.0
tide = lambda t: 0.5 + 0.5 * math.sin(t * 1.7 - 1.6)

def poly_partial(d, pts, frac, fill, width):
    n = max(2, int(len(pts) * max(0.0, min(1.0, frac))))
    if frac > 0: d.line(pts[:n], fill=fill, width=width, joint="curve")
    return pts[n - 1]

def circle_pts(cx, cy, r, n=90, start=-90):
    return [(cx + r * math.cos(math.radians(start + 360 * i / (n - 1))), cy + r * math.sin(math.radians(start + 360 * i / (n - 1)))) for i in range(n)]

# 1 flat vector ------------------------------------------------------------
def s_flat(t):
    fr = Image.new("RGB", (W, H))
    ex = scenes.draw_scene(fr, {"scene": "beach", "p": {"amp": 1, "gauge": 0, "speed": 1.7}}, t, SEC, t)
    for e in ex: render.draw_item(fr, dict(e, x=e["x"] / W, y=e["y"] / H, anim="none"), 1, SEC, t, "whatif")
    return fr

# 2 whiteboard doodle -------------------------------------------------------
def s_whiteboard(t):
    fr = Image.new("RGB", (W, H), (250, 250, 246)); d = ImageDraw.Draw(fr)
    ex, ey, er = W * 0.42, H * 0.38, 190
    ang = max(0, t - 2.6) * 1.2
    mx, my = ex + 360 * math.cos(ang - 0.3), ey + 360 * math.sin(ang - 0.3)
    pen = None
    pen = poly_partial(d, circle_pts(ex, ey, er), t / 0.9, (20, 20, 20), 9) or pen
    if t > 0.9:
        cont = [(ex - 90 + 40 * math.sin(i / 3), ey - 80 + i * 9) for i in range(18)]
        pen = poly_partial(d, cont, (t - 0.9) / 0.5, (40, 140, 60), 9)
    if t > 1.4:
        pen = poly_partial(d, circle_pts(mx, my, 60, 50), (t - 1.4) / 0.6, (20, 20, 20), 8)
    if t > 2.0:
        k = min(1, (t - 2.0) / 0.6); a = math.atan2(my - ey, mx - ex)
        bulge = [(ex + (er + 30 + 45 * math.cos(2 * (math.radians(i * 4) - a)) ** 2) * math.cos(math.radians(i * 4)),
                  ey + (er + 30 + 45 * math.cos(2 * (math.radians(i * 4) - a)) ** 2) * math.sin(math.radians(i * 4))) for i in range(91)]
        pen = poly_partial(d, bulge, k, (40, 110, 230), 8)
        if k >= 1:
            sx, sy = mx - 90 * math.cos(a), my - 90 * math.sin(a); tx, ty = ex + 260 * math.cos(a), ey + 260 * math.sin(a)
            d.line((sx, sy, tx, ty), fill=(220, 50, 50), width=8)
            for s in (-0.5, 0.5):
                d.line((tx, ty, tx + 40 * math.cos(a + s), ty + 40 * math.sin(a + s)), fill=(220, 50, 50), width=8)
            d.text((W * 0.5, H * 0.13), "GRAVITY PULLS\nTHE OCEAN!", font=font(FONT_SANS, 72), fill=(20, 20, 20), anchor="mm", align="center")
    if pen and t < 2.6: paste_center(fr, emoji_img("✍️", 130), pen[0] + 40, pen[1] + 50)
    return fr

# 3 stick figure ------------------------------------------------------------
def stick(d, x, y, t, mood):
    jump = abs(math.sin(t * 10)) * 50 if mood == "panic" else 0; y -= jump
    d.ellipse((x - 42, y - 300, x + 42, y - 216), outline=(0, 0, 0), width=10, fill="white")
    d.line((x, y - 216, x, y - 100), fill=(0, 0, 0), width=10)
    sw = math.sin(t * 12) * 40 if mood == "panic" else 0
    arms = (-70, -260 + sw, 70, -260 - sw) if mood == "panic" else (-60, -130, 60, -130)
    d.line((x + arms[0], y + arms[1], x, y - 190, x + arms[2], y + arms[3]), fill=(0, 0, 0), width=10, joint="curve")
    d.line((x - 45, y, x, y - 100, x + 45, y), fill=(0, 0, 0), width=10, joint="curve")
    if mood == "panic": d.ellipse((x - 15, y - 262, x + 15, y - 232), fill=(0, 0, 0))
    else: d.arc((x - 20, y - 268, x + 20, y - 238), 20, 160, fill=(0, 0, 0), width=6)

def s_stick(t):
    fr = Image.new("RGB", (W, H), (205, 232, 250)); d = ImageDraw.Draw(fr)
    gy = H * 0.56
    d.rectangle((0, gy, W, H), fill=(240, 215, 160))
    render.draw_item(fr, {"emoji": "🌕", "x": 0.75, "y": 0.13, "s": 150, "anim": "none"}, 1, SEC, t, "skits")
    edge = W * (0.05 + 0.75 * ease_out(t / 3.6))
    pts = [(x, gy - 14 + 10 * math.sin(x / 40 + t * 6)) for x in range(0, int(edge) + 1, 20)]
    d.polygon(pts + [(edge, H), (0, H)], fill=(70, 150, 230)); d.line(pts, fill=(255, 255, 255), width=8)
    mood = "panic" if edge > W * 0.58 else "calm"
    stick(d, W * 0.66, gy + 20, t, mood)
    if mood == "panic": render.draw_item(fr, {"text": "AAAH!", "x": 0.66, "y": 0.30, "size": 90, "anim": "shake"}, 1, SEC, t, "skits")
    return fr

# 4 paper cutout ------------------------------------------------------------
_paper = None
def paper_tex():
    global _paper
    if _paper is None:
        n = np.random.default_rng(2).normal(0, 1, (H // 4, W // 4))
        _paper = Image.fromarray(((n - n.min()) / (n.max() - n.min()) * 255).astype(np.uint8)).resize((W, H)).filter(ImageFilter.GaussianBlur(1))
    return _paper

def s_paper(t):
    tb = math.floor(t * 12) / 12  # 12 fps "stop motion"
    rng = np.random.default_rng(int(tb * 12))
    j = lambda: rng.uniform(-4, 4)
    fr = Image.new("RGB", (W, H), (45, 55, 110)); d = ImageDraw.Draw(fr)
    def cut(shape, pts, col):
        sh = [(x + 12, y + 14) for x, y in pts]
        getattr(d, shape)(sh, fill=(15, 15, 30)); getattr(d, shape)(pts, fill=col)
    mx, my = W * (0.3 + 0.4 * tb / SEC), H * 0.16
    cut("ellipse", [(mx - 90 + j(), my - 90 + j()), (mx + 90 + j(), my + 90 + j())], (245, 235, 200))
    lvl = tide(tb)
    for k, col in enumerate(((60, 120, 200), (40, 95, 180), (25, 70, 150))):
        base = H * (0.50 - 0.10 * lvl) + k * 110
        pts = [(x + j(), base + 30 * math.sin(x / 120 + k + tb * 2) + j()) for x in range(-40, W + 80, 60)]
        cut("polygon", pts + [(W + 40, H), (-40, H)], col)
    cut("polygon", [(W * 0.55 + j(), H), (W + 20, H * 0.62 + j()), (W + 20, H)], (215, 180, 120))
    tex = paper_tex(); fr = Image.blend(fr, Image.merge("RGB", (tex, tex, tex)), 0.10)
    render.draw_item(fr, {"emoji": "⛵", "x": 0.45, "y": (H * (0.47 - 0.10 * lvl) - 60) / H, "s": 170, "anim": "none"}, 1, SEC, t, "x")
    return fr

# 5 silhouette --------------------------------------------------------------
def s_silhouette(t):
    fr = Image.new("RGB", (W, H)); d = ImageDraw.Draw(fr)
    for i in range(96):
        c = scenes.mix((60, 20, 80), (255, 140, 60), i / 95)
        d.rectangle((0, H * 0.7 * i / 96, W, H * 0.7 * (i + 1) / 96 + 1), fill=c)
    d.rectangle((0, H * 0.7, W, H), fill=(255, 150, 60))
    d.ellipse((W * 0.5 - 200, H * 0.30 - 200, W * 0.5 + 200, H * 0.30 + 200), fill=(255, 230, 170))
    lvl = tide(t); yw = H * (0.58 - 0.12 * lvl)
    pts = [(x, yw + 22 * math.sin(x / 90 + t * 3)) for x in range(0, W + 30, 30)]
    d.polygon(pts + [(W, H), (0, H)], fill=(10, 8, 15))
    d.polygon([(W * 0.72, H), (W * 0.78, H * 0.30), (W * 0.84, H * 0.30), (W * 0.90, H)], fill=(10, 8, 15))
    d.rectangle((W * 0.76, H * 0.26, W * 0.86, H * 0.30), fill=(10, 8, 15))
    if int(t * 2) % 2 == 0: d.polygon([(W * 0.81, H * 0.28), (W * 0.40, H * 0.22), (W * 0.40, H * 0.34)], fill=(255, 240, 200))
    for i in range(4):
        bx, by = (t * 90 + i * 140) % (W + 200) - 100, H * 0.18 + i * 40; f = math.sin(t * 9 + i) * 18
        d.line((bx - 30, by + f, bx, by, bx + 30, by + f), fill=(10, 8, 15), width=7)
    return fr

# 6 pixel art ---------------------------------------------------------------
def s_pixel(t):
    w, h = 135, 240; im = Image.new("RGB", (w, h), (20, 18, 50)); d = ImageDraw.Draw(im)
    rng = np.random.default_rng(4)
    for i in range(40):
        x, y = rng.integers(0, w), rng.integers(0, 120)
        if (i + int(t * 4)) % 5: d.point((x, y), fill=(255, 255, 220))
    mx = int(20 + 90 * t / SEC); d.ellipse((mx, 20, mx + 22, 42), fill=(240, 240, 200)); d.ellipse((mx + 5, 26, mx + 9, 30), fill=(200, 200, 170))
    lvl = tide(t); yw = int(150 - 22 * lvl)
    for x in range(w):
        top = yw + (1 if (x // 6 + int(t * 6)) % 2 else 0)
        d.line((x, top, x, h), fill=(40, 90, 200)); d.point((x, top), fill=(200, 230, 255))
    for x in range(w):
        sy = int(200 - (x - 50) * 0.9) if x > 50 else h
        d.line((x, max(sy, 0), x, h), fill=(230, 190, 110))
    d.rectangle((100, 92, 103, 120), fill=(120, 70, 30)); d.rectangle((94, 88, 110, 92), fill=(40, 160, 60))
    return im.resize((W, H), Image.NEAREST)

# 7 infographic -------------------------------------------------------------
def s_info(t):
    fr = Image.new("RGB", (W, H), (16, 20, 34)); d = ImageDraw.Draw(fr)
    d.text((W / 2, H * 0.09), "TIDE HEIGHT", font=font(FONT_SANS, 80), fill="white", anchor="mm")
    x0, x1, y0, y1 = 110, W - 90, H * 0.16, H * 0.40
    for i in range(5): d.line((x0, y0 + (y1 - y0) * i / 4, x1, y0 + (y1 - y0) * i / 4), fill=(45, 52, 75), width=2)
    k = min(1, t / 3.5); n = int(200 * k)
    curve = lambda amp: [(x0 + (x1 - x0) * i / 199, (y0 + y1) / 2 - (y1 - y0) * 0.42 * amp * math.sin(i / 199 * 4 * math.pi)) for i in range(200)]
    for amp, col in ((1.0, (90, 200, 255)), (0.33, (255, 90, 90))):
        c = curve(amp)
        if n > 1: d.line(c[:n], fill=col, width=8, joint="curve"); d.ellipse((c[n - 1][0] - 14, c[n - 1][1] - 14, c[n - 1][0] + 14, c[n - 1][1] + 14), fill=col)
    f = font(FONT_SANS, 48)
    for i, (lab, v, col) in enumerate((("WITH MOON", 1.0, (90, 200, 255)), ("NO MOON", 0.33, (255, 90, 90)))):
        by = H * 0.47 + i * 120; p = ease_out((t - 1 - i * 0.4) / 1.2) * v
        d.text((x0, by), lab, font=f, fill="white", anchor="lm")
        d.rounded_rectangle((x0 + 330, by - 32, x0 + 330 + 440 * max(p, 0.02), by + 32), 16, fill=col)
        d.text((x0 + 350 + 440 * max(p, 0.02), by), f"{int(p * 100)}%", font=f, fill="white", anchor="lm")
    return fr

# 8 kinetic typography ------------------------------------------------------
def s_kinetic(t):
    words = [("THE", "#ffd600", "#1b1b2f"), ("MOON", "#ffffff", "#5b2ecc"), ("PULLS", "#1b1b2f", "#ffd600"),
             ("THE OCEAN", "#ffffff", "#1d6fe0"), ("UPWARD!", "#ffffff", "#e0324b")]
    i = min(len(words) - 1, int(t / (SEC / len(words)))); lt = t - i * SEC / len(words)
    wd, fg, bg = words[i]
    fr = Image.new("RGB", (W, H), hexrgb(bg))
    size = int(230 * max(0.05, ease_back(lt / 0.3))) if wd != "THE OCEAN" else int(170 * max(0.05, ease_back(lt / 0.3)))
    lay = Image.new("RGBA", (W * 2, 600), (0, 0, 0, 0))
    ImageDraw.Draw(lay).text((W, 300), wd, font=font(FONT_SANS, max(10, size)), fill=fg, anchor="mm")
    rot = (1 - ease_out(lt / 0.3)) * (-25 if i % 2 else 25)
    lay = lay.rotate(rot, resample=Image.BICUBIC)
    dy = -lt * 60 if wd == "UPWARD!" else 0
    paste_center(fr, lay, W / 2, H * 0.38 + dy)
    if wd == "THE OCEAN":
        d = ImageDraw.Draw(fr); pts = [(x, H * 0.52 + 20 * math.sin(x / 60 + t * 8)) for x in range(0, W + 20, 20)]
        d.polygon(pts + [(W, H), (0, H)], fill=(255, 255, 255))
    return fr

STYLES = [("FLAT VECTOR", "clean shapes · current What If? style", s_flat),
          ("WHITEBOARD", "hand-drawn explainer · great for science", s_whiteboard),
          ("STICK FIGURE", "simple + funny · great for skits", s_stick),
          ("PAPER CUTOUT", "stop-motion crafts look · cozy stories", s_paper),
          ("SILHOUETTE", "moody shadows · great for dark history", s_silhouette),
          ("PIXEL ART", "retro video-game look · gaming/nostalgia", s_pixel),
          ("INFOGRAPHIC", "charts + data · facts & comparisons", s_info),
          ("KINETIC TEXT", "animated words · hooks & quotes", s_kinetic)]

def label(fr, i, name, sub):
    d = ImageDraw.Draw(fr)
    d.rounded_rectangle((60, H * 0.70, W - 60, H * 0.80), 30, fill=(0, 0, 0))
    d.text((W / 2, H * 0.73), f"STYLE {i + 1}: {name}", font=font(FONT_SANS, 70), fill=(255, 214, 0), anchor="mm")
    d.text((W / 2, H * 0.775), sub, font=font(FONT_SANS, 40), fill="white", anchor="mm")

if __name__ == "__main__":
    out = os.path.join(render.ROOT, "out", "style_reel.mp4"); sheet = []
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-shortest", "-c:v", "libx264", "-crf", "21",
                           "-pix_fmt", "yuv420p", "-c:a", "aac", out], stdin=subprocess.PIPE)
    for i, (name, sub, fn) in enumerate(STYLES):
        for f in range(int(SEC * FPS)):
            t = f / FPS; fr = fn(t).convert("RGB"); label(fr, i, name, sub)
            if f == int(3.4 * FPS): sheet.append(fr.resize((270, 480)))
            ff.stdin.write(fr.tobytes())
    ff.stdin.close(); ff.wait()
    g = Image.new("RGB", (270 * 4, 480 * 2), "white")
    for i, im in enumerate(sheet): g.paste(im, (270 * (i % 4), 480 * (i // 4)))
    g.save(os.path.join(render.ROOT, "out", "style_sheet.png")); print("OK", out)
