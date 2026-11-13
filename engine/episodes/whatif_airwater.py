"""What If #2: What if all the air turned into water for one minute?  (cartoon style A + cinematic look)
Premise: the air becomes the same *weight* of water. Facts: 1 atm ≈ 10.3 m of water -> a ~10 m global flood (~3 floors);
no atmosphere -> black daytime sky; water exposed to vacuum boils and freezes at once; most people hold their breath ~30–90 s.
"""
import math
from cartoon import *

NAME = "whatif_airwater"
LOOK = "cinematic"
TITLE = "What if air turned into water for 1 minute? 🌊 #shorts"
DESCRIPTION = ("If all the air on Earth became water for 60 seconds, the planet would flood three floors deep and the sky would turn black. "
               "Hold your breath and comment your time! #whatif #science #physics #shorts")
TAGS = ["what if", "air", "water", "science", "physics", "shorts"]
VOICE, SPEED = "am_michael", 1.05
HOOK = ("WHAT IF AIR TURNED", "INTO WATER?")
BEATS = [
    ("hook", "What if all the air on Earth... turned into water for one minute?", 0.4),
    ("flood", "The air above you weighs the same as a ten-meter pool of water. So the whole planet would flood... three floors deep.", 0.0),
    ("sky", "And above the water? Nothing. No air at all. The sky would turn black, even at noon, and planes would start to fall.", 0.3),
    ("boil", "The water's surface, touching empty space, would boil and freeze at the same time.", 0.0),
    ("you", "And you? Trapped underwater, with nothing above to breathe. Your only hope: hold your breath.", 0.0),
    ("end", "Most people can only manage about a minute. Could you? Try it now, and tell me your time.", 0.9),
]
DEEP, MID, LIGHT = rgb("#0a3d7a"), rgb("#1f78c8"), rgb("#6fd0ff")

# ---------------- underwater kit (episode-local)
def bg_underwater(c, t, top=LIGHT, bot=DEEP):
    c.save(); c.identity_matrix()
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, *top); g.add_color_stop_rgb(1, *bot); c.set_source(g); c.paint(); c.restore()

def caustics(c, t, alpha=0.18, y0=0, y1=H):
    """wobbling net of light lines, like sunlight through waves"""
    c.save(); c.set_line_width(6); c.set_line_cap(cairo.LINE_CAP_ROUND)
    for i in range(10):
        y = y0 + (y1 - y0) * i / 10
        c.new_path(); c.move_to(-50, y)
        for x in range(0, W + 100, 60):
            c.line_to(x, y + 22 * math.sin(x * 0.013 + t * 1.6 + i) + 14 * math.sin(x * 0.031 - t * 2.2 + i * 2))
        c.set_source_rgba(0.85, 0.97, 1, alpha * (0.6 + 0.4 * math.sin(t + i))); c.stroke()
    c.restore()

def bubbles(c, t, n=24, seed=1, x0=0, x1=W, y0=0, y1=H, size=1.0):
    rng = np.random.default_rng(seed)
    for i in range(n):
        x = rng.uniform(x0, x1); sp = rng.uniform(0.08, 0.2); r = rng.uniform(6, 22) * size; ph = rng.uniform(0, 1)
        u = (t * sp + ph) % 1; y = y1 - (y1 - y0) * u; xx = x + math.sin(t * 2 + i) * 14
        c.new_path(); c.arc(xx, y, r, 0, 2 * math.pi); c.set_source_rgba(0.9, 0.98, 1, 0.25); c.fill_preserve()
        c.set_source_rgba(1, 1, 1, 0.8); c.set_line_width(3); c.stroke()
        c.new_path(); c.arc(xx - r * 0.35, y - r * 0.35, r * 0.25, 0, 2 * math.pi); c.set_source_rgba(1, 1, 1, 0.9); c.fill()

def building(c, x, y, w, h, col, win=(0.75, 0.9, 1), lit=0.0):
    c.new_path(); c.rectangle(x, y - h, w, h); fs(c, col, 8)
    for k in range(int(h // 110)):
        for j in range(int(w // 90)):
            wx, wy = x + 25 + j * 90, y - h + 30 + k * 110
            c.new_path(); c.rectangle(wx, wy, 50, 66); fs(c, mix(win, (1, 0.85, 0.4), lit), 5)

def floating_car(c, x, y, s, t, ang=0.0, col=RED):
    c.save(); c.translate(x, y + math.sin(t * 1.2) * 12); c.rotate(ang + 0.06 * math.sin(t * 0.9)); c.scale(s, s)
    c.new_path(); path(c, [(-170, -40), (-170, -100), (-90, -110), (-50, -170), (60, -170), (110, -110), (175, -95), (175, -40)]); fs(c, col, 8)
    c.new_path(); path(c, [(-35, -160), (50, -160), (90, -112), (-70, -112)]); fs(c, SKY, 6)
    for wx in (-100, 105): circle(c, wx, -38, 38, rgb("#333344"), 8); circle(c, wx, -38, 14, GREY, 5)
    c.restore()

def cone(c, x, y, s, t, ang=0.0):
    c.save(); c.translate(x, y + math.sin(t * 1.5 + 1) * 10); c.rotate(ang + 0.1 * math.sin(t)); c.scale(s, s)
    c.new_path(); path(c, [(-45, 0), (-12, -120), (12, -120), (45, 0)]); fs(c, ORANGE, 7)
    c.new_path(); c.rectangle(-30, -70, 60, 18); c.set_source_rgb(1, 1, 1); c.fill()
    c.new_path(); c.rectangle(-60, 0, 120, 18); fs(c, ORANGE, 7); c.restore()

# ---------------- scenes
def s_hook(c, s):
    t = s.t
    bg_underwater(c, t)
    for i, (x, w, h, col) in enumerate([(-40, 260, 1250, rgb("#3a6fa8")), (250, 230, 1050, rgb("#2f5f96")), (500, 280, 1350, rgb("#356aa3")), (800, 300, 1150, rgb("#2d5a8f"))]):
        building(c, x, 1500, w, h, mix(col, DEEP, 0.25), lit=0.4)
    c.new_path(); c.rectangle(0, 1500, W, 500); fs(c, rgb("#29304a"), 0)
    for i in range(6): c.new_path(); c.rectangle(40 + i * 190, 1590, 110, 16); c.set_source_rgba(1, 0.9, 0.4, 0.6); c.fill()
    floating_car(c, 800, 1180, 0.9, t, -0.25)
    cone(c, 170, 1050, 0.9, t, 0.6)
    caustics(c, t, 0.16)
    bubbles(c, t, 30, 1)
    leo(c, 520, 1640 + math.sin(t * 1.3) * 18, 0.95, "shock", "hold", t, look=(0, -0.6), bob=False)
    bubbles(c, t, 6, 9, 440, 640, 600, 1050, 0.8)

SCENES = [("hook", s_hook)]
