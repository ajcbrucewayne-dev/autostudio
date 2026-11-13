"""What If #0 (template): What if the Moon vanished?  — cartoon style A.
Facts: solar tide ~46% of lunar -> sun-only tides ~1/3 of today's combined range; coral mass spawning is cued by the lunar cycle;
without the Moon, Earth's obliquity could vary chaotically over millions of years (Laskar 1993); Moon recedes ~3.8 cm/yr.
"""
import math
from cartoon import *

NAME = "whatif_moon"
TITLE = "What if the Moon vanished? 🌙 #shorts"
DESCRIPTION = "One night the Moon disappears. Here's what would happen to our tides, sea life and seasons. #whatif #space #science #shorts"
TAGS = ["what if", "moon", "space", "science", "tides", "shorts"]
VOICE, SPEED = "am_michael", 1.05
HOOK = ("WHAT IF THE MOON", "VANISHED?")
BEATS = [
    ("hook", "What if, one night... the Moon just vanished?", 0.5),
    ("pull", "Right now, the Moon's gravity tugs on our oceans, pulling them into a giant bulge.", 0.0),
    ("tides", "Without it, that bulge would flatten, and tides would shrink to about a third.", 0.0),
    ("life", "Tide pools would stop refilling, leaving crabs stranded. And corals that spawn by moonlight would lose their calendar.", 0.0),
    ("tilt", "And over millions of years, Earth's tilt could wobble wildly, scrambling the seasons.", 0.0),
    ("end", "Good news? The Moon is only drifting away about four centimeters a year. Would you miss it?", 0.8),
]

MX, MY, MR = 760, 560, 120

def s_hook(c, s):
    t = s.t; tv = s.W("hook", "vanished")
    bg_space(c, t)
    earth(c, 500, 1000, 270, spin=t * 0.05)
    if t < tv:
        sh = (t - tv + 1.2) * 6 if t > tv - 1.2 else 0
        moon(c, MX + math.sin(sh * 7) * min(sh, 6), MY, MR, face="shock" if t > tv - 1.5 else "happy", t=t, crack=clamp(t / tv))
    else:
        lt = t - tv
        ring(c, MX, MY, MR + lt * 900, WHITE, 14, 1 - clamp(lt / 0.6))
        for i in range(14):  # chunks flying away
            a = i * 0.45 + 0.2; d = MR * 0.4 + ease_out(lt / 1.4) * (260 + 60 * (i % 4))
            if lt < 2.0: c.new_path(); path(c, blob(MX + math.cos(a) * d, MY + math.sin(a) * d, 26 - 8 * (i % 3), 40 + i, 0.4)); fs(c, GREY, 5, 1 - clamp((lt - 1.2) / 0.8))
        dashed_circle(c, MX, MY, MR, t=t, alpha=clamp((lt - 0.4) / 0.4) * 0.85)
        pop_text(c, "?", MX, MY, 170, clamp((lt - 0.6) / 0.4), YEL)
    leo(c, 250, 2080, 0.78, "idle" if t < tv else "shock", "curious" if t < tv else "shock", t, look=(0.8, -0.9))

def s_pull(c, s):
    t = s.t; t0 = s.t0; tb = s.W("pull", "bulge")
    bg_space(c, t)
    k = ease(s.P(s.W("pull", "tugs"), 1.2)) * (0.75 + 0.25 * math.sin(t * 3))
    earth(c, 470, 960, 260, spin=t * 0.05, bulge=k, bulge_ang=-0.55)
    moon(c, 900, 520, 85, face="happy", t=t)
    for i in range(3):  # gravity pull arrows
        u = (t * 0.7 + i / 3) % 1
        arrow(c, (840 - u * 140, 600 + u * 120), (800 - u * 140 - 70, 620 + u * 120 + 40), 1, CYAN, 12, 26)
    label(c, "GRAVITY", 860, 700, 40, CYAN, OUT, s.P(s.W("pull", "gravity"), 0.35))
    label(c, "OCEAN BULGE", 300, 600, 46, rgb("#5aa9ff"), WHITE, s.P(tb - 0.1, 0.35))
    arrow(c, (330, 650), (560, 720), s.P(tb + 0.2, 0.4), WHITE, 12, 28)
    leo(c, 860, 2060, 0.72, "point_left", "curious", t, look=(-0.8, -0.6))

def s_tides(c, s):
    t = s.t; tf = s.W("tides", "flatten"); tt = s.W("tides", "third")
    bg_sky(c, t)
    sun(c, 920, 300, 62, t, face="happy")

    for i in range(14):  # pebbles
        c.new_path(); c.arc(80 + i * 75, 1720 - i * 48 + (i % 3) * 30, 9, 0, 2 * math.pi); c.set_source_rgba(0.75, 0.6, 0.35, 0.8); c.fill()
    lvl = lerp(1060, 1290, ease((t - tf) / 1.6))
    wave_band(c, lvl, t, bottom=H + 50)
    c.new_path(); path(c, [(380, H + 50), (520, 1500), (760, 1180), (1130, 900), (1130, H + 50)]); fs(c, SAND, 10)   # beach in front of the sea
    # tide gauge
    c.new_path(); c.rectangle(170, 880, 26, 560); fs(c, rgb("#8b5a2b"), 7)
    for i, (yy, lab) in enumerate(((1060, "HIGH"), (1290, "LOW"))):
        c.new_path(); c.move_to(196, yy); c.line_to(250, yy); c.set_source_rgb(*OUT); c.set_line_width(8); c.stroke(); text(c, lab, 330, yy, 40)
    text(c, "TIDES", W / 2, 420, 90, WHITE)
    if t > tt - 0.3:
        pct = lerp(100, 33, ease((t - tt + 0.3) / 0.8)); pop_text(c, f"{pct:.0f}%", W / 2, 580, 150, s.P(tt - 0.3, 0.3), YEL)
    else: pop_text(c, "100%", W / 2, 580, 150, s.P(s.t0, 0.3), WHITE)

def s_life(c, s):
    t = s.t; tc = s.W("life", "corals")
    if t < tc - 0.25:
        bg_sky(c, t)
        c.new_path(); path(c, [(-50, 1000), (1130, 920), (1130, H + 50), (-50, H + 50)]); fs(c, SAND, 10)
        drain = ease(s.P(s.t0 + 0.3, 2.2))
        c.new_path(); c.save(); c.translate(540, 1150); c.scale(1, 0.38); c.arc(0, 0, 330, 0, 2 * math.pi); c.restore(); fs(c, rgb("#d9b46a"), 9)
        if drain < 1:
            c.new_path(); c.save(); c.translate(540, 1150 + 40 * drain); c.scale(1, 0.38 * (1 - drain * 0.9)); c.arc(0, 0, 300 * (1 - 0.5 * drain), 0, 2 * math.pi); c.restore()
            fs(c, rgb("#5aa9ff"), 7)
        ts = s.W("life", "stranded")
        crab(c, 540, 1170, 1.25, t, "sad" if t > ts - 0.3 else "happy", walk=0 if t > ts else 1)
        label(c, "TIDE POOL", 540, 800, 46, WHITE, OUT, s.P(s.t0 + 0.2, 0.35))
        if t > ts:
            for i in range(3):
                u = ((t - ts) * 0.9 + i / 3) % 1; c.new_path(); c.arc(700 + i * 30, 1030 - u * 120, 10, 0, 2 * math.pi); c.set_source_rgba(*SKY, 1 - u); c.fill()
    else:
        c.save(); c.identity_matrix(); g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, *rgb("#1e6fd1")); g.add_color_stop_rgb(1, *rgb("#0b2a66"))
        c.set_source(g); c.paint(); c.restore()
        for i in range(6):  # light rays
            c.new_path(); c.move_to(100 + i * 180, 0); c.line_to(160 + i * 180, 0); c.line_to(60 + i * 180 + 200, H); c.line_to(i * 180 + 200, H); c.close_path()
            c.set_source_rgba(1, 1, 1, 0.05); c.fill()
        c.new_path(); path(c, [(-50, 1250), (400, 1200), (800, 1240), (1130, 1190), (1130, H + 50), (-50, H + 50)]); fs(c, rgb("#e8c98a"), 9)
        tcal = s.W("life", "calendar")
        lost = clamp((t - tcal) / 0.6)
        for i, (x, sc_, col) in enumerate(((260, 0.9, PINK), (540, 1.2, ORANGE), (830, 0.95, PURPLE))):
            coral(c, x, 1250, sc_ * 1.35, t, mix(col, GREY, lost * 0.6), glow=1 - lost)
        moon(c, 540, 420, 90, alpha=1 - lost * 0.8, face="happy" if lost < 0.5 else "sad", t=t)
        c.new_path(); rrect(c, 690, 330, 200, 190, 20); fs(c, WHITE, 7)
        c.new_path(); c.rectangle(690, 330, 200, 50); c.set_source_rgb(*RED); c.fill()
        text(c, "?" if lost > 0.5 else "FULL", 790, 450, 70 if lost > 0.5 else 46, OUT, outline=None)
        if lost > 0:
            c.new_path(); c.move_to(700, 340); c.line_to(880, 510); c.set_source_rgb(*RED); c.set_line_width(12); c.stroke()

def s_tilt(c, s):
    t = s.t; tw = s.W("tilt", "wobble")
    bg_space(c, t)
    sun(c, 130, 400, 70, t)
    wob = clamp((t - tw) / 1.0)
    ang = 23.5 + wob * 38 * math.sin((t - tw) * 2.6) * min(1, (t - tw) * 0.8 + 0.3)
    earth(c, 560, 960, 250, spin=t * 0.15, tilt=math.radians(ang), axis=True)
    c.save(); c.translate(560, 1000); c.rotate(math.radians(ang)); c.restore()
    text(c, f"TILT {ang:.0f}°", W / 2, 470, 96, YEL)
    tsn = s.W("tilt", "seasons")
    if t > tsn - 0.2:
        for i in range(4):
            a = t * 2.4 + i * math.pi / 2; x, y = 560 + math.cos(a) * 380, 960 + math.sin(a) * 330
            if i % 2: snowflake(c, x, y, 50 * ease_back(s.P(tsn - 0.2, 0.3)))
            else: sun(c, x, y, 34 * ease_back(s.P(tsn - 0.2, 0.3)), t, 6)
        label(c, "SEASONS: SCRAMBLED", W / 2, 1290, 52, RED, WHITE, s.P(tsn, 0.35))
    leo(c, 860, 2080, 0.72, "cover" if t > tw + 0.5 else "idle", "scared" if t > tw else "worried", t, look=(-0.6, -0.8))

def s_end(c, s):
    t = s.t; td = s.W("end", "drifting"); tm = s.W("end", "Would")
    bg_space(c, t)
    earth(c, 300, 980, 200, spin=t * 0.05)
    mx = 700 + ease(s.P(td, 3.0)) * 140
    moon(c, mx, 820, 80, face="happy", t=t)
    arrow(c, (mx + 100, 820), (mx + 230, 820), s.P(td + 0.2, 0.5), YEL, 12, 28)
    label(c, "3.8 cm / YEAR", 760, 980, 48, YEL, OUT, s.P(s.W("end", "four"), 0.35))
    pop_text(c, "WOULD YOU MISS IT?", W / 2, 470, 82, s.P(tm, 0.35), YEL)
    leo(c, 540, 2080, 0.8, "cheer" if t < tm else "think", "wow" if t < tm else "curious", t)

SCENES = [("hook", s_hook), ("pull", s_pull), ("tides", s_tides), ("life", s_life), ("tilt", s_tilt), ("end", s_end)]

def cams(Wt, B):
    tv = Wt("hook", "vanished")
    return {"hook": [(0, 600, 900, 1.12), (tv - 0.2, 640, 820, 1.22), (tv + 0.5, 540, 960, 1.0)],
            "tilt": [(Wt("tilt"), 560, 1000, 1.25), (Wt("tilt", "wobble"), 560, 960, 1.0)]}

def sfx(Wt, B, put):
    tv = Wt("hook", "vanished")
    put(sfx_shatter(), tv, 1.0)
    put(sfx_ding(), Wt("pull", "bulge"), 0.6)
    put(sfx_pop(), Wt("tides", "third"), 0.7)
    put(sfx_pop(500), Wt("life", "stranded"), 0.6)
    put(sfx_boom(55, 1.0), Wt("tilt", "wobble"), 0.5)
    put(sfx_pop(700), Wt("tilt", "seasons"), 0.6)
    put(sfx_ding(1568), Wt("end", "Would"), 0.6)
