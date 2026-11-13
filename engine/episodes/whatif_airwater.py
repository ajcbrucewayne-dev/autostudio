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

GROUND, FLOOR = 1300, 150          # street level and storey height for the flood scenes

def house(c, x, w, floors, col, roof_col):
    top = GROUND - floors * FLOOR
    c.new_path(); c.rectangle(x, top, w, floors * FLOOR); fs(c, col, 8)
    c.new_path(); path(c, [(x - 20, top), (x + w / 2, top - 110), (x + w + 20, top)]); fs(c, roof_col, 8)
    for f in range(floors):
        for j in range(int(w // 110)):
            c.new_path(); c.rectangle(x + 30 + j * 110, GROUND - (f + 1) * FLOOR + 35, 60, 75); fs(c, rgb("#bfe6ff"), 5)
        c.new_path(); c.move_to(x, GROUND - f * FLOOR); c.line_to(x + w, GROUND - f * FLOOR); c.set_source_rgba(*OUT, 0.35); c.set_line_width(4); c.stroke()

def cat(c, x, y, s, t):
    c.save(); c.translate(x, y); c.scale(s, s); GR = rgb("#ff9f43")
    c.new_path(); c.save(); c.scale(1.3, 1); c.arc(0, 0, 40, 0, 2 * math.pi); c.restore(); fs(c, GR, 6)
    c.new_path(); c.arc(-40, -40, 30, 0, 2 * math.pi); fs(c, GR, 6)
    for ex in (-58, -22): c.new_path(); path(c, [(ex - 12, -62), (ex, -88), (ex + 12, -62)]); fs(c, GR, 5)
    for ex in (-50, -30): c.new_path(); c.move_to(ex - 6, -42); c.line_to(ex + 6, -42); c.set_source_rgb(*OUT); c.set_line_width(5); c.stroke()  # unimpressed eyes
    c.new_path(); c.move_to(48, 0); c.curve_to(90, -10 + 10 * math.sin(t * 3), 80, -60, 100, -70 + 10 * math.sin(t * 3)); c.set_source_rgb(*OUT); c.set_line_width(14); c.stroke()
    c.new_path(); c.move_to(48, 0); c.curve_to(90, -10 + 10 * math.sin(t * 3), 80, -60, 100, -70 + 10 * math.sin(t * 3)); c.set_source_rgb(*GR); c.set_line_width(7); c.stroke()
    c.restore()

def water_over(c, y, t, x0=-60, x1=W + 60, alpha=0.55):
    """translucent flood water from height y down"""
    pts = [(x, y + 12 * math.sin(x * 0.012 + t * 2.0)) for x in range(int(x0), int(x1) + 30, 30)]
    c.new_path(); path(c, pts + [(x1, H + 60), (x0, H + 60)]); c.set_source_rgba(0.12, 0.5, 0.95, alpha); c.fill()
    c.new_path(); path(c, pts, close=False); c.set_source_rgba(1, 1, 1, 0.85); c.set_line_width(7); c.stroke()

def plane(c, x, y, s, ang, t, dead=False):
    c.save(); c.translate(x, y); c.rotate(ang); c.scale(s, s)
    c.new_path(); path(c, [(-150, 0), (-120, -30), (130, -30), (175, -5), (130, 20), (-120, 20)]); fs(c, WHITE, 8)
    c.new_path(); path(c, [(-20, -10), (40, -10), (-30, 90), (-70, 90)]); fs(c, rgb("#d9e2f2"), 7)
    c.new_path(); path(c, [(-150, -5), (-120, -5), (-150, -75), (-175, -75)]); fs(c, RED, 7)
    for i in range(5): c.new_path(); c.arc(-60 + i * 40, -8, 9, 0, 2 * math.pi); fs(c, SKY, 4)
    if dead:
        for k in range(3):
            u = (t * 1.5 + k / 3) % 1; c.new_path(); c.arc(-180 - u * 120, -10 - u * 30, 18 + u * 26, 0, 2 * math.pi); c.set_source_rgba(0.3, 0.3, 0.35, 0.7 * (1 - u)); c.fill()
    c.restore()

def sky_drain(c, t, t0, dur=1.6, y_bottom=1000):
    """blue daytime sky draining to black from the top, stars appearing"""
    f = clamp((t - t0) / dur)
    c.save(); c.identity_matrix(); g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, *rgb("#3e9bff")); g.add_color_stop_rgb(1, *rgb("#bfe6ff"))
    c.set_source(g); c.paint(); c.restore()
    if f > 0:
        edge = lerp(-200, y_bottom + 200, ease(f))
        g = cairo.LinearGradient(0, edge - 220, 0, edge); g.add_color_stop_rgba(0, 0.02, 0.02, 0.06, 1); g.add_color_stop_rgba(1, 0.02, 0.02, 0.06, 0)
        c.new_path(); c.rectangle(-100, -300, W + 200, edge + 300); c.set_source(g); c.fill()
        rng = np.random.default_rng(4)
        for i in range(120):
            x, y = rng.uniform(0, W), rng.uniform(0, y_bottom)
            if y < edge - 220: c.new_path(); c.arc(x, y, rng.choice([1.5, 2.5, 3.5]), 0, 2 * math.pi); c.set_source_rgba(1, 1, 0.9, clamp((edge - 220 - y) / 200) * (0.6 + 0.4 * math.sin(t * 2 + i))); c.fill()

def s_flood(c, s):
    t = s.t; tf = s.W("flood", "flood"); td = s.W("flood", "deep", end=True)
    sky_drain(c, t, 1e9)
    sun(c, 900, 260, 60, t, face="happy")
    house(c, 40, 300, 5, rgb("#ff9f6b"), rgb("#c0392b")); house(c, 390, 300, 4, rgb("#ffd36b"), rgb("#8e44ad")); house(c, 740, 300, 6, rgb("#7fd18b"), rgb("#2c6e49"))
    cat(c, 560, GROUND - 3 * FLOOR - 20, 0.9, t)
    c.new_path(); c.rectangle(0, GROUND, W, 700); fs(c, rgb("#55555f"), 0)
    lvl = lerp(GROUND + 80, GROUND - 3 * FLOOR, ease((t - tf + 0.3) / max(0.6, td - tf + 0.3)))
    floating_car(c, 250, min(GROUND - 20, lvl + 60), 0.55, t, 0.15 * clamp((GROUND - lvl) / 200))
    water_over(c, lvl, t)
    # ruler
    c.new_path(); c.rectangle(1000, GROUND - 3 * FLOOR - 40, 22, 3 * FLOOR + 40); fs(c, YEL, 6)
    m = clamp((GROUND - lvl) / (3 * FLOOR)) * 10.3
    text(c, f"{m:.0f} m", 920, lvl - 40, 64, WHITE)
    label(c, "AIR WEIGHT = 10 m OF WATER", W / 2, 330, 46, WHITE, OUT, s.P(s.W("flood", "weighs"), 0.35))
    if t > td - 0.3: label(c, "3 FLOORS DEEP", W / 2, 470, 60, YEL, OUT, s.P(td - 0.3, 0.35))
    bubbles(c, t, 10, 3, 0, W, lvl + 40, H, 0.8)
    leo(c, 540, 2080, 0.72, "shock", "hold", t, look=(0, -0.8))

def s_sky(c, s):
    t = s.t; tb = s.W("sky", "black"); tp = s.W("sky", "planes")
    sky_drain(c, t, tb - 0.4, 1.8, 1000)
    sun(c, 860, 280, 55, t)
    if t < tb: label(c, "NO AIR", W / 2, 420, 64, WHITE, OUT, s.P(s.W("sky", "Nothing"), 0.35))
    else: label(c, "BLACK SKY AT NOON", W / 2, 420, 56, YEL, OUT, s.P(tb + 0.3, 0.35))
    T_SPLASH = tp + 2.0
    if t > tp - 1.2:
        u = clamp((t - tp + 1.2) / 3.2); x = lerp(-200, 760, u); y = 560 + max(0, (t - tp)) ** 2 * 120
        if t < T_SPLASH: plane(c, x, min(y, 1000), 0.8, 0.0 + clamp((t - tp) / 2) * 0.9, t, dead=t > tp)
    wave_band(c, 1000, t, col=rgb("#1f78c8"), bottom=H + 60)
    if t > T_SPLASH:
        lt = t - T_SPLASH
        for k in range(9):
            a = math.pi + (k + 0.5) * math.pi / 9; d = ease_out(lt / 0.8) * 260
            circle(c, 640 + math.cos(a) * d, 1000 + math.sin(a) * d * 1.2 + lt * lt * 300, 22 * (1 - clamp(lt / 1.2)), WHITE, 5, 1 - clamp(lt / 1.2))
    bubbles(c, t, 14, 5, 0, W, 1040, H, 0.8)
    leo(c, 540, 2080, 0.72, "point_up", "hold" if t < tp else "shock", t, look=(0.2, -1))

def s_boil(c, s):
    t = s.t; tb = s.W("boil", "boil"); tz = s.W("boil", "freeze")
    bg_color(c, rgb("#040612"))
    rng = np.random.default_rng(6)
    for i in range(120):
        c.new_path(); c.arc(rng.uniform(0, W), rng.uniform(0, 900), rng.choice([1.5, 2.5]), 0, 2 * math.pi); c.set_source_rgba(1, 1, 0.9, 0.8); c.fill()
    bg = 1 - clamp((t - tz) / 2.5)
    wave_band(c, 900, t, col=mix(rgb("#1f78c8"), rgb("#bfe9ff"), 1 - bg), amp=14 * bg + 2, bottom=H + 60)
    if t > tb - 0.2:   # boiling: bubbles bursting through the surface + vapour
        for i in range(16):
            u = ((t - tb) * 1.4 + i / 16) % 1; x = 60 + (i * 137) % 960
            circle(c, x, 900 - u * 160, 16 + 10 * (i % 3), WHITE, 4, (1 - u) * bg * 0.9)
            c.new_path(); c.move_to(x, 880 - u * 300); c.curve_to(x + 30, 820 - u * 320, x - 30, 780 - u * 330, x, 740 - u * 360)
            c.set_source_rgba(1, 1, 1, 0.35 * (1 - u) * bg); c.set_line_width(10); c.stroke()
    if t > tz - 0.2:   # frost crystals growing across the surface
        g = ease(clamp((t - tz + 0.2) / 1.6))
        for i in range(9):
            cx = 70 + i * 120; L = 70 * g
            for k in range(6):
                a = k * math.pi / 3
                c.new_path(); c.move_to(cx, 905); c.line_to(cx + math.cos(a) * L, 905 + math.sin(a) * L * 0.4)
                c.set_source_rgba(0.85, 0.97, 1, 0.95); c.set_line_width(7); c.stroke()
    label(c, "BOILING", 300, 560, 60, ORANGE, WHITE, s.P(tb, 0.35))
    label(c, "FREEZING", 780, 560, 60, CYAN, OUT, s.P(tz, 0.35))
    text(c, "AT THE SAME TIME", W / 2, 700, 54, YEL, alpha=s.P(tz + 0.4, 0.3))
    leo(c, 540, 2080, 0.72, "think", "wow", t, look=(0, -1))

COUNT_FROM = 60
def countdown_val(s):
    t0 = s.W("you", "hope"); t1 = s.W("end", "Could")
    return max(0, COUNT_FROM - COUNT_FROM * clamp((s.t - t0) / (t1 - t0))) if s.t > t0 else COUNT_FROM

def s_you(c, s):
    t = s.t
    bg_underwater(c, t, MID, DEEP)
    c.new_path(); c.rectangle(-60, -60, W + 120, 420); c.set_source_rgb(0.02, 0.02, 0.06); c.fill()      # black sky above the surface
    for i in range(40): c.new_path(); c.arc((i * 263) % W, (i * 97) % 330, 2.5, 0, 2 * math.pi); c.set_source_rgba(1, 1, 0.9, 0.8); c.fill()
    pts = [(x, 360 + 14 * math.sin(x * 0.012 + t * 2)) for x in range(-60, W + 90, 30)]
    c.new_path(); path(c, pts, close=False); c.set_source_rgba(1, 1, 1, 0.85); c.set_line_width(8); c.stroke()
    caustics(c, t, 0.14, 380, H)
    bubbles(c, t, 16, 8, 0, W, 400, H)
    th = s.W("you", "hope")
    if t > th - 0.3:
        v = countdown_val(s); beat = 1 + 0.06 * max(0, math.sin(t * 7))
        pop_text(c, f"{v:.0f}", W / 2, 640, 210 * beat, s.P(th - 0.3, 0.3), YEL if v > 15 else RED)
        text(c, "HOLD YOUR BREATH", W / 2, 800, 56, WHITE, alpha=s.P(th, 0.3))
    face = "hold" if t < th + 1.5 else "worried"
    leo(c, 540, 2120 + math.sin(t * 1.3) * 16, 0.8, "idle" if t < th else "cover", face, t, look=(0, -1), bob=False)

def s_end(c, s):
    t = s.t; tz = s.W("end", "Could"); tt = s.W("end", "tell")
    gone = clamp((t - tz) / 0.5)
    if gone < 1:
        bg_underwater(c, t, MID, DEEP); bubbles(c, t, 20, 8, 0, W, 300, H)
    c.save(); c.set_source_rgba(1, 1, 1, 0); c.restore()
    if gone > 0:
        c.save(); c.identity_matrix(); g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, *rgb("#3e9bff")); g.add_color_stop_rgb(1, *rgb("#d4f0ff"))
        c.set_source(g); c.paint_with_alpha(gone); c.restore()
        for i in range(14):  # mist burst
            a = i * 0.45; d = ease_out((t - tz) / 0.9) * 600
            circle(c, W / 2 + math.cos(a) * d, 1000 + math.sin(a) * d, 70 * (1 - clamp((t - tz) / 1.2)), WHITE, 0, 0.6 * (1 - clamp((t - tz) / 1.2)))
        cloud(c, 220, 300, 80); cloud(c, 800, 420, 60)
    if t < tz:
        v = countdown_val(s); pop_text(c, f"{v:.0f}", W / 2, 640, 210, 1, YEL if v > 15 else RED)
    else:
        pop_text(c, "0", W / 2, 640, 210, 1 - clamp((t - tz - 0.4) / 0.3), RED)
    if t > tz + 0.6:
        pop_text(c, "HOLD YOUR BREATH: 60s", W / 2, 420, 68, s.P(tz + 0.6, 0.35), YEL)
        pop_text(c, "COMMENT YOUR TIME!", W / 2, 540, 74, s.P(tt - 0.2, 0.35), WHITE)
    face = "worried" if t < tz else ("gasp" if t < tz + 1.6 else "wow")
    leo(c, 540, 2120 + (math.sin(t * 1.3) * 16 if t < tz else 0), 0.8, "cover" if t < tz else "cheer", face, t, bob=t > tz)

SCENES = [("hook", s_hook), ("flood", s_flood), ("sky", s_sky), ("boil", s_boil), ("you", s_you), ("end", s_end)]

def cams(Wt, B):
    return {"hook": [(0, 540, 1000, 1.06), (B["hook"]["t1"], 540, 960, 1.0)],
            "flood": [(Wt("flood"), 540, 960, 1.0), (Wt("flood", "deep"), 540, 900, 1.06)],
            "you": [(Wt("you"), 540, 1100, 1.0), (B["you"]["t1"], 540, 900, 1.12)]}

def impacts(Wt, B):
    return [Wt("sky", "planes") + 2.0]

def sfx(Wt, B, put):
    put(sfx_whoosh(3, 1.4), 0.0, 0.8); put(sfx_boom(50, 1.6), 0.05, 0.5)          # frame-1 splash
    put(sfx_whoosh(4, 2.0), Wt("flood", "flood"), 0.6)
    put(sfx_ding(1200), Wt("sky", "black"), 0.4)
    put(sfx_whoosh(6, 0.6), Wt("sky", "planes") + 1.9, 0.9)
    for i in range(8): put(sfx_pop(300 + 60 * i), Wt("boil", "boil") + i * 0.12, 0.3)
    put(sfx_shatter(), Wt("boil", "freeze"), 0.4)
    t0 = Wt("you", "hope"); t1 = Wt("end", "Could"); n = int((t1 - t0) / 0.5)
    for i in range(n): put(sfx_boom(55, 0.25), t0 + i * 0.5, 0.35)                 # heartbeat while counting down
    put(sfx_whoosh(8, 1.0), t1, 1.0); put(sfx_ding(1568), t1 + 0.6, 0.6)
