"""Style tests round 2: the same moment (a fish chasing a glittering sea sapphire) in Paper cut-out and Neon glow.
python3 engine/style_tests2.py out_dir
"""
import math, os, sys
import numpy as np
import cairo
from PIL import Image, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cartoon import rgb, path, blob, mix, W, H, Post, glow

def surf(): S = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); return S, cairo.Context(S)
def arr(S): S.flush(); return np.ndarray((H, W, 4), np.uint8, S.get_data()).copy()

def fish_shape(c, x, y, s, flip=False):
    """returns nothing; adds fish body path (big hungry fish facing right)"""
    c.save(); c.translate(x, y); c.scale(-s if flip else s, s)
    c.move_to(-260, 0); c.curve_to(-180, -170, 120, -190, 230, -30); c.curve_to(250, 0, 250, 20, 230, 40)
    c.curve_to(120, 190, -180, 170, -260, 0); c.close_path(); c.restore()

def tail_shape(c, x, y, s): c.save(); c.translate(x, y); c.scale(s, s); c.move_to(-240, 0); c.line_to(-400, -150); c.line_to(-360, 0); c.line_to(-400, 150); c.close_path(); c.restore()

# ---------------------------------------------------------------- PAPER CUT-OUT
def paper_layer(base, draw, shadow=18, blur=10, grain=None):
    """draw a paper layer with a soft drop shadow onto base (float RGB array)"""
    S, c = surf(); draw(c); a = arr(S); alpha = a[..., 3:4].astype(np.float32) / 255
    sh = Image.fromarray(a[..., 3]).filter(ImageFilter.GaussianBlur(blur)); sh = np.roll(np.roll(np.asarray(sh), shadow, 0), shadow // 2, 1)[..., None] / 255.0
    base *= (1 - 0.45 * sh)
    rgbv = a[..., 2::-1].astype(np.float32)
    if grain is not None: rgbv = rgbv * (1 + grain[..., None])
    return base * (1 - alpha) + rgbv * alpha * (alpha > 0) / np.maximum(alpha, 1e-6) * alpha

def paper(out):
    rng = np.random.default_rng(2)
    grain = (np.asarray(Image.fromarray(rng.integers(0, 255, (H // 3, W // 3), dtype=np.uint8)).resize((W, H)).filter(ImageFilter.GaussianBlur(1))).astype(np.float32) / 255 - 0.5) * 0.10
    base = np.zeros((H, W, 3), np.float32); base[:] = (20, 60, 120)
    bands = ["#2d7fc1", "#2468a8", "#1b558f", "#134478", "#0d3462"]
    for i, col in enumerate(bands):   # torn-edge depth bands
        y0 = 260 + i * 330
        def d(c, y0=y0, col=col, i=i):
            pts = [(x, y0 + 30 * math.sin(x * 0.01 + i) + rng.uniform(-6, 6)) for x in range(-20, W + 40, 18)]
            c.new_path(); path(c, pts + [(W + 40, H + 40), (-20, H + 40)]); c.set_source_rgb(*rgb(col)); c.fill()
        base = paper_layer(base, d, 14, 9, grain)
    def kelp(c):
        for x, h, col in ((120, 900, "#2f9e6a"), (230, 700, "#3bb57a"), (930, 1000, "#2f9e6a"), (1010, 760, "#46c487")):
            c.new_path(); c.move_to(x - 30, H + 20)
            for k in range(12): c.line_to(x + 40 * math.sin(k * 0.9), H - k * h / 12)
            for k in range(12, -1, -1): c.line_to(x + 40 * math.sin(k * 0.9) + 50, H - k * h / 12)
            c.close_path(); c.set_source_rgb(*rgb(col)); c.fill()
    base = paper_layer(base, kelp, 16, 10, grain)
    def fishd(c):
        tail_shape(c, 420, 820, 1.0); c.set_source_rgb(*rgb("#e8562c")); c.fill()
        fish_shape(c, 420, 820, 1.0); c.set_source_rgb(*rgb("#ff7a3a")); c.fill()
        for k in range(4):  # paper scales
            c.new_path(); c.arc(330 - k * 90, 820, 70, -1.0, 1.0); c.set_source_rgb(*rgb("#f26a30")); c.set_line_width(14); c.stroke()
        c.new_path(); c.arc(560, 760, 48, 0, 2 * math.pi); c.set_source_rgb(1, 1, 1); c.fill()
        c.new_path(); c.arc(575, 760, 24, 0, 2 * math.pi); c.set_source_rgb(0.1, 0.1, 0.15); c.fill()
        c.new_path(); c.move_to(640, 840); c.curve_to(600, 880, 560, 880, 530, 860); c.set_source_rgb(0.4, 0.05, 0.05); c.set_line_width(14); c.stroke()
    base = paper_layer(base, fishd, 22, 12, grain)
    def sapph(c):
        cx, cy = 860, 640
        for i in range(14):
            a = i * 0.45; r = 30 + (i % 4) * 22
            k = [rgb("#7ad7ff"), rgb("#b18cff"), rgb("#ffd84a"), rgb("#64f0d8")][i % 4]
            c.new_path(); hexa = [(cx + math.cos(a) * r * 0.9 + 26 * math.cos(math.pi / 3 * j), cy + math.sin(a) * r * 1.2 + 26 * math.sin(math.pi / 3 * j)) for j in range(6)]
            path(c, hexa); c.set_source_rgb(*k); c.fill()
        for j in range(6):  # paper sparkles
            a = j * 1.05; c.new_path(); c.move_to(cx + math.cos(a) * 150, cy + math.sin(a) * 150)
            for q in range(8): rr = 34 if q % 2 == 0 else 12; c.line_to(cx + math.cos(a) * 150 + math.cos(q * math.pi / 4) * rr, cy + math.sin(a) * 150 + math.sin(q * math.pi / 4) * rr)
            c.close_path(); c.set_source_rgb(1, 0.97, 0.8); c.fill()
    base = paper_layer(base, sapph, 18, 10, grain)
    def bubbles(c):
        for i in range(10):
            c.new_path(); c.arc(640 + i * 30, 700 - i * 45, 10 + i % 3 * 6, 0, 2 * math.pi); c.set_source_rgb(0.85, 0.95, 1); c.fill()
    base = paper_layer(base, bubbles, 8, 5, grain)
    Image.fromarray(base.clip(0, 255).astype(np.uint8)).save(out)

# ---------------------------------------------------------------- NEON / BIOLUMINESCENT
def neon_stroke(c, draw, col, w=8):
    for lw, a in ((w * 7, 0.06), (w * 4, 0.12), (w * 2, 0.35), (w, 1.0)):
        draw(c); c.set_source_rgba(*col, a); c.set_line_width(lw); c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND); c.stroke()
    draw(c); c.set_source_rgba(1, 1, 1, 0.8); c.set_line_width(max(2, w * 0.35)); c.stroke()

def neon(out):
    S = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); c = cairo.Context(S)
    g = cairo.RadialGradient(W / 2, H * 0.45, 50, W / 2, H * 0.45, H * 0.8); g.add_color_stop_rgb(0, 0.03, 0.06, 0.16); g.add_color_stop_rgb(1, 0.0, 0.0, 0.02); c.set_source(g); c.paint()
    rng = np.random.default_rng(5)
    for i in range(160):  # plankton specks
        x, y = rng.uniform(0, W), rng.uniform(0, H); k = [(0.3, 0.9, 1), (0.6, 0.4, 1), (0.3, 1, 0.7)][i % 3]
        glow(c, x, y, rng.uniform(6, 16), k, 0.6); c.new_path(); c.arc(x, y, 1.6, 0, 2 * math.pi); c.set_source_rgb(1, 1, 1); c.fill()
    for x, h in ((110, 800), (960, 950)):   # glowing kelp
        neon_stroke(c, lambda k, x=x, h=h: (k.new_path(), k.move_to(x, H), [k.line_to(x + 45 * math.sin(q * 0.8), H - q * h / 14) for q in range(15)]), (0.2, 1.0, 0.6), 6)
    for k in range(5):  # speed streaks behind the fish
        neon_stroke(c, lambda q, k=k: (q.new_path(), q.move_to(-40, 700 + k * 60), q.line_to(120 + k * 20, 700 + k * 60)), (1, 0.55, 0.2), 3)
    neon_stroke(c, lambda q: (q.new_path(), tail_shape(q, 420, 820, 1.0)), (1, 0.45, 0.15), 8)
    neon_stroke(c, lambda q: (q.new_path(), fish_shape(q, 420, 820, 1.0)), (1, 0.55, 0.2), 9)
    neon_stroke(c, lambda q: (q.new_path(), q.arc(560, 760, 46, 0, 2 * math.pi)), (1, 0.9, 0.5), 6)
    c.new_path(); c.arc(575, 760, 20, 0, 2 * math.pi); c.set_source_rgb(1, 1, 1); c.fill()
    neon_stroke(c, lambda q: (q.new_path(), q.move_to(640, 840), q.curve_to(600, 885, 560, 885, 525, 860)), (1, 0.35, 0.35), 6)
    cx, cy = 860, 640   # the sapphire: a glowing rainbow mosaic
    for i in range(19):
        a = i * 0.33; r = 20 + (i % 5) * 20; hx, hy = cx + math.cos(a) * r * 0.9, cy + math.sin(a) * r * 1.3
        k = [(0.3, 0.75, 1), (0.7, 0.45, 1), (1, 0.85, 0.3), (0.3, 1, 0.85)][i % 4]
        neon_stroke(c, lambda q, hx=hx, hy=hy: (q.new_path(), path(q, [(hx + 22 * math.cos(math.pi / 3 * j), hy + 22 * math.sin(math.pi / 3 * j)) for j in range(6)])), k, 3)
    glow(c, cx, cy, 280, (0.6, 0.7, 1), 0.5)
    for j in range(5):
        a = j * 1.25; x, y = cx + math.cos(a) * 170, cy + math.sin(a) * 190
        neon_stroke(c, lambda q, x=x, y=y: (q.new_path(), q.move_to(x - 26, y), q.line_to(x + 26, y), q.move_to(x, y - 26), q.line_to(x, y + 26)), (1, 1, 0.9), 3)
    S.flush(); img = np.ndarray((H, W, 4), np.uint8, S.get_data())[..., 2::-1]
    Image.fromarray(Post(1.3)(np.ascontiguousarray(img), 0.0)).save(out)

if __name__ == "__main__":
    o = sys.argv[1]; os.makedirs(o, exist_ok=True)
    paper(os.path.join(o, "style_paper.png")); neon(os.path.join(o, "style_neon.png")); print("ok")
