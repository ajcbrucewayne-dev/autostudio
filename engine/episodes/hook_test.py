"""Three hook variants (~4-5 s each) on the same NOAA footage. Choose with env HOOK_VARIANT = A | B | C.
A "Guess what this is": extreme macro (unrecognisable) -> whoosh pull-back reveal.
B "Lights on": pitch black, a robot's lights click on -> the creature appears out of the dark.
C "Alien": glitchy fast zoom, bold claim -> reveal it's on Earth.
Footage: NOAA Ocean Exploration, "Psychedelic Medusa" (Océano Profundo 2018), public domain.
"""
import math, os
from cartoon import *
from footage import Clip

V = os.environ.get("HOOK_VARIANT", "A")
NAME = "hook_test_" + V
LOOK = "cinematic"
VOICE, SPEED = "am_michael", 1.0
LINES = {"A": "Guess what this is.", "B": "A robot switched on its lights in the deep sea... and found this.",
         "C": "This looks like an alien. But it lives on our planet."}
BEATS = [("hook", LINES[V], 2.4 if V == "A" else 0.8)]
CLIP = Clip(os.path.join(ROOT, "assets", "footage", "Okeanos_Explorer_PR_and_USVI_Dive_8-_Psychedelic_Medusa-NOAA-1280x720.webm"))
FULL = (0, 0, W, H)

def s_hook(c, s):
    t = s.t
    if V == "A":
        tr = 2.2                                                   # reveal moment
        if t < tr:   # extreme macro on the glowing core: you can't tell what it is
            CLIP.draw(c, 49.0 + t * 0.3, *FULL, zoom=4.2 - t * 0.15, focus=(0.47, 0.42), radius=1, border=False)
            pop_text(c, "GUESS WHAT", W / 2, 360, 120, s.P(0.0, 0.25), WHITE)
            pop_text(c, "THIS IS", W / 2, 500, 140, s.P(0.15, 0.25), YEL)
        else:        # whoosh pull-back to the whole jellyfish
            z = lerp(3.6, 1.05, ease_out((t - tr) / 0.6))
            CLIP.draw_fill(c, 49.0 + t * 0.3)
            CLIP.draw(c, 49.0 + t * 0.3, 40, 420, 1000, 850, zoom=z, focus=(0.47, 0.42), radius=40)
            pop_text(c, "A JELLYFISH!", W / 2, 300, 110, s.P(tr + 0.4, 0.3), YEL)
    elif V == "B":
        lt = t - 1.0                                               # lights click on at t = 1.0
        bg_color(c, (0, 0, 0))
        if lt > 0:
            fl = 1 if lt > 0.25 else (1 if (int(lt * 24) % 2) else 0.15)   # flicker on
            CLIP.draw(c, 45.0 + t * 0.6, *FULL, zoom=1.7, focus=(0.47, 0.42), radius=1, border=False, alpha=fl * clamp(lt / 0.4))
            c.save(); c.identity_matrix()
            g = cairo.RadialGradient(W / 2, H * 0.45, 200, W / 2, H * 0.45, 1100); g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, 0.85)
            c.set_source(g); c.paint(); c.restore()       # spotlight falloff, like an ROV lamp
        else:
            for k in range(30):  # floating specks in the dark
                circle(c, (k * 211) % W, ((k * 373) + t * 30) % H, 2.5, WHITE, 0, 0.35)
        text(c, "DEEP SEA · ROBOT CAMERA", W / 2, 200, 44, WHITE, alpha=0.85)
        if lt > 1.6: pop_text(c, "...AND FOUND THIS", W / 2, 1150, 92, s.P(1.0 + 1.6, 0.3), YEL)
    else:  # C
        z = 1.0 + 1.6 * (1 - ease_out(t / 1.2))
        gl = t < 0.6 and int(t * 30) % 3 == 0
        CLIP.draw(c, 44.0 + t, *FULL, zoom=z + 0.6, focus=(0.5, 0.45), radius=1, border=False)
        if gl:   # RGB-split glitch frames
            c.save(); c.identity_matrix(); c.set_source_rgba(1, 0, 0.4, 0.25); c.rectangle(0, (t * 9000) % H, W, 120); c.fill(); c.restore()
        pop_text(c, "ALIEN?", W / 2, 360, 170, s.P(0.0, 0.25), WHITE)
        if t > s.W("hook", "But") - 0.1:
            pop_text(c, "IT LIVES ON EARTH", W / 2, 1150, 88, s.P(s.W("hook", "But") - 0.1, 0.3), YEL)

SCENES = [("hook", s_hook)]

def impacts(Wt, B):
    return {"A": [2.2], "B": [1.0], "C": [0.0]}[V]

def sfx(Wt, B, put):
    if V == "A": put(sfx_whoosh(3, 0.6), 2.0, 1.0); put(sfx_ding(1800), 2.6, 0.5)
    if V == "B":
        for k in range(3): put(sfx_tick(), 1.0 + k * 0.08, 1.0)      # clunk-clunk of the lamps
        put(sfx_boom(40, 2.0), 1.0, 0.6)
    if V == "C": put(sfx_shatter(), 0.0, 0.4)
