"""Format test: real public-domain NOAA footage + our motion-graphics overlays + globe (≈12 s).
Footage: NOAA Office of Ocean Exploration and Research, "Psychedelic Medusa", Océano Profundo 2018 (Okeanos Explorer),
public domain (work of the US federal government), via Wikimedia Commons.
"""
import math, os
from cartoon import *
import globe
from footage import Clip

NAME = "footage_test"
LOOK = "cinematic"
VOICE, SPEED = "am_michael", 1.05
HOOK = ("THIS IS NOT CGI", "IT'S A REAL ANIMAL")
BEATS = [
    ("hook", "This isn't CGI. It's a real animal... filmed deep below the ocean.", 0.2),
    ("name", "Scientists call it the psychedelic medusa.", 0.1),
    ("where", "A robot camera found it near Puerto Rico, in 2018.", 0.6),
]
CLIP = Clip(os.path.join(ROOT, "assets", "footage", "Okeanos_Explorer_PR_and_USVI_Dive_8-_Psychedelic_Medusa-NOAA-1280x720.webm"))
BOX = (40, 400, 1000, 850)      # x, y, w, h of the main footage window (tall crop of the 16:9 clip)

def footage(c, s, src_t, zoom, focus):
    CLIP.draw_fill(c, src_t)
    CLIP.draw(c, src_t, *BOX, zoom=zoom, focus=focus, radius=40)
    text(c, "Footage: NOAA Ocean Exploration (public domain)", W / 2, BOX[1] + BOX[3] + 34, 26, WHITE, alpha=0.8)

def s_hook(c, s):
    t = s.t
    footage(c, s, 44.0 + t, 1.0 + 0.05 * t, (0.5, 0.45))
    k = 0.5 + 0.5 * math.sin(t * 5)
    ring(c, 560, 800, 290 + 15 * k, YEL, 8, 0.7)
    label(c, "REAL FOOTAGE", W / 2, BOX[1] + 70, 46, RED, WHITE, s.P(s.W("hook", "real") - 0.1, 0.3))

def s_name(c, s):
    t = s.t
    footage(c, s, 38.0 + (t - s.t0), 1.15, (0.5, 0.45))
    lp = s.P(s.W("name", "psychedelic") - 0.1, 0.35)
    arrow(c, (420, 1120), (660, 860), lp, YEL, 12, 28)
    label(c, "PSYCHEDELIC MEDUSA", W / 2, 1180, 56, YEL, OUT, lp)

def s_where(c, s):
    t = s.t; tp = s.W("where", "Puerto"); u = clamp((t - s.t0) / 1.6)
    if t < tp + 1.0:
        bg_cinema(c, t)
        from episodes_util import paint_rgba
        R = lerp(430, 2400, ease(u)); lon0 = lerp(-40, -66.5, ease(u)); lat0 = lerp(10, 18.2, ease(u))
        paint_rgba(c, globe.render_globe(lon0, lat0, R, W / 2, 960))
        x, y, vis = globe.lonlat_to_screen(-66.5, 18.2, lon0, lat0, R, W / 2, 960)
        if vis:
            glow(c, x, y, 160, (1, 0.5, 0.7), 0.6); circle(c, x, y, 16, YEL, 6)
            label(c, "PUERTO RICO", x, y - 110, 54, WHITE, OUT, s.P(tp - 0.1, 0.35))
    else:
        footage(c, s, 48.0 + (t - tp - 1.0), 1.25, (0.5, 0.45))
        label(c, "FOUND 2018", W / 2, BOX[1] + 70, 50, CYAN, OUT, s.P(tp + 1.0, 0.3))
    leo(c, 930, 2050, 0.5, "point_left" if t > tp + 1.0 else "idle", "wow", t, look=(-0.8, -0.5))

SCENES = [("hook", s_hook), ("name", s_name), ("where", s_where)]

def sfx(Wt, B, put):
    put(sfx_boom(45, 1.8), 0.0, 0.5)
    put(sfx_ding(1500), Wt("hook", "real"), 0.4)
    put(sfx_pop(), Wt("name", "psychedelic"), 0.5)
    put(sfx_whoosh(4, 1.0), Wt("where"), 0.5)
    put(sfx_ding(1800), Wt("where", "Puerto"), 0.4)
