"""Nature's Weirdest #2: the Venus flytrap anemone — real NOAA footage + overlays + globe. Hook style A ("Guess what this is").
Facts: deep-sea sea anemone (Actinoscyphia aurelia) named for its resemblance to the Venus flytrap plant; anemones are cnidarians,
relatives of jellyfish and corals; it perches on a stalk facing the current and spreads its tentacles to catch drifting food
(passive suspension feeder); it can close its tentacles to catch prey or defend itself.
Footage: NOAA Office of Ocean Exploration and Research, 2017 American Samoa Expedition (public domain), via Wikimedia Commons.
"""
import math, os
from cartoon import *
import globe
from footage import Clip
from episodes_util import paint_rgba

NAME = "nature_flytrap"
LOOK = "cinematic"
TITLE = "This is NOT a plant 🌺 #shorts"
DESCRIPTION = ("It looks exactly like a Venus flytrap... but it's an animal living in the deep sea. #nature #ocean #deepsea #animals #shorts\n\n"
               "Footage: NOAA Office of Ocean Exploration and Research, 2017 American Samoa Expedition (public domain).\n"
               "Earth imagery: NASA Goddard (Blue Marble), public domain.")
TAGS = ["venus flytrap anemone", "deep sea", "weird animals", "nature", "ocean", "shorts"]
VOICE, SPEED = "am_michael", 1.05
BEATS = [
    ("hook", "Guess what this is.", 2.3),
    ("plant", "A plant? It looks just like a Venus flytrap.", 0.1),
    ("twist", "But it's not a plant at all. It's an animal, a sea anemone, a cousin of jellyfish and corals.", 0.1),
    ("where", "A robot filmed it deep under the sea, off American Samoa.", 0.1),
    ("how", "It perches on a long stalk facing the current, spreading its tentacles to catch food drifting past.", 0.0),
    ("trap", "And to grab a meal... it can fold its tentacles shut, like a trap.", 0.3),
    ("end", "A flytrap that's actually an animal. What should I show you next?", 1.0),
]
CLIP = Clip(os.path.join(ROOT, "assets", "footage", "Venus_Flytrap_Anemone-_2017_American_Samoa.webm"))
BOX = (40, 400, 1000, 850)
CREDIT = "Footage: NOAA Ocean Exploration (public domain)"

def boxed(c, src_t, zoom=1.0, focus=(0.5, 0.5)):
    CLIP.draw_fill(c, src_t)
    CLIP.draw(c, src_t, *BOX, zoom=zoom, focus=focus, radius=40)
    text(c, CREDIT, W / 2, BOX[1] + BOX[3] + 34, 26, WHITE, alpha=0.8)

def flytrap_icon(c, x, y, s, closed=0.0):
    """little cartoon Venus flytrap plant (for comparison)"""
    c.save(); c.translate(x, y); c.scale(s, s)
    c.new_path(); c.move_to(0, 0); c.curve_to(10, 60, -10, 120, 0, 170); c.set_source_rgb(*OUT); c.set_line_width(22); c.stroke()
    c.new_path(); c.move_to(0, 0); c.curve_to(10, 60, -10, 120, 0, 170); c.set_source_rgb(*rgb("#4cc35a")); c.set_line_width(12); c.stroke()
    for sgn in (-1, 1):
        a = sgn * (0.75 - 0.7 * closed)
        c.save(); c.rotate(a)
        c.new_path(); c.move_to(0, 0); c.curve_to(sgn * 0, -60, sgn * 70, -110, sgn * 120, -60); c.close_path(); fs(c, rgb("#7ad15a"), 7)
        for k in range(6):
            px, py = sgn * (20 + k * 18), -60 - 40 * math.sin(math.pi * (k + 0.5) / 6)
            c.new_path(); c.move_to(px, py); c.line_to(px + sgn * 8, py - 26); c.set_source_rgb(*OUT); c.set_line_width(5); c.stroke()
        c.new_path(); c.move_to(sgn * 10, -10); c.curve_to(sgn * 20, -50, sgn * 60, -80, sgn * 100, -55); c.set_source_rgba(1, 0.35, 0.35, 0.8); c.set_line_width(14); c.stroke()
        c.restore()
    c.restore()

def s_hook(c, s):
    t = s.t; tr = 2.0
    if t < tr:   # extreme macro: unrecognisable pink fringe
        CLIP.draw(c, 20.5 + t * 0.4, 0, 0, W, H, zoom=3.6 - t * 0.2, focus=(0.38, 0.38), radius=1, border=False)
        pop_text(c, "GUESS WHAT", W / 2, 360, 120, 1.0, WHITE)
        pop_text(c, "THIS IS", W / 2, 500, 140, 1.0, YEL)
    else:        # whoosh pull-back reveal
        z = lerp(3.2, 1.0, ease_out((t - tr) / 0.6))
        CLIP.draw_fill(c, 20.5 + t * 0.4)
        CLIP.draw(c, 20.5 + t * 0.4, *BOX, zoom=z, focus=(0.38, 0.38), radius=40)
        pop_text(c, "?", 900, 520, 200, s.P(tr + 0.3, 0.3), YEL)
        text(c, CREDIT, W / 2, BOX[1] + BOX[3] + 34, 26, WHITE, alpha=0.8)

def s_plant(c, s):
    t = s.t; tv = s.W("plant", "Venus")
    boxed(c, 27.0 + (t - s.t0) * 0.8, 1.15, (0.45, 0.45))
    pop_text(c, "A PLANT?", W / 2, 300, 110, s.P(s.t0, 0.3), WHITE)
    if t > tv - 0.2:   # side-by-side comparison with a cartoon flytrap
        p = s.P(tv - 0.2, 0.35)
        c.new_path(); rrect(c, 700, 860, 300, 340, 30); fs(c, rgb("#14284a"), 6, 0.9 * p)
        if p > 0.05: flytrap_icon(c, 850, 1150, 1.0 * p)
        label(c, "VENUS FLYTRAP", 850, 1230, 34, rgb("#4cc35a"), OUT, p)

def s_twist(c, s):
    t = s.t; ta = s.W("twist", "animal"); tc = s.W("twist", "cousin")
    boxed(c, 21.0 + (t - s.t0) * 0.6, 1.25, (0.4, 0.4))
    if t < ta - 0.1:
        pop_text(c, "NOT A PLANT", W / 2, 300, 104, s.P(s.t0 + 0.2, 0.3), WHITE)
        c.new_path(); c.move_to(250, 300); c.line_to(830, 300); c.set_source_rgba(*RED, s.P(s.t0 + 0.6, 0.2)); c.set_line_width(16); c.stroke()
    else:
        pop_text(c, "IT'S AN ANIMAL!", W / 2, 300, 110, s.P(ta - 0.1, 0.3), YEL)
    if t > tc - 0.2:
        for i, (lab, col) in enumerate((("JELLYFISH", PINK), ("CORAL", ORANGE))):
            label(c, "COUSIN: " + lab, W / 2, 1150 - i * 90, 42, col, OUT, s.P(tc - 0.2 + i * 0.4, 0.3))

def s_where(c, s):
    t = s.t; ts = s.W("where", "Samoa"); u = clamp((t - s.t0) / 1.8)
    if t < ts + 0.9:
        bg_cinema(c, t)
        R = lerp(430, 2300, ease(u)); lon0 = lerp(150, 189.3, ease(u)); lat0 = lerp(10, -14.3, ease(u))
        paint_rgba(c, globe.render_globe(lon0, lat0, R, W / 2, 960, sun=(-0.3, 0.35, 0.9)))
        x, y, vis = globe.lonlat_to_screen(-170.7, -14.3, lon0, lat0, R, W / 2, 960)
        if vis:
            glow(c, x, y, 180, (1, 0.5, 0.6), 0.6); circle(c, x, y, 16, YEL, 6)
            label(c, "AMERICAN SAMOA", x, y - 110, 54, WHITE, OUT, s.P(ts - 0.15, 0.35))
    else:   # the robot's arm next to the anemone
        boxed(c, 36.0 + (t - ts - 0.9), 1.0, (0.5, 0.5))
        label(c, "NOAA ROBOT ARM", 300, 1150, 46, CYAN, OUT, s.P(ts + 0.9, 0.3))
        arrow(c, (300, 1100), (250, 960), s.P(ts + 1.0, 0.3), CYAN, 10, 24)

def s_how(c, s):
    t = s.t; tsk = s.W("how", "stalk"); tcu = s.W("how", "current"); tf = s.W("how", "food")
    boxed(c, 11.0 + (t - s.t0) * 0.9, 1.0, (0.55, 0.5))
    label(c, "LONG STALK", 300, 1150, 48, YEL, OUT, s.P(tsk - 0.15, 0.3))
    arrow(c, (320, 1100), (500, 900), s.P(tsk, 0.35), YEL, 10, 24)
    if t > tcu - 0.2:   # animated current arrows streaming past
        for k in range(4):
            u = ((t - tcu) * 0.6 + k / 4) % 1; y = 560 + k * 70
            arrow(c, (80 + u * 700, y), (220 + u * 700, y), 1, (0.75, 0.95, 1), 7, 18)
        label(c, "CURRENT", 860, 470, 40, SKY, OUT, s.P(tcu - 0.2, 0.3))
    if t > tf - 0.2:
        for k in range(10):  # drifting food specks
            u = ((t - tf) * 0.5 + k / 10) % 1
            circle(c, 100 + u * 800, 620 + 40 * math.sin(k * 2 + t), 6, (1, 0.95, 0.7), 0, 0.9 * math.sin(math.pi * u))

def s_trap(c, s):
    t = s.t; tsh = s.W("trap", "shut")
    boxed(c, 44.5 + (t - s.t0) * 0.7, 1.35, (0.45, 0.42))
    p = s.P(tsh - 0.3, 0.35)                 # diagram: tentacles folding shut (no closing shot exists in the footage)
    if p > 0:
        c.new_path(); rrect(c, 680, 820, 330, 380, 30); fs(c, rgb("#14284a"), 6, 0.92 * p)
        cl = ease(clamp((t - tsh) / 0.5))
        cx, cy = 845, 1060
        for sgn in (-1, 1):
            c.save(); c.translate(cx, cy); c.rotate(sgn * (1.2 - 1.05 * cl))
            for k in range(7):
                a = -math.pi / 2 + sgn * (k - 3) * 0.12
                c.new_path(); c.move_to(0, 0); c.line_to(math.cos(a) * 120, math.sin(a) * 120)
                c.set_source_rgba(1, 0.6, 0.65, p); c.set_line_width(9); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke()
            c.restore()
        circle(c, cx, cy + 10, 20, rgb("#ff7a8a"), 5, p)
        c.new_path(); c.move_to(cx, cy + 30); c.line_to(cx, cy + 130); c.set_source_rgba(0.7, 0.5, 0.35, p); c.set_line_width(10); c.stroke()
        text(c, "CLOSES", cx, cy + 165, 34, WHITE, alpha=p)
    if t > tsh: pop_text(c, "SNAP!", 380, 1120, 120, s.P(tsh, 0.25) * (1 - clamp((t - tsh - 1.4) / 0.3)), YEL)

def s_end(c, s):
    t = s.t; tq = s.W("end", "What")
    boxed(c, 28.0 + (t - s.t0) * 0.8, 1.15, (0.45, 0.45))
    pop_text(c, "FLYTRAP OR ANIMAL?", W / 2, 300, 84, s.P(s.t0 + 0.2, 0.3), YEL)
    pop_text(c, "COMMENT AN ANIMAL!", W / 2, 1180, 64, s.P(tq, 0.3), WHITE)
    leo(c, 930, 2050, 0.5, "point_left", "wow", t)

SCENES = [("hook", s_hook), ("plant", s_plant), ("twist", s_twist), ("where", s_where), ("how", s_how), ("trap", s_trap), ("end", s_end)]

def impacts(Wt, B):
    return [2.0, Wt("twist", "animal")]

def sfx(Wt, B, put):
    put(sfx_boom(45, 1.6), 0.0, 0.4)
    put(sfx_whoosh(3, 0.6), 1.8, 1.0)
    put(sfx_pop(), Wt("plant", "Venus"), 0.5)
    put(sfx_ding(1500), Wt("twist", "cousin"), 0.4)
    put(sfx_whoosh(5, 1.2), Wt("where"), 0.5); put(sfx_ding(1800), Wt("where", "Samoa"), 0.4)
    put(sfx_pop(500), Wt("how", "stalk"), 0.4)
    put(sfx_pop(1100), Wt("trap", "shut"), 0.9)
    put(sfx_ding(1568), Wt("end", "What"), 0.5)
