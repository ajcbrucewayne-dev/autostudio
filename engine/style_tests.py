"""Style tests for the What If channel: same moment ("the Moon vanished") in two fast 2D looks.
A) Bright cartoon  B) Leo's notebook (marker doodles on lined paper)
python3 engine/style_tests.py out_dir
"""
import math, os, sys
import numpy as np
import cairo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parchment as pm

W, H = 1080, 1920
def rgb(h): h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
OUT = rgb("#1b1530")

def blob(cx, cy, r, seed, k=7, amp=0.35):
    rng = np.random.default_rng(seed); ph = rng.uniform(0, 6, k); a = np.linspace(0, 2 * np.pi, 80)
    rr = r * (1 + sum(amp / (i + 1) * np.sin((i + 2) * a + ph[i]) for i in range(3)))
    return np.stack([cx + np.cos(a) * rr, cy + np.sin(a) * rr], 1)

def path(c, P):
    c.move_to(*P[0])
    for q in P[1:]: c.line_to(*q)
    c.close_path()

def text(c, s, x, y, size, col, font="Inter", bold=True, outline=None, ow=10):
    c.select_font_face(font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    c.set_font_size(size); e = c.text_extents(s); x0 = x - e.x_advance / 2
    if outline:
        c.move_to(x0, y); c.text_path(s); c.set_source_rgb(*outline); c.set_line_width(ow); c.set_line_join(cairo.LINE_JOIN_ROUND); c.stroke()
    c.move_to(x0, y); c.set_source_rgb(*col); c.show_text(s)
    return e.x_advance

def earth(c, cx, cy, r, ow=10, flat=True):
    c.save(); c.arc(cx, cy, r * 1.12, 0, 2 * math.pi)
    g = cairo.RadialGradient(cx, cy, r * 0.95, cx, cy, r * 1.12); g.add_color_stop_rgba(0, 0.45, 0.8, 1, 0.55); g.add_color_stop_rgba(1, 0.45, 0.8, 1, 0)
    c.set_source(g); c.fill()
    c.arc(cx, cy, r, 0, 2 * math.pi); c.set_source_rgb(*rgb("#2f7de1")); c.fill_preserve(); c.save(); c.clip()
    for i, (dx, dy, rr) in enumerate([(-0.45, -0.35, 0.42), (0.35, -0.1, 0.38), (-0.1, 0.5, 0.33), (0.6, 0.55, 0.22), (-0.75, 0.3, 0.2)]):
        path(c, blob(cx + dx * r, cy + dy * r, rr * r, i + 3)); c.set_source_rgb(*rgb("#4cc35a")); c.fill_preserve()
        c.set_source_rgb(*rgb("#2e8f3e")); c.set_line_width(ow * 0.5); c.stroke()
    for i in range(4):  # clouds
        path(c, blob(cx + (-0.6 + i * 0.4) * r, cy + (-0.55 + (i % 2) * 0.7) * r, r * 0.13, 20 + i, amp=0.25)); c.set_source_rgba(1, 1, 1, 0.85); c.fill()
    c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD); c.arc(cx, cy, r * 1.01, 0, 2 * math.pi); c.new_sub_path(); c.arc(cx - r * 0.18, cy - r * 0.18, r * 1.0, 0, 2 * math.pi)
    c.set_source_rgba(0.05, 0.05, 0.25, 0.30); c.fill(); c.set_fill_rule(cairo.FILL_RULE_WINDING)   # cel shadow crescent
    c.arc(cx - r * 0.4, cy - r * 0.45, r * 0.18, 0, 2 * math.pi); c.set_source_rgba(1, 1, 1, 0.25); c.fill()
    c.restore()
    c.arc(cx, cy, r, 0, 2 * math.pi); c.set_source_rgb(*OUT); c.set_line_width(ow); c.stroke(); c.restore()

def leo(c, x, y, s, ow=8, mood="shock"):
    """Leo (original character): curly hair, brown skin, yellow hoodie with a star. (x,y) = feet."""
    skin, hood, hair = rgb("#a86b45"), rgb("#ffc928"), rgb("#2b1a14")
    def fill_stroke(col, lw=ow):
        c.set_source_rgb(*col); c.fill_preserve(); c.set_source_rgb(*OUT); c.set_line_width(lw); c.stroke()
    c.save(); c.translate(x, y); c.scale(s, s); c.set_line_join(cairo.LINE_JOIN_ROUND); c.set_line_cap(cairo.LINE_CAP_ROUND)
    for sx in (-1, 1):  # legs + shoes
        c.rectangle(sx * 38 - 22, -170, 44, 140); fill_stroke(rgb("#3b5bdb"))
        c.save(); c.translate(sx * 45, -22); c.scale(1.6, 1); c.arc(0, 0, 26, 0, 2 * math.pi); c.restore(); fill_stroke(rgb("#ef4444"))
    # arm pointing up (right), other arm on cheek (left)
    c.move_to(80, -330); c.line_to(190, -470); c.line_to(215, -560); c.set_source_rgb(*OUT); c.set_line_width(64); c.stroke()
    c.move_to(80, -330); c.line_to(190, -470); c.line_to(215, -560); c.set_source_rgb(*hood); c.set_line_width(46); c.stroke()
    c.arc(218, -575, 26, 0, 2 * math.pi); fill_stroke(skin)
    c.move_to(-80, -330); c.line_to(-150, -420); c.line_to(-110, -520); c.set_source_rgb(*OUT); c.set_line_width(64); c.stroke()
    c.move_to(-80, -330); c.line_to(-150, -420); c.line_to(-110, -520); c.set_source_rgb(*hood); c.set_line_width(46); c.stroke()
    # hoodie body
    c.move_to(-95, -400); c.curve_to(-120, -300, -115, -200, -100, -160); c.line_to(100, -160); c.curve_to(115, -200, 120, -300, 95, -400)
    c.curve_to(60, -430, -60, -430, -95, -400); c.close_path(); fill_stroke(hood)
    st = [(math.cos(-math.pi / 2 + i * math.pi / 5) * (34 if i % 2 == 0 else 15), -285 + math.sin(-math.pi / 2 + i * math.pi / 5) * (34 if i % 2 == 0 else 15)) for i in range(10)]
    path(c, st); c.set_source_rgb(1, 1, 1); c.fill()
    # head
    hy = -560
    for i in range(11):  # curly hair puffs
        a = math.pi + i * math.pi / 10; c.arc(math.cos(a) * 150, hy - 20 + math.sin(a) * 140, 52, 0, 2 * math.pi); fill_stroke(hair, ow * 0.8)
    c.save(); c.translate(0, hy); c.scale(1, 1.05); c.arc(0, 0, 150, 0, 2 * math.pi); c.restore(); fill_stroke(skin)
    for i in range(7):
        a = math.pi * 1.1 + i * math.pi * 0.8 / 6; c.arc(math.cos(a) * 125, hy - 30 + math.sin(a) * 110, 42, 0, 2 * math.pi); c.set_source_rgb(*hair); c.fill()
    for sx in (-1, 1):
        c.arc(sx * 152, hy + 10, 26, 0, 2 * math.pi); fill_stroke(skin)  # ears
        ex = sx * 58
        c.save(); c.translate(ex, hy + 10); c.scale(1, 1.25); c.arc(0, 0, 40, 0, 2 * math.pi); c.restore(); fill_stroke((1, 1, 1), ow * 0.8)
        c.arc(ex + 10, hy - 8, 19, 0, 2 * math.pi); c.set_source_rgb(*OUT); c.fill()
        c.arc(ex + 4, hy - 16, 7, 0, 2 * math.pi); c.set_source_rgb(1, 1, 1); c.fill()
        c.move_to(ex - 34, hy - 72); c.curve_to(ex - 15, hy - 102, ex + 15, hy - 102, ex + 34, hy - 72)
        c.set_source_rgb(*OUT); c.set_line_width(ow * 1.4); c.stroke()
        c.arc(sx * 95, hy + 75, 22, 0, 2 * math.pi); c.set_source_rgba(0.9, 0.35, 0.3, 0.35); c.fill()
    c.save(); c.translate(0, hy + 95); c.scale(1, 1.3); c.arc(0, 0, 30, 0, 2 * math.pi); c.restore(); fill_stroke(rgb("#5a1414"), ow * 0.8)
    c.restore()

def style_a(path_out):
    S = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); c = cairo.Context(S)
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, *rgb("#0f1b4d")); g.add_color_stop_rgb(1, *rgb("#3a1f6b")); c.set_source(g); c.paint()
    rng = np.random.default_rng(2)
    for _ in range(160):
        x, y, r = rng.uniform(0, W), rng.uniform(0, H * 0.75), rng.choice([1.5, 2, 3, 4])
        c.arc(x, y, r, 0, 2 * math.pi); c.set_source_rgba(1, 1, 0.9, rng.uniform(0.5, 1)); c.fill()
    # moon gone: dashed outline + crumbling pieces + "?"
    mx, my, mr = 770, 560, 125
    c.set_dash([22, 16]); c.arc(mx, my, mr, 0, 2 * math.pi); c.set_source_rgba(1, 1, 1, 0.8); c.set_line_width(7); c.stroke(); c.set_dash([])
    for i in range(9):
        a = i * 0.7; d = mr * (1.25 + 0.35 * (i % 3)); px, py = mx + math.cos(a) * d, my + math.sin(a) * d
        path(c, blob(px, py, 14 + 6 * (i % 2), 40 + i, amp=0.4)); c.set_source_rgb(*rgb("#c9c9d6")); c.fill_preserve(); c.set_source_rgb(*OUT); c.set_line_width(4); c.stroke()
    text(c, "?", mx, my + 55, 160, rgb("#ffd43b"), outline=OUT, ow=14)
    earth(c, 600, 1030, 300)
    leo(c, 250, 2080, 0.78)
    text(c, "WHAT IF THE MOON", W / 2, 220, 84, (1, 1, 1), outline=OUT, ow=16)
    text(c, "VANISHED?", W / 2, 320, 104, rgb("#ffd43b"), outline=OUT, ow=18)
    # caption
    c.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(78)
    words = [("THE", 0), ("MOON", 1), ("WAS", 0), ("GONE.", 0)]; widths = [c.text_extents(w).x_advance for w, _ in words]
    x = W / 2 - (sum(widths) + 22 * 3) / 2
    for (w, hi), wd in zip(words, widths):
        c.move_to(x, 1420); c.text_path(w); c.set_source_rgb(*OUT); c.set_line_width(14); c.stroke()
        c.move_to(x, 1420); c.set_source_rgb(*(rgb("#ffd43b") if hi else (1, 1, 1))); c.show_text(w); x += wd + 22
    S.write_to_png(path_out)

def style_b(path_out):
    """Leo's notebook: marker + colored-pencil doodles on lined paper (reuses the ink engine on white paper)."""
    pm.BOIL_AMP = 1.0
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    paper = np.empty((H, W, 3), np.float32); paper[:] = (250, 247, 236)
    paper *= (1 + 0.012 * pm._fbm((H, W), 4)[..., None])
    for yy in range(300, H, 64): paper[yy:yy + 2] = paper[yy:yy + 2] * np.array([0.78, 0.86, 0.98])
    paper[:, 130:133] = paper[:, 130:133] * np.array([1.0, 0.7, 0.7])
    ink = pm.Ink(); ink.clear(); c = ink.ctx
    BLUE, GREEN, YEL, PEN = (0.25, 0.55, 0.95), (0.35, 0.75, 0.35), (1.0, 0.82, 0.2), (0.12, 0.14, 0.3)
    # earth (marker fill + pen outline + pencil shading)
    cx, cy, r = 600, 1030, 280
    circ = [(cx + math.cos(a) * r, cy + math.sin(a) * r) for a in np.linspace(0, 2 * math.pi, 60)]
    ink.fill(circ, BLUE, 0.75)
    for i in range(5):
        P = blob(cx + [-0.45, 0.35, -0.1, 0.55, -0.7][i] * r, cy + [-0.35, -0.1, 0.5, 0.5, 0.25][i] * r, [0.36, 0.34, 0.3, 0.18, 0.17][i] * r, i + 3)
        P = P[((P[:, 0] - cx) ** 2 + (P[:, 1] - cy) ** 2) < (r * 0.97) ** 2]
        if len(P) > 5: ink.fill(P, GREEN, 0.85); ink.stroke(list(P) + [P[0]], 3, 1, (0.15, 0.4, 0.15), 0.8, taper=False, dense=False)
    ink.hatch([(cx + math.cos(a) * r, cy + math.sin(a) * r) for a in np.linspace(-0.6, 2.2, 30)] + [(cx + r * 0.3, cy + r * 0.2)], 1, 45, 14, 2.5, PEN, 0.35)
    ink.circle(cx, cy, r, 7, 1, PEN, 1)
    # moon gone
    mx, my, mr = 780, 560, 120
    for k in range(18):
        a0 = k * 2 * math.pi / 18; ink.stroke([(mx + math.cos(a0) * mr, my + math.sin(a0) * mr), (mx + math.cos(a0 + 0.2) * mr, my + math.sin(a0 + 0.2) * mr)], 6, 1, PEN, 0.9)
    ink.text("?", mx, my + 10, 170, (0.9, 0.2, 0.2), 1, family="Inter")
    for k in range(6):  # motion "poof" marks
        a = k * 1.05; ink.line((mx + math.cos(a) * 150, my + math.sin(a) * 150), (mx + math.cos(a) * 200, my + math.sin(a) * 200), 6, 1, PEN, 0.8)
    # arrow + handwritten note
    ink.stroke([(330, 640), (450, 600), (620, 580)], 6, 1, (0.9, 0.2, 0.2), 1)
    ink.stroke([(590, 555), (625, 580), (592, 605)], 6, 1, (0.9, 0.2, 0.2), 1)
    ink.text("GONE?!", 250, 700, 70, (0.9, 0.2, 0.2), 1, family="Inter")
    # washi tape + title on a sticky note
    ink.fill([(140, 120), (940, 100), (950, 390), (150, 405)], YEL, 0.85)
    ink.fill([(470, 70), (640, 80), (630, 140), (465, 130)], (0.95, 0.5, 0.6), 0.6)
    ink.text("WHAT IF THE MOON", W / 2, 215, 74, PEN, 1, family="Inter")
    ink.text("VANISHED?", W / 2, 320, 100, (0.9, 0.2, 0.2), 1, family="Inter")
    out = pm.composite(paper, np.zeros((H, W), np.float32), ink, 0, flick=False)
    # Leo as a colored doodle: draw cartoon Leo on its own layer, then paste over the paper
    S = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c2 = cairo.Context(S); leo(c2, 250, 2080, 0.78, ow=9); S.flush()
    L = np.ndarray((H, W, 4), np.uint8, S.get_data()).astype(np.float32) / 255
    a = L[..., 3:4]; out = (out * (1 - a) + L[..., 2::-1] * 255).clip(0, 255).astype(np.uint8)
    from PIL import Image, ImageDraw, ImageFont
    im = Image.fromarray(out); d = ImageDraw.Draw(im); f = ImageFont.truetype(os.path.join(os.path.dirname(__file__), "..", "fonts", "Inter-ExtraBold.otf"), 78)
    d.text((W / 2, 1400), "THE MOON WAS GONE.", font=f, fill=(255, 255, 255), anchor="mm", stroke_width=12, stroke_fill=(27, 21, 48))
    im.save(path_out)

if __name__ == "__main__":
    o = sys.argv[1]; os.makedirs(o, exist_ok=True)
    style_a(os.path.join(o, "style_A_bright_cartoon.png")); style_b(os.path.join(o, "style_B_notebook.png")); print("ok")
