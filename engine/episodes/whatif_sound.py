"""What If #1: What if sound moved at walking speed?  (approved script, cartoon style A + cinematic look)
Facts: speed of sound in air ~343 m/s at 20 °C; walking pace ~1.4 m/s -> 2.8 m room = 2 s, 100 m field = 71 s,
2 km storm = 1430 s = ~24 min; a breeze (> 1.4 m/s) out-runs the sound, so people upwind can't hear you;
a 3 m/s jogger would be 'supersonic'; sound in Bose-Einstein condensates measured at mm/s speeds (Andrews et al., 1997).
"""
import math
from cartoon import *

NAME = "whatif_sound"
LOOK = "cinematic"
TITLE = "What if sound moved at walking speed? 🔊 #shorts"
DESCRIPTION = ("If sound only travelled 1.4 m per second, thunder would arrive 24 minutes late, wind would mute you, and every jogger "
               "would break the sound barrier. #whatif #science #physics #sound #shorts")
TAGS = ["what if", "sound", "physics", "science", "sonic boom", "shorts"]
VOICE, SPEED = "am_michael", 1.05
HOOK = ("WHAT IF SOUND", "WAS THIS SLOW?")
BEATS = [
    ("cold", "What if sound... moved at walking speed?", 0.6),
    ("why", "Sound is just air molecules bumping into each other, like falling dominoes. Normally, that chain races at 343 meters a second. Now slow it down... to a walking pace.", 0.0),
    ("talk", "Talk to a friend across the room, and your words arrive two seconds late. Shout across a football field... they'd hear you over a minute later.", 0.0),
    ("storm", "A storm two kilometers away? You'd see the lightning... and hear the thunder twenty-four minutes later.", 1.0),
    ("wind", "Even a gentle breeze would outrun sound. Anyone upwind of you... couldn't hear you at all.", 0.0),
    ("boom", "And anyone who jogs would break the sound barrier. Runners, bikes, cars... sonic booms all day long.", 0.0),
    ("end", "The wildest part? Scientists have really made sound this slow, in clouds of atoms colder than outer space. Could you survive a day in this world?", 0.9),
]
FRIEND = (rgb("#e8b48a"), rgb("#ff7aa8"), rgb("#d9622b"))      # skin, hoodie, hair

# ---------------- props drawn in this episode
def bubble(c, x, y, txt, size=70, p=1.0, col=WHITE, tail=-1):
    if p <= 0: return
    k = ease_back(p); c.save(); c.translate(x, y); c.scale(k, k)
    c.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(size)
    w = c.text_extents(txt).x_advance + size * 0.9; h = size * 1.5
    c.new_path(); rrect(c, -w / 2, -h / 2, w, h, h * 0.45)
    c.move_to(tail * w * 0.2, h / 2 - 2); c.line_to(tail * w * 0.35, h / 2 + 34); c.line_to(tail * w * 0.02, h / 2 - 2); fs(c, col, 7)
    text(c, txt, 0, 0, size, OUT, outline=None); c.restore()

def domino(c, x, y, ang, col=WHITE):
    """domino standing on (x, y), tipped by ang radians to the right around its bottom-right corner"""
    c.save(); c.translate(x + 22, y); c.rotate(ang); c.new_path(); rrect(c, -44, -150, 44, 150, 8); fs(c, col, 7)
    for dy in (-115, -40): c.new_path(); c.arc(-22, dy, 7, 0, 2 * math.pi); c.set_source_rgb(*OUT); c.fill()
    c.restore()

def bolt(c, x, y, s=1.0, alpha=1.0):
    pts = [(0, 0), (-60, 260), (10, 250), (-50, 520), (110, 200), (30, 210), (80, 0)]
    c.save(); c.translate(x, y); c.scale(s, s); c.new_path(); path(c, pts); fs(c, YEL, 8, alpha); c.restore()

def storm_cloud(c, x, y, r, dark=0.0):
    cloud(c, x, y + 8, r * 1.03, OUT); cloud(c, x, y, r, mix(rgb("#8a93b8"), rgb("#3d4466"), dark))

def town(c, y, t, lit=1.0):
    for i, (x, w, h) in enumerate([(40, 120, 180), (170, 90, 260), (270, 140, 150), (420, 100, 230), (530, 160, 170), (700, 110, 280), (820, 150, 190), (980, 120, 240)]):
        c.new_path(); c.rectangle(x, y - h, w, h); fs(c, rgb("#2a2550"), 6)
        for k in range(int(h / 60)):
            for j in range(int(w / 50)):
                on = ((i * 7 + k * 3 + j) % 4) != 0
                c.new_path(); c.rectangle(x + 15 + j * 45, y - h + 20 + k * 55, 22, 28); c.set_source_rgba(1, 0.85, 0.4, (0.9 if on else 0.15) * lit); c.fill()

def clock(c, x, y, r, minutes, p=1.0):
    if p <= 0: return
    k = ease_back(p); c.save(); c.translate(x, y); c.scale(k, k)
    c.new_path(); c.arc(0, 0, r, 0, 2 * math.pi); fs(c, WHITE, 9)
    for i in range(12):
        a = i * math.pi / 6; c.new_path(); c.move_to(math.cos(a) * r * 0.8, math.sin(a) * r * 0.8); c.line_to(math.cos(a) * r * 0.92, math.sin(a) * r * 0.92)
        c.set_source_rgb(*OUT); c.set_line_width(6); c.stroke()
    for ang, L, w in ((minutes / 60 * 2 * math.pi, 0.75, 9), (minutes / 720 * 2 * math.pi, 0.5, 13)):
        c.new_path(); c.move_to(0, 0); c.line_to(math.sin(ang) * r * L, -math.cos(ang) * r * L); c.set_source_rgb(*RED if w == 9 else OUT); c.set_line_width(w); c.stroke()
    c.restore()

def jogger(c, x, y, s, t, col=rgb("#3dd6d0")):
    c.save(); c.translate(x, y); c.scale(s, s); c.set_line_cap(cairo.LINE_CAP_ROUND)
    ph = t * 14
    for sgn in (-1, 1):
        a1 = sgn * 0.7 * math.sin(ph); a2 = a1 + 0.6
        for lw, cc in ((30, OUT), (18, rgb("#3b5bdb"))):
            c.new_path(); c.move_to(0, -90); c.line_to(math.sin(a1) * 60, -90 + math.cos(a1) * 60); c.line_to(math.sin(a1) * 60 - math.sin(a2) * 55, -30 + math.cos(a2) * 30)
            c.set_source_rgb(*cc); c.set_line_width(lw); c.stroke()
    c.new_path(); rrect(c, -32, -200, 64, 120, 28); fs(c, col, 7)
    for sgn in (-1, 1):
        a = -sgn * 0.9 * math.sin(ph)
        for lw, cc in ((26, OUT), (14, col)):
            c.new_path(); c.move_to(0, -180); c.line_to(math.sin(a) * 55, -180 + math.cos(a) * 45); c.set_source_rgb(*cc); c.set_line_width(lw); c.stroke()
    circle(c, 6, -240, 38, rgb("#c98a5a"), 7)
    c.restore()

def bike(c, x, y, s, t):
    c.save(); c.translate(x, y); c.scale(s, s)
    for wx in (-70, 70):
        c.new_path(); c.arc(wx, -45, 45, 0, 2 * math.pi); c.set_source_rgb(*OUT); c.set_line_width(10); c.stroke()
        a = t * 12; c.new_path(); c.move_to(wx + math.cos(a) * 40, -45 + math.sin(a) * 40); c.line_to(wx - math.cos(a) * 40, -45 - math.sin(a) * 40); c.set_line_width(4); c.stroke()
    c.new_path(); c.move_to(-70, -45); c.line_to(-10, -110); c.line_to(55, -110); c.line_to(70, -45); c.move_to(-10, -110); c.line_to(0, -45)
    c.set_source_rgb(*RED); c.set_line_width(10); c.stroke()
    c.new_path(); rrect(c, -40, -230, 60, 110, 26); fs(c, ORANGE, 7); circle(c, 0, -265, 36, rgb("#e8b48a"), 7)
    c.restore()

def car(c, x, y, s, t):
    c.save(); c.translate(x, y); c.scale(s, s)
    c.new_path(); path(c, [(-170, -40), (-170, -100), (-90, -110), (-50, -170), (60, -170), (110, -110), (175, -95), (175, -40)]); fs(c, rgb("#7c5cff"), 8)
    c.new_path(); path(c, [(-35, -160), (50, -160), (90, -112), (-70, -112)]); fs(c, SKY, 6)
    for wx in (-100, 105): circle(c, wx, -38, 38, rgb("#333344"), 8); circle(c, wx, -38, 14, GREY, 5)
    c.restore()

def mach_cone(c, x, y, h, col=WHITE, alpha=0.8):
    """Mach cone trailing behind a supersonic object moving right"""
    for k in range(3):
        L = h * (1 + k * 0.6); a = alpha * (1 - k * 0.3)
        c.new_path(); c.move_to(x - L * 1.4, y - L); c.line_to(x + 10, y - h * 0.5); c.line_to(x - L * 1.4, y + 20)
        c.set_source_rgba(*col, a); c.set_line_width(8); c.stroke()

# ---------------- scenes
def s_cold(c, s):
    t = s.t
    bg_cinema(c, t)
    town(c, 1250, t)
    fl = 1 - clamp(t / 0.6)                                   # frame 1: the lightning has just struck
    if t < 0.9 or (1.4 < t < 1.6): bolt(c, 640, 660, 1.0)
    glow(c, 680, 660, 700, (0.85, 0.9, 1), 0.7 * fl)
    storm_cloud(c, 640, 640, 150, 0.7); storm_cloud(c, 380, 700, 110, 0.6)
    # the thunder "BOOM" is still crawling out of the cloud at walking pace
    bx = 700 + s.lt * 40
    bubble(c, bx, 760, "B O O M . . .", 54, s.P(0.1, 0.4), WHITE)
    text(c, "1.4 m/s", bx, 850, 40, YEL)
    leo(c, 300, 2070, 0.78, "cover", "worried", t, look=(0.8, -0.9))

def s_why(c, s):
    t = s.t; ts = s.W("why", "slow"); t343 = s.W("why", "343"); tw = s.W("why", "walking")
    bg_cinema(c, t, seed=6)
    text(c, "AIR = DOMINOES", W / 2, 360, 70, WHITE)
    # chain of dominoes: fast wave before "slow", then it crawls
    fast_end = ts - 0.2
    def pos(tt):
        if tt < s.t0 + 0.5: return -1.0
        if tt < fast_end: return ((tt - s.t0 - 0.5) * 9.0) % 14
        return (tt - fast_end) * 0.9
    front = pos(t)
    for i in range(14):
        x = 90 + i * 66; d = front - i
        ang = clamp(d / 0.6) * 1.2 if d > 0 else 0
        domino(c, x, 1050, ang, mix(WHITE, YEL, clamp(d)))
    if t < ts: counter(c, W / 2, 520, 300, 343, s.P(s.t0, 0.8), 130, suffix=" m/s")
    else:
        v = lerp(343, 1.4, ease((t - ts) / 1.2)); text(c, f"{v:,.1f} m/s" if v < 10 else f"{v:,.0f} m/s", W / 2, 520, 130, RED if v < 10 else YEL)
    if t > tw - 0.3:
        label(c, "= WALKING PACE", W / 2, 680, 56, YEL, OUT, s.P(tw - 0.3, 0.35))
    leo(c, 120 + clamp((t - ts) / 6) * 400, 2070, 0.7, "idle", "curious" if t < ts else "wow", t, look=(1, 0))

def s_talk(c, s):
    t = s.t; tsh = s.W("talk", "Shout")
    if t < tsh - 0.2:
        bg_color(c, rgb("#ffe6b8")); c.new_path(); c.rectangle(0, 1250, W, 700); fs(c, rgb("#c98a5a"), 0)
        tw = s.W("talk", "words"); p = clamp((t - tw + 0.6) / 2.0)
        leo(c, 230, 1300, 0.62, "point_right", "happy", t)
        leo(c, 860, 1300, 0.62, "idle", "curious" if p < 1 else "shock", t, colors=FRIEND, mirror=True)
        if t > tw - 0.6: bubble(c, lerp(330, 700, ease_out(p)), 720, "HI!", 70, 1, WHITE)
        clock(c, W / 2, 420, 85, (t - tw + 0.6) * 30 if t > tw - 0.6 else 0, s.P(s.W("talk", "two") - 0.3, 0.35))
        label(c, "2 SECONDS LATE", W / 2, 560, 54, RED, WHITE, s.P(s.W("talk", "late") - 0.2, 0.35))
    else:
        bg_color(c, rgb("#3f9b4a"))
        for i in range(11):
            y = 250 + i * 100; c.new_path(); c.move_to(80, y); c.line_to(W - 80, y); c.set_source_rgba(1, 1, 1, 0.75); c.set_line_width(6); c.stroke()
        c.new_path(); c.rectangle(80, 250, W - 160, 1000); c.set_source_rgb(1, 1, 1); c.set_line_width(10); c.stroke()
        text(c, "100 m", 980, 750, 46, WHITE)
        circle(c, W / 2, 1260, 34, rgb("#ffc928"), 7); circle(c, W / 2, 240, 34, rgb("#ff7aa8"), 7)
        p = clamp((t - tsh) / 4.5)
        bubble(c, W / 2, lerp(1170, 900, p), "HEY!", 64, s.P(tsh, 0.3), WHITE, tail=1)
        counter(c, W / 2, 560, 0, 71, s.P(s.W("talk", "minute") - 0.5, 1.2), 140, suffix=" SEC", col=YEL)

def s_storm(c, s):
    t = s.t; tl = s.W("storm", "lightning"); tt = s.W("storm", "twenty")
    bg_cinema(c, t, seed=7)
    town(c, 1300, t, 0.8)
    fl = clamp(1 - (t - tl) / 0.5) if t > tl else 0
    if 0 < t - tl < 0.35: bolt(c, 760, 360, 1.0)
    glow(c, 780, 400, 800, (0.85, 0.9, 1), 0.8 * fl)
    storm_cloud(c, 780, 360, 160, 0.75)
    arrow(c, (160, 760), (720, 760), s.P(s.W("storm", "two"), 0.6), WHITE, 10, 26); label(c, "2 KM", 440, 700, 50, WHITE, OUT, s.P(s.W("storm", "two"), 0.35))
    mins = 24 * ease(clamp((t - tt) / 2.4)) if t > tt else 0
    clock(c, W / 2, 930, 110, mins * 60 % 720, s.P(tt - 0.4, 0.35))
    text(c, f"{int(mins):02d} MIN LATER" if t > tt else "", W / 2, 1100, 64, YEL)
    T_TH = s.B["storm"]["t1"] - 0.4
    if t > T_TH:
        lt = t - T_TH; ring(c, 780, 400, 120 + lt * 1400, WHITE, 18, 1 - clamp(lt / 0.6)); pop_text(c, "BOOM!", W / 2, 560, 150, clamp(lt / 0.25), YEL)
    leo(c, 860, 2070, 0.72, "idle" if t < T_TH else "shock", "smirk" if t < T_TH else "shock", t, look=(-0.4, -0.9))

def s_wind(c, s):
    t = s.t; tu = s.W("wind", "upwind")
    bg_sky(c, t)
    for i in range(7):  # wind streaks blowing right
        u = ((t * 0.9 + i / 7) % 1); y = 380 + i * 110
        c.new_path(); c.move_to(-150 + u * 1400, y); c.curve_to(-50 + u * 1400, y - 30, 30 + u * 1400, y + 30, 120 + u * 1400, y)
        c.set_source_rgba(1, 1, 1, 0.8); c.set_line_width(10); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke()
    label(c, "WIND  →", 280, 300, 56, WHITE, OUT, s.P(s.t0 + 0.2, 0.3))
    for k in range(4):  # Leo's voice rings get blown downwind (to the right)
        u = ((t - s.t0) * 0.6 + k / 4) % 1
        ring(c, 760 + u * 380, 1000, 30 + u * 180, YEL, 9, 1 - u)
    leo(c, 760, 1300, 0.62, "point_left", "happy" if t < tu else "worried", t)
    leo(c, 220, 1300, 0.62, "think", "curious", t, colors=FRIEND)
    bubble(c, 230, 760, "...?", 60, s.P(tu, 0.3))
    label(c, "CAN'T HEAR YOU", 300, 640, 50, RED, WHITE, s.P(s.W("wind", "couldn't"), 0.35))
    label(c, "WIND > SOUND", W / 2, 460, 60, YEL, OUT, s.P(s.W("wind", "outrun") - 0.2, 0.35))

def s_boom(c, s):
    t = s.t; tr = s.W("boom", "Runners"); tb = s.W("boom", "bikes"); tc = s.W("boom", "cars")
    bg_sky(c, t, top="#ffb36b", bot="#ffe3b8")
    c.new_path(); c.rectangle(0, 1180, W, 760); fs(c, rgb("#55555f"), 0)
    for i in range(8):
        x = ((i * 180 - t * 600) % (W + 200)) - 100; c.new_path(); c.rectangle(x, 1255, 90, 16); c.set_source_rgb(1, 0.9, 0.4); c.fill()
    who = [(s.t0, jogger, 1.4), (tb - 0.1, bike, 1.4), (tc - 0.1, car, 1.3)]
    for i, (t0, fn, sc_) in enumerate(who):
        nxt = who[i + 1][0] if i + 1 < len(who) else 1e9
        if t0 <= t < nxt + 0.3:
            lt = t - t0; x = lerp(-150, W + 250, clamp(lt / 2.6))
            mach_cone(c, x, 1170 - (60 if fn is car else 120), 160)
            fn(c, x, 1175, sc_, t)
            for k, bt in enumerate((0.35, 1.3)):
                if lt > bt: burst(c, x - 150, 900, lt - bt, 12, 30, 230, YEL, seed=i * 7 + k, size=14)
            pop_text(c, "BOOM!", lerp(260, 820, (i % 2)), 700, 120, clamp((lt - 0.35) / 0.25) * (1 - clamp((lt - 1.6) / 0.3)), YEL)
    label(c, "3 m/s  >  1.4 m/s", W / 2, 420, 60, WHITE, OUT, s.P(s.W("boom", "jogs") - 0.1, 0.35))
    leo(c, 540, 2080, 0.74, "cover", "shock", t)

def s_end(c, s):
    t = s.t; tq = s.W("end", "Could"); ta = s.W("end", "clouds")
    bg_cinema(c, t, seed=8)
    glow(c, W / 2, 820, 520, (0.5, 0.8, 1), 0.5)
    c.new_path(); rrect(c, 290, 520, 500, 560, 60); fs(c, (0.75, 0.9, 1), 9, 0.25)          # vacuum chamber
    for i in range(70):
        a = i * 2.39996; r = 190 * math.sqrt(i / 70)
        x, y = W / 2 + math.cos(a) * r + math.sin(t * 9 + i) * 3, 800 + math.sin(a) * r * 1.1 + math.cos(t * 8 + i) * 3
        circle(c, x, y, 9, CYAN, 3, s.P(ta - 0.3 + i * 0.005, 0.2))
    label(c, "-273 °C", 360, 470, 50, SKY, OUT, s.P(s.W("end", "colder"), 0.35))
    label(c, "SOUND: ~1 mm/s", 720, 1140, 50, YEL, OUT, s.P(s.W("end", "really") , 0.35))
    for k in range(3): snowflake(c, 300 + k * 240, 1240, 34 * s.P(s.W("end", "colder") + k * 0.1, 0.3))
    pop_text(c, "COULD YOU SURVIVE?", W / 2, 330, 84, s.P(tq, 0.35), YEL)
    leo(c, 540, 2080, 0.78, "think" if t < tq else "shrug", "wow" if t < tq else "curious", t)

SCENES = [("cold", s_cold), ("why", s_why), ("talk", s_talk), ("storm", s_storm), ("wind", s_wind), ("boom", s_boom), ("end", s_end)]

def cams(Wt, B):
    return {"cold": [(0, 540, 960, 1.08), (B["cold"]["t1"], 540, 960, 1.0)],
            "storm": [(Wt("storm"), 540, 960, 1.0), (Wt("storm", "twenty"), 540, 1020, 1.12), (B["storm"]["t1"] - 0.4, 540, 960, 1.0)],
            "end": [(Wt("end"), 540, 880, 1.15), (Wt("end", "Could"), 540, 960, 1.0)]}

def impacts(Wt, B):
    return [B["storm"]["t1"] - 0.4, Wt("boom", "Runners")]

def sfx(Wt, B, put):
    put(sfx_boom(40, 2.2), 0.0, 0.6)                                   # frame-1 rumble
    for i in range(10): put(sfx_tick(), Wt("why", "dominoes") + i * 0.11, 0.5)
    put(sfx_pop(), Wt("talk", "late"), 0.6)
    put(sfx_pop(500), Wt("talk", "minute"), 0.6)
    put(sfx_ding(1800), Wt("storm", "lightning"), 0.5)
    put(sfx_boom(38, 2.5), B["storm"]["t1"] - 0.4, 1.0)
    put(sfx_whoosh(9, 1.2), Wt("wind", "breeze"), 0.6)
    for w in ("Runners", "bikes", "cars"):
        put(sfx_boom(55, 1.2), Wt("boom", w) + 0.35, 0.7)
    put(sfx_ding(1568), Wt("end", "Could"), 0.6)
