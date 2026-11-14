"""Postcards from Mars #1 — "The rock that appeared out of nowhere" (narrated by the Opportunity rover, 'Oppy').
Facts (NASA/JPL news 2014): Pinnacle Island, ~4 cm, white rim + dark-red centre, absent in a Sol 3528 image and present on Sol 3540
(Jan 2014); explained as a fragment of a rock the rover's wheel broke and flicked downhill; very high sulfur & magnesium and twice
as much manganese as anything seen before on Mars. Opportunity was planned for a 90-sol mission (landed Jan 2004 in Meridiani
Planum; by 2014 at Endeavour crater); last contact June 2018 during a planet-wide dust storm.
Images: NASA/JPL-Caltech/Cornell Univ./Arizona State Univ. (PIA17761, PIA17942, Pinnacle Island Jan 2014), PIA22222 (NASA/JPL-Caltech),
artist's concept (NASA/JPL/Cornell, Maas Digital), Mars map NASA/JPL/USGS (Viking MDIM 2.1) — public domain.
"""
import math, os
from cartoon import *
import globe
from episodes_util import paint_rgba
from PIL import Image

NAME = "mars_01_rock"
LOOK = "cinematic"
TITLE = "A rock appeared on Mars overnight 🪨 #shorts"
DESCRIPTION = ("Postcards from Mars #1 — Opportunity found a rock that wasn't there 12 days earlier. #mars #space #nasa #shorts\n\n"
               "Images: NASA/JPL-Caltech/Cornell Univ./Arizona State Univ.; Mars map: NASA/JPL/USGS. Public domain.")
TAGS = ["mars", "opportunity rover", "space", "nasa", "mystery", "shorts"]
VOICE, SPEED = "af_heart", 1.0
HOOK = ("SOL 3540", "GUESS WHAT I FOUND")
BEATS = [
    ("hook", "Sol thirty-five forty. Guess what I found today.", 2.0),
    ("plant", "A rock. But it wasn't here twelve days ago. Did it fall from the sky? Did something... put it there?", 0.3),
    ("twist", "The truth? It was me. My wheel cracked a rock while I was turning, and flicked this piece downhill.", 0.1),
    ("where", "I'm Opportunity, a NASA rover. I've been exploring Mars since 2004, near a giant crater called Endeavour.", 0.0),
    ("how", "Scientists nicknamed it the jelly doughnut. White outside, dark red inside, with twice as much manganese as anything ever seen on Mars.", 0.2),
    ("shock", "Oh, and I was built to last ninety days. That was ten years ago.", 0.5),
    ("end", "I kept exploring for four more years, until a giant dust storm. Which postcard should I send you next?", 1.2),
]
MARS = os.path.join(ROOT, "assets", "mars")
IMG = {"close": "Pinnacle_Island_(January_2014).jpg", "ba": "PIA17761-MarsOpportunityRover-MysteryRock-Sol3528-Sol3540-color.jpg",
       "src": "PIA17942-MarsOpportunityRover-PinnacleIslandRockMysterySolved-20140204.jpg", "selfie": "PIA22222-Mars-OpportunityRover-FirstSelfie-20180220.jpg",
       "rover": "NASA_Mars_Rover.jpg"}
CREDIT = "Images: NASA/JPL-Caltech/Cornell/ASU"
_S = {}
def surf(key):
    if key not in _S:
        im = Image.open(os.path.join(MARS, IMG[key])).convert("RGB"); a = np.asarray(im)
        bgra = np.dstack([a[..., ::-1], np.full(a.shape[:2], 255, np.uint8)])
        _S[key] = (cairo.ImageSurface.create_for_data(bytearray(np.ascontiguousarray(bgra).tobytes()), cairo.FORMAT_RGB24, im.width, im.height), im.width, im.height)
    return _S[key]

def photo(c, key, x, y, w, h, zoom=1.0, focus=(0.5, 0.5)):
    """image cropped to fill box (x, y, w, h), punch-in around focus"""
    S, iw, ih = surf(key); s = max(w / iw, h / ih) * zoom
    ox = x + w / 2 - focus[0] * iw * s; oy = y + h / 2 - focus[1] * ih * s
    ox = min(x, max(x + w - iw * s, ox)); oy = min(y, max(y + h - ih * s, oy))
    c.save(); c.new_path(); c.rectangle(x, y, w, h); c.clip(); c.translate(ox, oy); c.scale(s, s)
    c.set_source_surface(S); c.get_source().set_filter(cairo.FILTER_GOOD); c.paint(); c.restore()

def postcard(c, key, cx, cy, w, h, rot=0.0, zoom=1.0, focus=(0.5, 0.5), p=1.0, note=None, stamp=True):
    """photo as a tilted postcard with white border, drop shadow and a MARS stamp; p = pop-in progress"""
    if p <= 0: return
    k = ease_back(p); b = 22
    c.save(); c.translate(cx, cy); c.rotate(rot * (2 - k)); c.scale(k, k)
    c.new_path(); c.rectangle(-w / 2 - b + 14, -h / 2 - b + 18, w + 2 * b, h + 2 * b + (70 if note else 0)); c.set_source_rgba(0, 0, 0, 0.45); c.fill()
    c.new_path(); c.rectangle(-w / 2 - b, -h / 2 - b, w + 2 * b, h + 2 * b + (70 if note else 0)); c.set_source_rgb(0.97, 0.95, 0.9); c.fill()
    photo(c, key, -w / 2, -h / 2, w, h, zoom, focus)
    if stamp:
        sx, sy = w / 2 - 70, -h / 2 + 20
        c.new_path(); c.rectangle(sx - 46, sy, 100, 120); c.set_source_rgb(*rgb("#c1440e")); c.fill()
        c.new_path(); c.arc(sx + 4, sy + 48, 28, 0, 2 * math.pi); c.set_source_rgb(*rgb("#f2b07a")); c.fill()
        text(c, "MARS", sx + 4, sy + 98, 22, WHITE, outline=None)
        c.new_path(); c.arc(sx - 30, sy + 110, 52, 0, 2 * math.pi); c.set_source_rgba(0.2, 0.2, 0.3, 0.55); c.set_line_width(4); c.stroke()
    if note:
        c.select_font_face("DejaVu Serif", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD); c.set_font_size(40)
        e = c.text_extents(note); c.move_to(-e.x_advance / 2, h / 2 + b + 42); c.set_source_rgb(0.2, 0.15, 0.3); c.show_text(note)
    c.restore()

def bg_mars(c, t):
    bg_cinema(c, t, seed=11, top="#07050f", bot="#2a0e0a", neb=(("#8f3a1a", 0.45), ("#5a1f3a", 0.35), ("#b0602a", 0.25)))

def credit(c): text(c, CREDIT, W / 2, 1880, 26, WHITE, alpha=0.75)

# ---------------- scenes
def s_hook(c, s):
    t = s.t; tr = 2.2
    if t < tr:   # extreme macro on the rock: unrecognisable
        photo(c, "close", 0, 0, W, H, zoom=4.2 - t * 0.35, focus=(0.43, 0.58))
    else:
        bg_mars(c, t)
        z = lerp(3.2, 1.25, ease_out((t - tr) / 0.6))
        postcard(c, "close", W / 2, 880, 900, 900, -0.05, z, (0.43, 0.58), 1.0, note="Sol 3540 - found this today!")
        pop_text(c, "?", 920, 440, 180, s.P(tr + 0.3, 0.3), YEL)
    credit(c)

def s_plant(c, s):
    t = s.t; tw = s.W("plant", "wasn't"); tf = s.W("plant", "fall"); tp = s.W("plant", "put")
    bg_mars(c, t)
    # NASA's before/after image: left half = Sol 3528 (empty), right half = Sol 3540 (rock)
    after = clamp((t - tw - 1.2) / 0.5)
    postcard(c, "ba", 330, 640, 560, 640, -0.06, 1.0, (0.24, 0.5), s.P(tw - 0.4, 0.35), note="12 days ago")
    postcard(c, "ba", 760, 900, 560, 640, 0.05, 1.0, (0.76, 0.5), after, note="today")
    if after >= 1: ring(c, 905, 958, 70 + 8 * math.sin(t * 6), YEL, 8, 0.9)
    pop_text(c, "FELL FROM THE SKY?", W / 2, 260, 78, s.P(tf - 0.1, 0.3), WHITE)
    pop_text(c, "ALIENS?!", W / 2, 1530, 110, s.P(tp, 0.3), YEL)
    credit(c)

def s_twist(c, s):
    t = s.t; tm = s.W("twist", "me"); tw = s.W("twist", "wheel"); tf = s.W("twist", "flicked")
    bg_mars(c, t)
    postcard(c, "src", W / 2, 900, 940, 940, 0.03, 1.0 + 0.04 * (t - s.t0), (0.5, 0.5), s.P(s.t0, 0.35))
    pop_text(c, "IT WAS ME!", W / 2, 260, 120, s.P(tm - 0.1, 0.3), YEL)
    if t > tw - 0.2: label(c, "MY WHEEL TRACK", W / 2, 1500, 52, WHITE, OUT, s.P(tw - 0.2, 0.3))
    if t > tf - 0.2:
        u = ease(clamp((t - tf + 0.2) / 0.9)); x0, y0, x1, y1 = 380, 760, 700, 1060
        arrow(c, (x0, y0), (lerp(x0, x1, u) + 1, lerp(y0, y1, u) + 1), 1, YEL, 12, 30)
    credit(c)

def s_where(c, s):
    t = s.t; te = s.W("where", "Endeavour"); u = clamp((t - s.t0) / 2.6)
    bg_mars(c, t)
    R = lerp(420, 2400, ease(clamp((u - 0.45) / 0.55))); lon0 = lerp(-60, -5.3, ease(u)); lat0 = lerp(15, -2.3, ease(u))
    paint_rgba(c, globe.render_globe(lon0, lat0, R, W / 2, 1000, sun=(-0.4, 0.4, 0.85), planet="mars"))
    x, y, vis = globe.lonlat_to_screen(-5.3, -2.3, lon0, lat0, R, W / 2, 1000)
    if vis:
        glow(c, x, y, 160, (1, 0.8, 0.4), 0.6); circle(c, x, y, 16, YEL, 6)
        if t > te - 0.3: label(c, "ENDEAVOUR CRATER", x, y + 120, 52, WHITE, OUT, s.P(te - 0.3, 0.35))
    postcard(c, "rover", 720, 420, 560, 400, 0.06, 1.0, (0.5, 0.45), s.P(s.W("where", "Opportunity") - 0.2, 0.35), note="that's me, Oppy!", stamp=False)
    text(c, "Mars map: NASA/JPL/USGS · Art: NASA/JPL/Cornell", W / 2, 1880, 26, WHITE, alpha=0.75)

def s_how(c, s):
    t = s.t; tj = s.W("how", "jelly"); twh = s.W("how", "White"); tr = s.W("how", "red"); tm = s.W("how", "manganese")
    bg_mars(c, t)
    postcard(c, "close", W / 2, 860, 900, 900, -0.03, 2.4, (0.43, 0.58), s.P(s.t0, 0.35))
    pop_text(c, "\"JELLY DOUGHNUT\"", W / 2, 250, 96, s.P(tj - 0.1, 0.3), YEL)
    if t > twh - 0.2: label(c, "WHITE RIM", 280, 640, 46, WHITE, OUT, s.P(twh - 0.2, 0.3)); arrow(c, (330, 680), (470, 820), s.P(twh, 0.3), WHITE, 9, 22)
    if t > tr - 0.2: label(c, "DARK-RED CENTER", 760, 1180, 46, RED, WHITE, s.P(tr - 0.2, 0.3)); arrow(c, (700, 1140), (580, 960), s.P(tr, 0.3), RED, 9, 22)
    if t > tm - 0.2:
        c.new_path(); rrect(c, 200, 1420, 680, 170, 30); fs(c, rgb("#1d1230"), 6, 0.92 * s.P(tm - 0.2, 0.3))
        text(c, "MANGANESE x2", W / 2, 1480, 72, YEL, alpha=s.P(tm - 0.2, 0.3))
        text(c, "more than anything seen on Mars before", W / 2, 1550, 30, WHITE, alpha=s.P(tm, 0.3))
    credit(c)

def s_shock(c, s):
    t = s.t; tn = s.W("shock", "ninety"); tt = s.W("shock", "ten")
    bg_mars(c, t)
    postcard(c, "selfie", W / 2, 680, 860, 600, 0.04, 1.0, (0.5, 0.45), s.P(s.t0, 0.35), note="my selfie (yes, I'm a bit dusty)")
    if t > tn - 0.2:
        c.new_path(); rrect(c, 140, 1080, 800, 250, 30); fs(c, rgb("#1d1230"), 6, 0.92 * s.P(tn - 0.2, 0.3))
        text(c, "BUILT FOR: 90 DAYS", W / 2, 1150, 56, WHITE, alpha=s.P(tn - 0.2, 0.3))
        if t > tt - 0.2:
            yrs = 10 * ease(clamp((t - tt + 0.2) / 0.8))
            text(c, f"STILL GOING: {yrs:.0f} YEARS", W / 2, 1250, 62, YEL, alpha=s.P(tt - 0.2, 0.3))
    credit(c)

def s_end(c, s):
    t = s.t; td = s.W("end", "dust"); tq = s.W("end", "Which")
    bg_mars(c, t)
    dust = clamp((t - td + 0.3) / 1.5)
    postcard(c, "rover", W / 2, 700, 900, 620, -0.03, 1.0 + 0.05 * (t - s.t0), (0.5, 0.5), s.P(s.t0, 0.35), note="- Oppy (2004-2018)", stamp=True)
    if dust > 0:   # dust storm rolls over the postcard
        for k in range(40):
            x = (k * 97 + t * 260 * (1 + k % 3)) % (W + 300) - 150; y = 300 + (k * 53) % 1100
            circle(c, x, y, 40 + (k % 5) * 18, (0.75, 0.45, 0.28), 0, 0.18 * dust)
        c.save(); c.identity_matrix(); c.set_source_rgba(0.55, 0.3, 0.18, 0.35 * dust); c.paint(); c.restore()
    pop_text(c, "WHICH POSTCARD NEXT?", W / 2, 1450, 72, s.P(tq, 0.3), YEL)
    text(c, "comment a place on Mars", W / 2, 1540, 40, WHITE, alpha=s.P(tq + 0.3, 0.3))
    credit(c)

SCENES = [("hook", s_hook), ("plant", s_plant), ("twist", s_twist), ("where", s_where), ("how", s_how), ("shock", s_shock), ("end", s_end)]

def cams(Wt, B):
    return {"twist": [(Wt("twist"), 540, 960, 1.0), (B["twist"]["t1"], 540, 940, 1.06)],
            "end": [(Wt("end"), 540, 960, 1.0), (B["end"]["t1"], 540, 900, 1.08)]}

def impacts(Wt, B):
    return [2.2, Wt("twist", "me")]

def sfx(Wt, B, put):
    put(sfx_boom(40, 2.0), 0.0, 0.4)
    put(sfx_whoosh(3, 0.6), 2.0, 1.0)
    put(sfx_pop(), Wt("plant", "wasn't") - 0.3, 0.4); put(sfx_pop(700), Wt("plant", "wasn't") + 1.2, 0.5)
    put(sfx_ding(1500), Wt("plant", "put"), 0.4)
    put(sfx_pop(1000), Wt("twist", "flicked"), 0.5)
    put(sfx_whoosh(6, 1.6), Wt("where"), 0.5); put(sfx_ding(1800), Wt("where", "Endeavour"), 0.4)
    put(sfx_ding(1320), Wt("how", "manganese"), 0.4)
    put(sfx_boom(55, 0.8), Wt("shock", "ten"), 0.6)
    put(sfx_whoosh(12, 2.5), Wt("end", "dust"), 0.6)
    put(sfx_ding(1568), Wt("end", "Which"), 0.5)
