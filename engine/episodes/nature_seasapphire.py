"""Nature's Weirdest #1: The animal that can turn invisible (the sea sapphire, Sapphirina copepods).
Facts (Gur et al., J. Am. Chem. Soc. 2015, Weizmann Institute): males carry layers of thin hexagonal guanine crystal plates;
the spacing between layers sets the reflected colour; at certain viewing angles (~45° in one species) the reflection shifts into
the ultraviolet and the animal practically disappears; females are translucent. Purpose (mating display / hiding) is not proven.
"""
import math
from cartoon import *

NAME = "nature_seasapphire"
LOOK = "cinematic"
TITLE = "This animal can turn INVISIBLE 💎 #shorts"
DESCRIPTION = ("The sea sapphire sparkles like a jewel... then vanishes. Here's the crystal trick behind it. "
               "#nature #animals #ocean #science #shorts")
TAGS = ["sea sapphire", "invisible animal", "nature", "ocean", "weird animals", "shorts"]
VOICE, SPEED = "am_michael", 1.05
HOOK = ("THIS ANIMAL CAN", "TURN INVISIBLE")
BEATS = [
    ("hook", "This tiny animal can turn completely invisible... in the blink of an eye.", 0.3),
    ("meet", "Meet the sea sapphire. It's just a few millimeters long, and it sparkles like a jewel in the open ocean.", 0.0),
    ("crystals", "Its back is covered in tiny hexagon-shaped crystals, made of guanine, one of the building blocks of your DNA.", 0.0),
    ("trick", "The gap between the layers decides which color it reflects. But when it tilts its body, the light shifts into ultraviolet, a color our eyes can't see. And just like that... it vanishes.", 0.6),
    ("why", "Only the males can do this. Scientists think the sparkle helps them find a mate, while vanishing hides them from hungry fish.", 0.0),
    ("end", "So next time you look at an empty ocean... is it really empty? Which weird animal should I show you next?", 0.9),
]

# ---------------- ocean kit
def bg_ocean(c, t, top="#0b3a78", bot="#020a1f"):
    c.save(); c.identity_matrix()
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, *rgb(top)); g.add_color_stop_rgb(1, *rgb(bot)); c.set_source(g); c.paint(); c.restore()
    god_rays(c, 540, -200, t, n=8, length=2200, col=(0.6, 0.85, 1), alpha=0.07, spread=0.9, ang=math.pi / 2)
    rng = np.random.default_rng(11)
    for i in range(70):  # marine snow drifting down
        x = rng.uniform(0, W); sp = rng.uniform(12, 30); y = (rng.uniform(0, H) + t * sp) % (H + 40) - 20
        c.new_path(); c.arc(x + math.sin(t + i) * 8, y, rng.uniform(1.5, 3.5), 0, 2 * math.pi); c.set_source_rgba(0.85, 0.95, 1, 0.45); c.fill()

def hue(h):
    """sapphire palette cycling blue -> violet -> gold -> cyan"""
    stops = [rgb("#2f7dff"), rgb("#7a4dff"), rgb("#ffcf3a"), rgb("#33e0d0"), rgb("#2f7dff")]
    h = h % 1 * 4; i = int(h); return mix(stops[i], stops[i + 1], h - i)

def sapphire(c, x, y, s, t, vis=1.0, ang=0.0, female=False, sparkle=1.0):
    """Sea sapphire: flat oval copepod with a mosaic of iridescent hexagon plates. vis 0..1 fades it out (UV trick)."""
    if vis <= 0.01: return
    c.save(); c.translate(x, y); c.rotate(ang); c.scale(s, s)
    if not female: glow(c, 0, 0, 260, hue(t * 0.15), 0.55 * vis * sparkle)
    # antennae + tail
    for sx in (-1, 1):
        c.new_path(); c.move_to(sx * 40, -150); c.curve_to(sx * 120, -230, sx * 200, -220, sx * 260, -170 + 10 * math.sin(t * 3 + sx))
        c.set_source_rgba(0.85, 0.95, 1, 0.8 * vis); c.set_line_width(7); c.stroke()
        c.new_path(); c.move_to(sx * 18, 150); c.line_to(sx * 45, 260); c.set_source_rgba(0.85, 0.95, 1, 0.8 * vis); c.set_line_width(10); c.stroke()
    body = [(math.cos(a) * 120 * (1 - 0.18 * math.sin(a)), math.sin(a) * 175) for a in np.linspace(0, 2 * math.pi, 60)]
    c.new_path(); path(c, body)
    if female:
        c.set_source_rgba(0.8, 0.95, 1, 0.18 * vis); c.fill_preserve(); c.set_source_rgba(0.85, 0.95, 1, 0.7 * vis); c.set_line_width(5); c.stroke()
    else:
        c.save(); c.clip()
        for row in range(-6, 7):
            for col in range(-5, 6):
                hx, hy = col * 46 + (23 if row % 2 else 0), row * 40
                k = hue(t * 0.18 + (hx + hy) * 0.002 + 0.25 * math.sin(t * 2 + col * 0.7 + row))
                tw = 0.55 + 0.45 * math.sin(t * 5 + col * 1.7 + row * 2.3)
                hexa = [(hx + 24 * math.cos(math.pi / 3 * i + math.pi / 6), hy + 24 * math.sin(math.pi / 3 * i + math.pi / 6)) for i in range(6)]
                c.new_path(); path(c, hexa); c.set_source_rgba(*mix(k, WHITE, 0.25 * tw * sparkle), vis); c.fill_preserve()
                c.set_source_rgba(0.05, 0.08, 0.2, 0.6 * vis); c.set_line_width(3); c.stroke()
        c.restore()
        c.new_path(); path(c, body); c.set_source_rgba(1, 1, 1, 0.9 * vis); c.set_line_width(6); c.stroke()
        for i in range(5):  # segment lines
            yy = -110 + i * 55; c.new_path(); c.move_to(-110, yy); c.curve_to(-40, yy + 18, 40, yy + 18, 110, yy)
            c.set_source_rgba(1, 1, 1, 0.35 * vis); c.set_line_width(4); c.stroke()
        for k in range(4):  # star glints
            u = (t * 0.9 + k * 0.27) % 1; gx, gy = math.sin(k * 2.1) * 80, math.cos(k * 1.7) * 120
            sz = 30 * math.sin(math.pi * u) * sparkle
            if sz > 2: star(c, gx, gy, sz, WHITE, 0, rot=t)
    for sx in (-1, 1): circle(c, sx * 34, -128, 9, OUT, 0, vis)  # little eyes
    c.restore()

def diver_mask(c, x, y, s):
    """snorkel mask over Leo's eyes; (x, y, s) = the same feet position / scale passed to leo()"""
    hx, hy = x, y - 575 * s
    c.save(); c.translate(hx, hy); c.scale(s, s)
    c.new_path(); c.move_to(-160, 0); c.line_to(160, 0); c.set_source_rgb(*rgb("#1b6b8f")); c.set_line_width(26); c.stroke()
    c.new_path(); rrect(c, -125, -55, 250, 120, 50); c.set_source_rgba(0.75, 0.95, 1, 0.35); c.fill_preserve()
    c.set_source_rgb(*rgb("#1b6b8f")); c.set_line_width(18); c.stroke()
    c.new_path(); c.move_to(-80, -40); c.line_to(-40, -40); c.set_source_rgba(1, 1, 1, 0.8); c.set_line_width(8); c.stroke()
    c.new_path(); c.move_to(150, 40); c.line_to(170, -170); c.line_to(130, -200); c.set_source_rgb(*OUT); c.set_line_width(28); c.stroke()   # snorkel
    c.new_path(); c.move_to(150, 40); c.line_to(170, -170); c.line_to(130, -200); c.set_source_rgb(*ORANGE); c.set_line_width(16); c.stroke()
    c.restore()

def explorer(c, x, y, s, pose, face, t, look=(0, 0)):
    leo(c, x, y + math.sin(t * 1.4) * 10, s, pose, face, t, look=look, bob=False)
    diver_mask(c, x, y + math.sin(t * 1.4) * 10, s)

def fish(c, x, y, s, t, mood="hungry"):
    c.save(); c.translate(x, y); c.scale(s, s)
    c.new_path(); path(c, [(120, 0), (180, -70), (180, 70)]); fs(c, ORANGE, 8)
    c.new_path(); c.save(); c.scale(1.5, 1); c.arc(0, 0, 100, 0, 2 * math.pi); c.restore(); fs(c, rgb("#ff7a3a"), 8)
    circle(c, -80, -30, 26, WHITE, 6); circle(c, -86 if mood == "hungry" else -70, -30, 12, OUT, 0)
    c.new_path()
    if mood == "hungry": c.move_to(-150, 20); c.line_to(-110, 40); c.line_to(-150, 55)
    else: c.arc(-130, 40, 12, 0, 2 * math.pi)
    c.set_source_rgb(*OUT); c.set_line_width(8); c.stroke()
    c.restore()

def rice(c, x, y, s):
    c.save(); c.translate(x, y); c.rotate(0.3); c.scale(s, s); c.new_path(); c.save(); c.scale(1, 2.2); c.arc(0, 0, 22, 0, 2 * math.pi); c.restore()
    fs(c, rgb("#fff6e0"), 5); c.restore()

# ---------------- scenes
def s_hook(c, s):
    t = s.t; tb = s.W("hook", "blink")
    bg_ocean(c, t)
    vis = 1 - ease((t - tb) / 0.35) if t > tb else 1.0
    sapphire(c, 540, 820, 1.25, t, vis, ang=0.15 * math.sin(t))
    if t > tb:
        bubbles_burst(c, 540, 820, t - tb)
        pop_text(c, "?!", 540, 820, 160, clamp((t - tb - 0.4) / 0.3), YEL)
    explorer(c, 540, 2120, 0.75, "shock" if t > tb else "idle", "shock" if t > tb else "wow", t, look=(0, -0.8))

def bubbles_burst(c, x, y, lt):
    for i in range(12):
        a = i * 0.52; d = ease_out(lt / 1.0) * 220
        circle(c, x + math.cos(a) * d, y + math.sin(a) * d - lt * 120, 14 * (1 - clamp(lt / 1.4)), (0.9, 0.98, 1), 3, 1 - clamp(lt / 1.4))

def s_meet(c, s):
    t = s.t; tm = s.W("meet", "millimeters"); tj = s.W("meet", "jewel")
    bg_ocean(c, t)
    z = ease(s.P(s.t0, 1.4))
    sapphire(c, 560, 760, lerp(0.15, 1.05, z), t)
    label(c, "SEA SAPPHIRE", 540, 330, 64, YEL, OUT, s.P(s.W("meet", "sapphire") - 0.1, 0.35))
    if t > tm - 0.3:
        p = s.P(tm - 0.3, 0.4)
        c.new_path(); rrect(c, 640, 1060, 360, 220, 30); fs(c, rgb("#0d2b55"), 6, 0.85 * p)
        sapphire(c, 740, 1170, max(0.28 * p, 1e-3), t); rice(c, 900, 1170, max(1.6 * p, 1e-3))
        text(c, "≈ RICE GRAIN", 820, 1250, 34, WHITE, alpha=p)
    if t > tj - 0.2:
        for k in range(6):
            u = ((t - tj) * 0.8 + k / 6) % 1; a = k * 1.05 + t * 0.3
            star(c, 560 + math.cos(a) * 300, 760 + math.sin(a) * 340, 26 * math.sin(math.pi * u), WHITE, 0, t)
    explorer(c, 230, 2080, 0.66, "point_right", "wow", t, look=(0.7, -0.8))

def s_crystals(c, s):
    t = s.t; tg = s.W("crystals", "guanine"); tdna = s.W("crystals", "DNA")
    bg_ocean(c, t, "#081c44", "#020613")
    # extreme close-up: honeycomb of crystal plates, layers sliding in on top of each other
    for layer in range(3):
        lp = ease(s.P(s.t0 + 0.3 + layer * 0.7, 0.8)); off = (1 - lp) * 700 * (1 if layer % 2 else -1)
        for row in range(-5, 6):
            for col in range(-4, 5):
                hx = 540 + col * 120 + (60 if row % 2 else 0) + off + layer * 18; hy = 820 + row * 104 + layer * 14
                k = hue(t * 0.12 + (col + row) * 0.04 + layer * 0.2)
                hexa = [(hx + 58 * math.cos(math.pi / 3 * i + math.pi / 6), hy + 58 * math.sin(math.pi / 3 * i + math.pi / 6)) for i in range(6)]
                c.new_path(); path(c, hexa); c.set_source_rgba(*k, 0.35 + 0.2 * layer); c.fill_preserve()
                c.set_source_rgba(1, 1, 1, 0.5 * lp); c.set_line_width(4); c.stroke()
    label(c, "HEXAGON CRYSTALS", 540, 330, 58, WHITE, OUT, s.P(s.W("crystals", "hexagon") - 0.1, 0.35))
    if t > tg - 0.2:
        label(c, "GUANINE", 300, 1230, 60, YEL, OUT, s.P(tg - 0.2, 0.35))
    if t > tdna - 0.4:   # DNA ladder
        p = s.P(tdna - 0.4, 0.5)
        c.save(); c.translate(820, 1230); c.scale(max(p, 1e-3), max(p, 1e-3))
        for i in range(9):
            yy = -160 + i * 40; dx = 60 * math.sin(i * 0.8 + t * 2)
            c.new_path(); c.move_to(-dx, yy); c.line_to(dx, yy); c.set_source_rgb(*(YEL if i % 3 == 0 else WHITE)); c.set_line_width(8); c.stroke()
            circle(c, -dx, yy, 11, CYAN, 4); circle(c, dx, yy, 11, PINK, 4)
        c.restore()

def s_trick(c, s):
    t = s.t; tg = s.W("trick", "gap"); tt = s.W("trick", "tilts"); tu = s.W("trick", "ultraviolet"); tv = s.W("trick", "vanishes")
    bg_ocean(c, t)
    if t < tt - 0.3:   # side view of the stacked plates reflecting a ray; colour changes with the gap
        gap = 30 + 18 * math.sin((t - tg) * 2.2)
        for i in range(5):
            y = 760 + i * gap; c.new_path(); rrect(c, 260, y, 560, 16, 8); fs(c, rgb("#bfe6ff"), 4)
        col = hue((gap - 12) / 80)
        arrow(c, (120, 420), (500, 740), 1, WHITE, 12, 28)
        arrow(c, (560, 740), (960, 420), s.P(tg, 0.5), col, 16, 34)
        label(c, "GAP = COLOR", 540, 1100, 56, WHITE, OUT, s.P(tg, 0.35))
    else:
        tilt = ease(s.P(tt - 0.3, 1.2)) * 0.8
        vis = 1 - ease((t - tv + 0.2) / 0.5) if t > tv - 0.2 else 1.0
        col = mix(hue(t * 0.15), PURPLE, clamp((t - tu + 0.3) / 0.6))
        arrow(c, (120, 330), (430, 640), 1, WHITE, 12, 28)
        if t > tu - 0.2 and vis > 0.05: arrow(c, (560, 660), (980, 300), 1, PURPLE, 16, 34)
        sapphire(c, 540, 800, 1.05, t, vis, ang=tilt, sparkle=1 - clamp((t - tu) / 0.8))
        if t > tu - 0.2:
            label(c, "ULTRAVIOLET", 760, 230, 52, PURPLE, WHITE, s.P(tu - 0.2, 0.35))
            # crossed-out eye: we can't see UV
            ex, ey = 300, 230; c.save(); c.translate(ex, ey); c.scale(max(1e-3, s.P(tu, 0.3)), max(1e-3, s.P(tu, 0.3)))
            c.new_path(); c.move_to(-60, 0); c.curve_to(-20, -45, 20, -45, 60, 0); c.curve_to(20, 45, -20, 45, -60, 0); fs(c, WHITE, 7)
            circle(c, 0, 0, 20, OUT, 0); c.new_path(); c.move_to(-60, 50); c.line_to(60, -50); c.set_source_rgb(*RED); c.set_line_width(12); c.stroke(); c.restore()
        if t > tv - 0.2: bubbles_burst(c, 540, 800, t - tv + 0.2)
    explorer(c, 540, 2120, 0.72, "idle" if t < tv else "shock", "curious" if t < tv else "shock", t, look=(0, -0.8))

def s_why(c, s):
    t = s.t; tm = s.W("why", "mate"); tf = s.W("why", "hungry")
    bg_ocean(c, t)
    male_vis = 1 - ease((t - tf + 0.4) / 0.4) if t > tf - 0.4 else 1.0
    sapphire(c, 330, 760, 0.62, t, male_vis, ang=-0.2)
    sapphire(c, 790, 820, 0.55, t, 1.0, ang=0.25, female=True)
    label(c, "MALE", 330, 1020, 46, YEL, OUT, s.P(s.t0 + 0.3, 0.3) * max(0.0, male_vis))
    label(c, "FEMALE", 790, 1060, 46, WHITE, OUT, s.P(s.t0 + 0.3, 0.3))
    if t > tm - 0.2:
        for k in range(3):
            u = ((t - tm) * 1.2 + k / 3) % 1; c.new_path(); c.move_to(450 + u * 230, 760 - 40 * math.sin(math.pi * u))
            c.set_source_rgba(1, 0.5, 0.7, 1 - u); c.set_font_size(60); c.show_text("♥")
    if t > tf - 1.2:
        fx = lerp(-250, 330, ease((t - tf + 1.2) / 1.2))
        fish(c, fx, 600, 0.9, t, "hungry" if t < tf + 0.3 else "confused")
        if t > tf + 0.3: pop_text(c, "?", fx - 40, 430, 120, s.P(tf + 0.3, 0.3), YEL)
    explorer(c, 540, 2120, 0.7, "point_left" if t < tf else "cheer", "happy" if t < tf else "wow", t)

def s_end(c, s):
    t = s.t; ti = s.W("end", "really"); tq = s.W("end", "Which")
    bg_ocean(c, t, "#06244f", "#01050f")
    if t > ti - 0.1:   # thousands of hidden sea sapphires flash on for a moment
        rng = np.random.default_rng(3); f = math.sin(math.pi * clamp((t - ti + 0.1) / 1.4))
        for i in range(160):
            x, y = rng.uniform(40, W - 40), rng.uniform(250, 1280); k = hue(rng.uniform(0, 1) + t * 0.2)
            glow(c, x, y, 26, k, 0.9 * f); circle(c, x, y, 5, mix(k, WHITE, 0.4), 0, f)
    pop_text(c, "IS IT REALLY EMPTY?", W / 2, 420, 76, s.P(ti + 0.6, 0.35), YEL)
    pop_text(c, "COMMENT AN ANIMAL!", W / 2, 560, 68, s.P(tq, 0.35), WHITE)
    explorer(c, 540, 2120, 0.78, "idle" if t < ti else "shock", "curious" if t < ti else "shock", t, look=(0, -0.8))

SCENES = [("hook", s_hook), ("meet", s_meet), ("crystals", s_crystals), ("trick", s_trick), ("why", s_why), ("end", s_end)]

def cams(Wt, B):
    return {"hook": [(0, 540, 860, 1.12), (Wt("hook", "blink"), 540, 900, 1.2), (B["hook"]["t1"], 540, 960, 1.0)],
            "meet": [(Wt("meet"), 560, 800, 1.3), (Wt("meet", "millimeters"), 540, 960, 1.0)],
            "crystals": [(Wt("crystals"), 540, 860, 1.25), (B["crystals"]["t1"], 540, 960, 1.0)],
            "end": [(Wt("end"), 540, 960, 1.0), (Wt("end", "really"), 540, 860, 0.92)]}

def impacts(Wt, B):
    return [Wt("trick", "vanishes")]

def sfx(Wt, B, put):
    for i in range(5): put(sfx_ding(1800 + i * 220), 0.05 + i * 0.25, 0.25)          # opening shimmer
    put(sfx_pop(900), Wt("hook", "blink"), 0.8)
    put(sfx_pop(), Wt("meet", "millimeters"), 0.5)
    for i in range(3): put(sfx_ding(2400 - i * 300), Wt("crystals") + 0.3 + i * 0.7, 0.35)
    put(sfx_ding(1100), Wt("crystals", "DNA"), 0.4)
    put(sfx_whoosh(5, 0.8), Wt("trick", "tilts"), 0.5)
    put(sfx_pop(1200), Wt("why", "hungry") + 0.3, 0.6)
    for i in range(6): put(sfx_ding(1600 + i * 300), Wt("end", "really") + i * 0.09, 0.25)
