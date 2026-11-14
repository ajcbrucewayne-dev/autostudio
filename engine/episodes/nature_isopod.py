"""Nature's Weirdest #3: the giant isopod (same script structure as #2) — real NOAA footage + overlays + globe. Hook style A ("Guess what this is").
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

NAME = "nature_isopod"
LOOK = "cinematic"
TITLE = "Guess what this is 🦐 #shorts"
DESCRIPTION = ("A giant cousin of the woodlice in your garden... that can skip meals for years. #nature #deepsea #ocean #animals #shorts\n\n"
               "Footage: NOAA Office of Ocean Exploration and Research, Gulf of Mexico 2017 (public domain).\n"
               "Earth imagery: NASA Goddard (Blue Marble), public domain.")
TAGS = ["giant isopod", "deep sea", "weird animals", "nature", "ocean", "shorts"]
VOICE, SPEED = "am_michael", 1.05
BEATS = [
    ("hook", "Guess what this is.", 2.3),
    ("plant", "An armadillo? Something from a sci-fi movie?", 0.1),
    ("twist", "Close... It's a giant isopod, a cousin of the tiny woodlice in your garden. But it can grow up to fifty centimeters long.", 0.1),
    ("where", "A NOAA robot filmed this one deep in the Gulf of Mexico.", 0.1),
    ("how", "It crawls across the dark sea floor, scavenging dead fish and anything that sinks from above.", 0.0),
    ("trap", "And it can go years without food. One in a Japanese aquarium refused to eat for over four years.", 0.3),
    ("end", "A giant woodlouse that can skip meals for years. What should I show you next?", 1.0),
]
CLIP = Clip(os.path.join(ROOT, "assets", "footage", "Bathynomus_giganteus.webm"))
BOX = (40, 400, 1000, 850)
CREDIT = "Footage: NOAA Ocean Exploration (public domain)"

def boxed(c, src_t, zoom=1.0, focus=(0.5, 0.5)):
    CLIP.draw_fill(c, src_t)
    CLIP.draw(c, src_t, *BOX, zoom=zoom, focus=focus, radius=40)
    text(c, CREDIT, W / 2, BOX[1] + BOX[3] + 34, 26, WHITE, alpha=0.8)

def woodlouse(c, x, y, s, col=GREY):
    """tiny cartoon woodlouse icon"""
    c.save(); c.translate(x, y); c.scale(s, s)
    c.new_path(); c.save(); c.scale(1.5, 1); c.arc(0, 0, 40, math.pi, 2 * math.pi); c.restore(); c.close_path(); fs(c, col, 5)
    for k in range(5): c.new_path(); c.move_to(-48 + k * 24, -2); c.line_to(-40 + k * 22, -36); c.set_source_rgb(*OUT); c.set_line_width(4); c.stroke()
    c.new_path(); c.move_to(60, -8); c.line_to(85, -30); c.set_source_rgb(*OUT); c.set_line_width(4); c.stroke()
    c.restore()

def s_hook(c, s):
    t = s.t; tr = 2.0
    if t < tr:   # extreme macro on the armoured shell: unrecognisable
        CLIP.draw(c, 35.0 + t * 0.4, 0, 0, W, H, zoom=3.4 - t * 0.2, focus=(0.42, 0.45), radius=1, border=False)
        pop_text(c, "GUESS WHAT", W / 2, 360, 120, 1.0, WHITE)
        pop_text(c, "THIS IS", W / 2, 500, 140, 1.0, YEL)
    else:
        z = lerp(3.0, 1.0, ease_out((t - tr) / 0.6))
        CLIP.draw_fill(c, 35.0 + t * 0.4)
        CLIP.draw(c, 35.0 + t * 0.4, *BOX, zoom=z, focus=(0.42, 0.45), radius=40)
        pop_text(c, "?", 900, 520, 200, s.P(tr + 0.3, 0.3), YEL)
        text(c, CREDIT, W / 2, BOX[1] + BOX[3] + 34, 26, WHITE, alpha=0.8)

def s_plant(c, s):
    t = s.t; ts = s.W("plant", "Something")
    boxed(c, 28.5 + (t - s.t0) * 0.8, 1.05, (0.5, 0.5))
    pop_text(c, "AN ARMADILLO?", W / 2, 300, 100, s.P(s.t0, 0.3), WHITE)
    if t > ts - 0.2: pop_text(c, "AN ALIEN?", W / 2, 1180, 100, s.P(ts - 0.2, 0.3), YEL)

def s_twist(c, s):
    t = s.t; ti = s.W("twist", "isopod"); tw = s.W("twist", "woodlice"); tf = s.W("twist", "fifty")
    boxed(c, 44.0 + (t - s.t0) * 0.5, 1.1, (0.5, 0.5))
    if t < ti - 0.1: pop_text(c, "CLOSE...", W / 2, 300, 110, s.P(s.t0 + 0.1, 0.3), WHITE)
    else: pop_text(c, "GIANT ISOPOD!", W / 2, 300, 110, s.P(ti - 0.1, 0.3), YEL)
    if t > tw - 0.2:   # size comparison panel: garden woodlouse vs giant isopod
        p = s.P(tw - 0.2, 0.35)
        c.new_path(); rrect(c, 90, 900, 900, 330, 30); fs(c, rgb("#14284a"), 6, 0.92 * p)
        if p > 0.05:
            woodlouse(c, 230, 1070, 0.7 * p); text(c, "WOODLOUSE ~1 cm", 230, 1150, 34, WHITE, alpha=p)
            grow = ease(s.P(tf - 0.2, 0.8))
            woodlouse(c, 660, 1080, max(0.35, 2.8 * grow) * p, rgb("#c8c3e6"))
            if grow > 0: text(c, "UP TO ~50 cm", 660, 1180, 40, YEL, alpha=grow)

def s_where(c, s):
    t = s.t; tg = s.W("where", "Gulf"); u = clamp((t - s.t0) / 1.8)
    if t < tg + 1.0:
        bg_cinema(c, t)
        R = lerp(430, 2200, ease(u)); lon0 = lerp(-40, -90.0, ease(u)); lat0 = lerp(10, 26.0, ease(u))
        paint_rgba(c, globe.render_globe(lon0, lat0, R, W / 2, 960, sun=(-0.3, 0.35, 0.9)))
        x, y, vis = globe.lonlat_to_screen(-90.0, 26.0, lon0, lat0, R, W / 2, 960)
        if vis:
            glow(c, x, y, 180, (0.5, 0.8, 1), 0.6); circle(c, x, y, 16, YEL, 6)
            label(c, "GULF OF MEXICO", x, y - 110, 54, WHITE, OUT, s.P(tg - 0.15, 0.35))
    else:
        boxed(c, 4.0 + (t - tg - 1.0), 1.0, (0.5, 0.5))
        label(c, "NOAA ROBOT VIEW", W / 2, 1180, 46, CYAN, OUT, s.P(tg + 1.0, 0.3))

def s_how(c, s):
    t = s.t; tsc = s.W("how", "scavenging"); tsk = s.W("how", "sinks")
    boxed(c, 15.0 + (t - s.t0) * 1.0, 1.35, (0.45, 0.5))
    label(c, "SCAVENGER", W / 2, 300, 70, YEL, OUT, s.P(tsc - 0.1, 0.3))
    if t > tsk - 0.4:   # food sinking from above
        for k in range(3):
            u = clamp((t - tsk + 0.4 - k * 0.35) / 2.0); x = 300 + k * 230; y = lerp(380, 1000, ease(u))
            if u > 0:
                c.save(); c.translate(x, y); c.rotate(0.3 * math.sin(t * 2 + k))
                c.new_path(); c.move_to(-60, 0); c.line_to(40, 0); c.set_source_rgb(1, 1, 1); c.set_line_width(7); c.stroke()
                for j in range(4): c.new_path(); c.move_to(-40 + j * 20, -22); c.line_to(-40 + j * 20, 22); c.set_line_width(5); c.stroke()
                c.new_path(); path(c, [(40, 0), (75, -24), (75, 24)]); fs(c, WHITE, 4)
                c.restore()
        text(c, "FOOD FALLS FROM ABOVE", W / 2, 1180, 48, WHITE, alpha=s.P(tsk, 0.3))

def s_trap(c, s):
    t = s.t; tj = s.W("trap", "Japanese"); tf = s.W("trap", "four")
    boxed(c, 48.0 + (t - s.t0) * 0.6, 1.2, (0.5, 0.5))
    pop_text(c, "NO FOOD FOR YEARS", W / 2, 300, 88, s.P(s.t0 + 0.2, 0.3), YEL)
    if t > tj - 0.2:
        p = s.P(tj - 0.2, 0.35)
        c.new_path(); rrect(c, 140, 930, 800, 300, 30); fs(c, rgb("#14284a"), 6, 0.92 * p)
        days = 1500 * ease(clamp((t - tj) / 2.2))
        text(c, f"{days:,.0f} DAYS", W / 2, 1040, 110, WHITE, alpha=p)
        text(c, "WITHOUT EATING · TOBA AQUARIUM, JAPAN", W / 2, 1160, 32, SKY, alpha=p)
    if t > tf: pop_text(c, "4+ YEARS!", 820, 860, 80, s.P(tf, 0.3), RED)

def s_end(c, s):
    t = s.t; tq = s.W("end", "What")
    boxed(c, 30.0 + (t - s.t0) * 0.6, 1.1, (0.5, 0.5))
    pop_text(c, "GIANT WOODLOUSE!", W / 2, 300, 96, s.P(s.t0 + 0.2, 0.3), YEL)
    pop_text(c, "COMMENT AN ANIMAL!", W / 2, 1180, 64, s.P(tq, 0.3), WHITE)
    leo(c, 930, 2050, 0.5, "point_left", "wow", t)

SCENES = [("hook", s_hook), ("plant", s_plant), ("twist", s_twist), ("where", s_where), ("how", s_how), ("trap", s_trap), ("end", s_end)]

def impacts(Wt, B):
    return [2.0, Wt("twist", "isopod")]

def sfx(Wt, B, put):
    put(sfx_boom(45, 1.6), 0.0, 0.4)
    put(sfx_whoosh(3, 0.6), 1.8, 1.0)
    put(sfx_pop(), Wt("plant", "Something"), 0.5)
    put(sfx_ding(1500), Wt("twist", "fifty"), 0.4)
    put(sfx_whoosh(5, 1.2), Wt("where"), 0.5); put(sfx_ding(1800), Wt("where", "Gulf"), 0.4)
    put(sfx_pop(500), Wt("how", "scavenging"), 0.4)
    for i in range(12): put(sfx_tick(), Wt("trap", "Japanese") + i * 0.18, 0.5)
    put(sfx_boom(55, 0.8), Wt("trap", "four"), 0.6)
    put(sfx_ding(1568), Wt("end", "What"), 0.5)
