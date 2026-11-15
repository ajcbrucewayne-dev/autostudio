"""Geo series #1: Why does China have only ONE time zone?  (real NASA globe + Natural Earth borders, GeoGlobeTales-style rhythm)
Facts: China officially uses one zone, Beijing Time (UTC+8); it spans roughly 73°E–135°E (about five 15° solar zones);
before 1949 it used five zones (e.g. Kunlun, Sinkiang-Tibet), merged into one after 1949; in western Xinjiang winter sunrise can be
around 10 a.m. and solar noon in Kashgar around 3 p.m. by Beijing Time; many locals informally use 'Xinjiang time', 2 hours behind.
The contiguous US uses four main zones. China and the contiguous US are of similar east-west width (~5,000 km vs ~4,500 km).
Imagery: NASA Blue Marble (public domain). Borders: Natural Earth (public domain).
"""
import math
from cartoon import *
import globe
from episodes_util import paint_rgba

NAME = "geo_01_china_time"
LOOK = "cinematic"
TITLE = "China should have 5 time zones. It uses ONE 🕗 #shorts"
DESCRIPTION = ("China is about as wide as the USA... but uses just one clock. Here's why, and what it does to the far west. "
               "#geography #maps #china #facts #shorts\n\nEarth imagery: NASA (public domain). Borders: Natural Earth (public domain).")
TAGS = ["china", "time zones", "geography", "maps", "facts", "shorts"]
VOICE, SPEED = "am_michael", 1.08
HOOK = ("AS WIDE AS THE USA", "5 TIME ZONES → 1 ?!")
BEATS = [
    ("hook", "China should have five time zones... but it uses only one.", 0.3),
    ("us", "The US uses four main time zones. China? Just one. Beijing time.", 0.1),
    ("should", "By the sun, China should have five.", 0.1),
    ("why", "And before 1949, it actually did. Then the new government merged them all into one, to unite the country.", 0.0),
    ("weird", "So in the far west, in Xinjiang, the winter sun can rise at ten in the morning, and noon feels like three p.m.", 0.0),
    ("twist", "That's why many locals quietly run their own clock, two hours behind.", 0.1),
    ("end", "One clock for everyone, or the sun on your side? Which would you choose?", 1.0),
]
ZC = [rgb("#ff5a5a"), rgb("#ffb03a"), rgb("#4cc35a"), rgb("#3fa9ff"), rgb("#b07aff")]   # zone colours
CHINA = None
def china():
    global CHINA
    if CHINA is None: CHINA = globe.rings("China")
    return CHINA

def earth(c, t, lon0, lat0, R, cy=980, sun=(-0.35, 0.4, 0.85)):
    bg_cinema(c, t)
    paint_rgba(c, globe.render_globe(lon0, lat0, R, W / 2, cy, sun=sun))

def pin_label(c, s, txt, lon, lat, lon0, lat0, R, cy, p, col=WHITE, size=46, dy=-90):
    x, y, vis = globe.lonlat_to_screen(lon, lat, lon0, lat0, R, W / 2, cy)
    if vis and p > 0: label(c, txt, x, y + dy, size, col, OUT, p)
    return x, y

def clock_icon(c, x, y, r, hour, p=1.0, col=WHITE):
    if p <= 0: return
    k = ease_back(p); c.save(); c.translate(x, y); c.scale(k, k)
    circle(c, 0, 0, r, col, 7)
    for ang, L, w in ((hour / 12 * 2 * math.pi, 0.5, 9), ((hour % 1) * 2 * math.pi, 0.75, 6)):
        c.new_path(); c.move_to(0, 0); c.line_to(math.sin(ang) * r * L, -math.cos(ang) * r * L); c.set_source_rgb(*OUT); c.set_line_width(w); c.stroke()
    c.restore()

# ---------------- scenes
def s_hook(c, s):
    t = s.t; to = s.W("hook", "one")
    lon0, lat0, R = 104, 35, 1350
    earth(c, t, lon0, lat0, R, 1000)
    merge = ease(clamp((t - to + 0.15) / 0.35))          # the 5 solar zones snap into ONE red zone on the word "one"
    globe.region_path(c, china(), lon0, lat0, R, W / 2, 1000); c.save(); c.clip()
    for i in range(5):
        a = 67.5 + 15 * i; globe.meridian_band(c, a, a + 15, 15, 56, lon0, lat0, R, W / 2, 1000)
        c.set_source_rgba(*mix(ZC[i], ZC[0], merge), 0.85); c.fill()
    c.restore()
    globe.region_path(c, china(), lon0, lat0, R, W / 2, 1000); c.set_source_rgba(1, 1, 1, 0.9); c.set_line_width(3); c.stroke()
    if merge < 1:
        for i in range(5):
            x, y, vis = globe.lonlat_to_screen(75 + 15 * i, 31 if i else 39, lon0, lat0, R, W / 2, 1000)
            if vis: text(c, f"+{5 + i}", max(x, 70), y, 56, WHITE, alpha=1 - merge)
    else:
        clock_icon(c, *globe.lonlat_to_screen(104, 34, lon0, lat0, R, W / 2, 1000)[:2], 80, 8.0, clamp((t - to - 0.2) / 0.3))
        pop_text(c, "ONLY ONE", W / 2, 480, 110, s.P(to + 0.1, 0.3), RED)

def s_us(c, s):
    t = s.t; tc = s.W("us", "China"); tb = s.W("us", "Beijing")
    if t < tc - 0.2:   # the USA with four colour bands
        lon0, lat0, R = -98, 39, 1250
        earth(c, t, lon0, lat0, R, 980)
        us = globe.rings("United States of America")
        globe.region_path(c, us, lon0, lat0, R, W / 2, 980)
        c.save(); c.clip()
        for i, (a, b) in enumerate(((-125, -114.5), (-114.5, -101), (-101, -86.5), (-86.5, -66))):
            pr = s.P(s.t0 + 0.25 * i, 0.3)
            globe.meridian_band(c, a, b, 24, 50, lon0, lat0, R, W / 2, 980); c.set_source_rgba(*ZC[3 - i], 0.75 * pr); c.fill()
        c.restore()
        globe.region_path(c, us, lon0, lat0, R, W / 2, 980); c.set_source_rgba(1, 1, 1, 0.9); c.set_line_width(3); c.stroke()
        label(c, "USA: 4 TIME ZONES", W / 2, 420, 60, WHITE, OUT, s.P(s.t0 + 0.3, 0.3))
    else:              # China: one single colour
        lon0, lat0, R = 104, 35, 1350
        earth(c, t, lon0, lat0, R, 1000)
        globe.fill_region(c, china(), lon0, lat0, R, ZC[0], 0.8, W / 2, 1000)
        label(c, "CHINA: 1", W / 2, 420, 70, YEL, OUT, s.P(tc - 0.2, 0.3))
        if t > tb - 0.2:
            x, y = pin_label(c, s, "BEIJING TIME (UTC+8)", 116.4, 39.9, lon0, lat0, R, 1000, s.P(tb - 0.2, 0.3), YEL, 44)
            circle(c, x, y, 14, YEL, 5)

def s_should(c, s):
    t = s.t
    lon0, lat0, R = 104, 35, 1350
    earth(c, t, lon0, lat0, R, 1000)
    globe.region_path(c, china(), lon0, lat0, R, W / 2, 1000); c.save(); c.clip()
    for i in range(5):   # five 15° solar zones appear one by one: UTC+5 ... +9
        pr = s.P(s.t0 + 0.2 + 0.28 * i, 0.3)
        a = 67.5 + 15 * i; globe.meridian_band(c, a, a + 15, 15, 56, lon0, lat0, R, W / 2, 1000); c.set_source_rgba(*ZC[i], 0.8 * pr); c.fill()
    c.restore()
    globe.region_path(c, china(), lon0, lat0, R, W / 2, 1000); c.set_source_rgba(1, 1, 1, 0.9); c.set_line_width(3); c.stroke()
    for i in range(5):
        x, y, vis = globe.lonlat_to_screen(75 + 15 * i, 31 if i else 39, lon0, lat0, R, W / 2, 1000)
        if vis: pop_text(c, f"+{5 + i}", x, y, 56, s.P(s.t0 + 0.3 + 0.28 * i, 0.3), WHITE)
    label(c, "BY THE SUN: 5 ZONES", W / 2, 420, 60, YEL, OUT, s.P(s.t0, 0.3))

def s_why(c, s):
    t = s.t; tm = s.W("why", "merged"); tu = s.W("why", "unite")
    lon0, lat0, R = 104, 35, 1350
    earth(c, t, lon0, lat0, R, 1000)
    merge = ease(clamp((t - tm) / 1.0))
    globe.region_path(c, china(), lon0, lat0, R, W / 2, 1000); c.save(); c.clip()
    for i in range(5):
        a = 67.5 + 15 * i; globe.meridian_band(c, a, a + 15, 15, 56, lon0, lat0, R, W / 2, 1000)
        c.set_source_rgba(*mix(ZC[i], ZC[0], merge), 0.8); c.fill()
    c.restore()
    globe.region_path(c, china(), lon0, lat0, R, W / 2, 1000); c.set_source_rgba(1, 1, 1, 0.9); c.set_line_width(3); c.stroke()
    if t < tm - 0.15: pop_text(c, "BEFORE 1949: 5 ZONES", W / 2, 420, 64, s.P(s.t0 + 0.2, 0.3), WHITE)
    if t > tm - 0.1: pop_text(c, "MERGED INTO ONE", W / 2, 420, 72, s.P(tm - 0.1, 0.3), YEL)
    if t > tu - 0.2: label(c, "\"TO UNITE THE COUNTRY\"", W / 2, 1300, 46, WHITE, OUT, s.P(tu - 0.2, 0.3))

def s_weird(c, s):
    t = s.t; tx = s.W("weird", "Xinjiang"); tten = s.W("weird", "ten"); tth = s.W("weird", "three")
    u = clamp((t - s.t0) / 1.2); lon0 = lerp(104, 82, ease(u)); lat0 = lerp(35, 41, ease(u)); R = lerp(1350, 2300, ease(u))
    earth(c, t, lon0, lat0, R, 1000, sun=(0.9, 0.2, 0.4))
    xj = globe.rings("Xinjiang", "ne_50m_admin_1_states_provinces", ("name", "name_en"))
    globe.fill_region(c, china(), lon0, lat0, R, ZC[0], 0.35, W / 2, 1000)
    if xj: globe.fill_region(c, xj, lon0, lat0, R, ZC[1], 0.7, W / 2, 1000)
    pin_label(c, s, "XINJIANG", 85, 41.5, lon0, lat0, R, 1000, s.P(tx - 0.2, 0.3), YEL, 56, 0)
    if t > tten - 0.3:   # late sunrise card
        p = s.P(tten - 0.3, 0.3)
        c.new_path(); rrect(c, 90, 1200, 420, 300, 30); fs(c, rgb("#14284a"), 6, 0.92 * p)
        sy = lerp(1420, 1330, ease(clamp((t - tten) / 1.2)))
        if p > 0.05: sun(c, 300, sy, 40 * p, t)
        clock_icon(c, 190, 1300, 50, 10.0, p); text(c, "SUNRISE", 300, 1460, 40, WHITE, alpha=p)
    if t > tth - 0.3:
        p = s.P(tth - 0.3, 0.3)
        c.new_path(); rrect(c, 570, 1200, 420, 300, 30); fs(c, rgb("#14284a"), 6, 0.92 * p)
        if p > 0.05: sun(c, 860, 1290, 40 * p, t)
        clock_icon(c, 680, 1300, 50, 3.0, p); text(c, "NOON?!", 780, 1460, 40, YEL, alpha=p)

def s_twist(c, s):
    t = s.t; tt = s.W("twist", "two")
    lon0, lat0, R = 82, 41, 2300
    earth(c, t, lon0, lat0, R, 1000, sun=(0.9, 0.2, 0.4))
    xj = globe.rings("Xinjiang", "ne_50m_admin_1_states_provinces", ("name", "name_en"))
    if xj: globe.fill_region(c, xj, lon0, lat0, R, ZC[1], 0.7, W / 2, 1000)
    p = s.P(s.t0, 0.3)
    clock_icon(c, 330, 560, 110, 8.0, p); text(c, "BEIJING", 330, 720, 48, WHITE, alpha=p)
    clock_icon(c, 750, 560, 110, 6.0, s.P(tt - 0.2, 0.3)); text(c, "LOCAL", 750, 720, 48, YEL, alpha=s.P(tt - 0.2, 0.3))
    if t > tt: pop_text(c, "-2 HOURS", W / 2, 400, 90, s.P(tt, 0.3), YEL)

def s_end(c, s):
    t = s.t; tq = s.W("end", "Which")
    u = clamp((t - s.t0) / 2.0); R = lerp(2300, 700, ease(u)); lon0 = lerp(82, 104, ease(u)); lat0 = lerp(41, 33, ease(u))
    earth(c, t, lon0, lat0, R, 1000)
    globe.fill_region(c, china(), lon0, lat0, R, ZC[0], 0.6, W / 2, 1000)
    pop_text(c, "1 CLOCK", 300, 420, 84, s.P(s.t0 + 0.2, 0.3), WHITE)
    pop_text(c, "OR THE SUN?", 760, 520, 84, s.P(s.t0 + 0.8, 0.3), YEL)
    pop_text(c, "COMMENT BELOW!", W / 2, 1520, 70, s.P(tq, 0.3), WHITE)

SCENES = [("hook", s_hook), ("us", s_us), ("should", s_should), ("why", s_why), ("weird", s_weird), ("twist", s_twist), ("end", s_end)]

def impacts(Wt, B):
    return [Wt("hook", "one"), Wt("us", "China"), Wt("why", "merged")]

def sfx(Wt, B, put):
    put(sfx_boom(45, 1.4), 0.0, 0.4)
    for i in range(4): put(sfx_pop(500 + 120 * i), Wt("us") + 0.25 * i, 0.4)
    for i in range(5): put(sfx_pop(500 + 120 * i), Wt("should") + 0.2 + 0.28 * i, 0.4)
    put(sfx_whoosh(6, 0.8), Wt("why", "merged"), 0.6)
    put(sfx_whoosh(7, 1.2), Wt("weird"), 0.5)
    put(sfx_ding(1320), Wt("weird", "ten"), 0.4); put(sfx_ding(1568), Wt("weird", "three"), 0.4)
    for i in range(6): put(sfx_tick(), Wt("twist", "two") + i * 0.15, 0.4)
    put(sfx_ding(1800), Wt("end", "Which"), 0.5)
