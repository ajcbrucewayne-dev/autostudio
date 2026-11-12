"""Motion-graphics kits: clean flat shapes, icons, pills, arrows, bars, dials, counters with smooth easing.
Registered into scenes.KITS as "mg_*". Draw on the 2x layer (coordinates in 1x units, scaled with z()).
"""
import math
from PIL import ImageDraw
import scenes
from scenes import z, W, H, Z, mix
from render import font, FONT_SANS, ease_back, ease_out, emoji_img

BG = (14, 20, 48); PANEL = (30, 40, 86); YEL = (255, 204, 0); CYAN = (0, 212, 255); CORAL = (255, 94, 98)
WHITE = (255, 255, 255); MUTED = (140, 150, 190); OCEAN = (40, 120, 230); LAND = (70, 200, 120); MOONC = (225, 228, 240)

def k_in(lt, start, dur=0.45): return max(0.0, min(1.0, (lt - start) / dur))

def bg(d, t, col=BG):
    d.rectangle(z(0, 0, W, H), fill=col)
    for i in range(0, W + 1, 90):
        for j in range(0, H + 1, 90):
            d.ellipse(z(i - 2, j - 2, i + 2, j + 2), fill=mix(col, WHITE, 0.08))
    for k, (cx, cy, r) in enumerate(((0.15, 0.2, 260), (0.9, 0.6, 340))):
        x = W * cx + 40 * math.sin(t * 0.4 + k * 2); y = H * cy + 40 * math.cos(t * 0.3 + k)
        d.ellipse(z(x - r, y - r, x + r, y + r), fill=mix(col, WHITE, 0.035))

def text(d, x, y, s, size, color=WHITE, k=1.0, anchor="mm", bgcol=BG):
    if k <= 0: return
    d.text((x * Z, (y + (1 - ease_out(k)) * 40) * Z), s, font=font(FONT_SANS, int(size * Z)), fill=mix(bgcol, color, min(1, k)), anchor=anchor)

def pill(d, x, y, s, color, k, size=44, fg=BG):
    if k <= 0: return
    sc = max(0.01, ease_back(k)); f = font(FONT_SANS, max(6, int(size * Z * sc)))
    w = f.getlength(s) / Z / 2 + 34 * sc; h = size * 0.8 * sc
    d.rounded_rectangle(z(x - w, y - h, x + w, y + h), int(h * Z), fill=color)
    d.text((x * Z, y * Z), s, font=f, fill=fg, anchor="mm")

def arrow(d, x0, y0, x1, y1, color, k, width=10, head=26):
    if k <= 0: return
    k = ease_out(k); x2, y2 = x0 + (x1 - x0) * k, y0 + (y1 - y0) * k
    d.line(z(x0, y0, x2, y2), fill=color, width=width * Z)
    a = math.atan2(y2 - y0, x2 - x0)
    d.polygon(z(x2 + math.cos(a) * head * 0.6, y2 + math.sin(a) * head * 0.6,
                x2 + math.cos(a + 2.5) * head, y2 + math.sin(a + 2.5) * head,
                x2 + math.cos(a - 2.5) * head, y2 + math.sin(a - 2.5) * head), fill=color)

def earth(d, x, y, r, k=1.0, tilt=0.0):
    if k <= 0: return
    r *= max(0.01, ease_back(k))
    scenes.disc(d, x, y, r, OCEAN)
    for ox, oy, rx, ry in ((-0.35, -0.3, 0.32, 0.22), (0.3, 0.1, 0.25, 0.35), (-0.15, 0.45, 0.2, 0.12)):
        a = math.radians(tilt); px = ox * math.cos(a) - oy * math.sin(a); py = ox * math.sin(a) + oy * math.cos(a)
        d.ellipse(z(x + (px - rx) * r, y + (py - ry) * r, x + (px + rx) * r, y + (py + ry) * r), fill=LAND)
    d.ellipse(z(x - r, y - r, x + r, y + r), outline=WHITE, width=5 * Z)

def moon(d, x, y, r, k=1.0, a=1.0):
    if k <= 0 or a <= 0.02: return
    r *= max(0.01, ease_back(k)); c = mix(BG, MOONC, a)
    scenes.disc(d, x, y, r, c)
    for ox, oy, rr in ((-0.3, -0.2, 0.2), (0.25, 0.2, 0.15), (0.1, -0.4, 0.1)):
        scenes.disc(d, x + ox * r, y + oy * r, rr * r, mix(BG, (185, 190, 210), a))

def emoji(out, ch, x, y, s, k):
    if k > 0: out.append({"emoji": ch, "x": x, "y": y, "s": max(8, int(s * ease_back(k)))})

# ------------------------------------------------------------------ kits
def mg_title(layer, d, P, t):
    bg(d, t); lt = P.lt
    words = P("words", "WHAT IF|THE MOON|VANISHED?").split("|")
    for i, w in enumerate(words):
        k = k_in(lt, 0.15 + i * 0.35, 0.4)
        col = YEL if i == len(words) - 1 else WHITE
        text(d, W / 2, H * (0.20 + i * 0.075), w, 112, col, k)
    k = k_in(lt, 1.2, 0.6); moon(d, W / 2, H * 0.47, 120, k, 1 - k_in(lt, 2.2, 1.0) * 0.85)
    for i in range(10):
        a = i * math.pi / 5 + lt * 0.6; rr = 190 + 20 * math.sin(lt * 3 + i)
        x, y = W / 2 + math.cos(a) * rr, H * 0.47 + math.sin(a) * rr
        if k > 0: scenes.disc(d, x, y, 8 * k, CYAN if i % 2 else YEL)
    return []

def mg_darkness(layer, d, P, t):
    bg(d, t); lt = P.lt; a = P("moon", 1.0)
    text(d, W / 2, H * 0.12, "NIGHT BRIGHTNESS", 64, MUTED, k_in(lt, 0.1))
    moon(d, W * 0.3, H * 0.30, 110, k_in(lt, 0.2), a)
    pill(d, W * 0.3, H * 0.42, "MOONLIGHT", YEL, k_in(lt, 0.5) * (0.2 + 0.8 * a))
    for i in range(14):
        x, y = W * (0.62 + 0.3 * ((i * 37) % 10) / 10), H * (0.22 + 0.18 * ((i * 53) % 10) / 10)
        tw = 0.5 + 0.5 * math.sin(t * 3 + i)
        scenes.disc(d, x, y, 5 + 3 * tw, mix(BG, WHITE, k_in(lt, 0.4 + i * 0.05)))
    pill(d, W * 0.76, H * 0.42, "STARLIGHT", CYAN, k_in(lt, 0.8))
    x0, x1, y = 120, W - 120, H * 0.52
    d.rounded_rectangle(z(x0, y - 26, x1, y + 26), 26 * Z, fill=PANEL)
    lvl = ease_out(k_in(lt, 0.6, 0.8)) * (0.12 + 0.88 * a)
    d.rounded_rectangle(z(x0, y - 26, x0 + max(52, (x1 - x0) * lvl), y + 26), 26 * Z, fill=mix(CYAN, YEL, a))
    return []

def mg_gravity(layer, d, P, t):
    bg(d, t); lt = P.lt
    ex, ey, mx, my = W * 0.36, H * 0.33, W * 0.83, H * 0.33
    kb = ease_out(k_in(lt, 1.2, 1.2))
    pts = []
    for i in range(72):
        a = 2 * math.pi * i / 72; rr = 175 * (1.05 + 0.22 * kb * math.cos(a) ** 2)
        pts.append(((ex + rr * math.cos(a)) * Z, (ey + rr * math.sin(a) * (1 - 0.08 * kb)) * Z))
    if k_in(lt, 0.2) > 0: d.polygon(pts, fill=mix(BG, CYAN, 0.45 * k_in(lt, 0.2)))
    earth(d, ex, ey, 160, k_in(lt, 0.0))
    moon(d, mx, my, 70, k_in(lt, 0.3))
    for i in range(3):
        off = (lt * 160 + i * 90) % 270
        if lt > 0.8: arrow(d, mx - 85 - off * 0.2, my + (i - 1) * 60, ex + 230 + (i - 1) * 0 - off * 0.05, ey + (i - 1) * 40, YEL, k_in(lt, 0.8 + i * 0.15), 8, 24)
    pill(d, W * 0.62, H * 0.19, "GRAVITY", YEL, k_in(lt, 1.0))
    pill(d, ex, H * 0.47, "OCEAN BULGE = HIGH TIDE", CYAN, k_in(lt, 2.2), 38)
    return []

def mg_tidebar(layer, d, P, t):
    bg(d, t); lt = P.lt
    text(d, W / 2, H * 0.10, "TIDE STRENGTH", 64, MUTED, k_in(lt, 0.05))
    base, top = H * 0.52, H * 0.18
    for i, (lab, v, col, emo) in enumerate((("WITH MOON", 1.0, CYAN, "🌕"), ("NO MOON", 0.33, CORAL, "🌑"))):
        x = W * (0.3 + 0.4 * i); k = ease_out(k_in(lt, 0.4 + i * 0.6, 1.0))
        h = (base - top) * v * k
        d.rounded_rectangle(z(x - 95, base - (base - top), x + 95, base), 24 * Z, fill=PANEL)
        if h > 4: d.rounded_rectangle(z(x - 95, base - h, x + 95, base), 24 * Z, fill=col)
        for j in range(3):  # little waves on top of the bar
            if h > 30:
                wy = base - h + 18 + 6 * math.sin(t * 5 + j)
                d.arc(z(x - 80 + j * 55, wy - 10, x - 30 + j * 55, wy + 10), 200, 340, fill=WHITE, width=4 * Z)
        text(d, x, base - h - 50, f"{int(v * 100 * k)}%", 72, WHITE, k_in(lt, 0.5 + i * 0.6))
        text(d, x, base + 50, lab, 40, MUTED, k_in(lt, 0.3 + i * 0.6))
    return []

def mg_coral(layer, d, P, t):
    bg(d, t); lt = P.lt; fade = P("fade", 0.0)
    text(d, W / 2, H * 0.11, "CORAL SPAWNING CALENDAR", 56, MUTED, k_in(lt, 0.05))
    phases = [0.0, 0.25, 0.5, 0.75, 1.0, 0.75, 0.5]
    for i, ph in enumerate(phases):
        x, y = W * (0.14 + i * 0.12), H * 0.22; k = k_in(lt, 0.2 + i * 0.1)
        a = (1 - fade)
        if k > 0:
            scenes.disc(d, x, y, 42 * ease_back(k), mix(BG, (60, 70, 110), 1))
            if ph > 0:
                w = 42 * ease_back(k) * ph
                d.ellipse(z(x - w, y - 42 * ease_back(k), x + w, y + 42 * ease_back(k)), fill=mix(BG, MOONC, a))
        if ph == 1.0 and lt > 1.2 and fade < 0.5:
            d.ellipse(z(x - 62, y - 62, x + 62, y + 62), outline=YEL, width=6 * Z)
    out = []
    emoji(out, "🪸", W * 0.5, H * 0.40, 260, k_in(lt, 0.6))
    if fade < 0.5:
        for i in range(10):
            x = W * (0.38 + 0.024 * i); y = H * 0.36 - ((lt * 90 + i * 37) % 200)
            if lt > 1.4: scenes.disc(d, x, y, 7, (255, 180, 200))
    else: emoji(out, "❓", W * 0.73, H * 0.33, 150, k_in(lt, P.sd * 0.55))
    return out

def mg_dial(layer, d, P, t):
    bg(d, t); lt = P.lt; wob = P("wobble", 0.0)
    cx, cy, R = W / 2, H * 0.42, 330
    text(d, W / 2, H * 0.10, "EARTH'S TILT", 64, MUTED, k_in(lt, 0.05))
    k = ease_out(k_in(lt, 0.1, 0.8))
    d.arc(z(cx - R, cy - R, cx + R, cy + R), 180, 180 + 180 * k, fill=PANEL, width=46 * Z)
    d.arc(z(cx - R, cy - R, cx + R, cy + R), 180 + 18, 180 + 32, fill=mix(PANEL, CYAN, 0.8 * k), width=46 * Z)  # stable zone
    for deg in range(0, 91, 15):
        a = math.radians(180 + deg * 2)
        d.line(z(cx + math.cos(a) * (R - 40), cy + math.sin(a) * (R - 40), cx + math.cos(a) * (R - 70), cy + math.sin(a) * (R - 70)), fill=MUTED, width=4 * Z)
    val = 23.4 + wob * math.sin(t * 2.6) * min(1, lt / 1.0)
    val = max(0, min(89, val)) * ease_out(k_in(lt, 0.4, 1.0))
    a = math.radians(180 + val * 2)
    d.line(z(cx, cy, cx + math.cos(a) * (R - 60), cy + math.sin(a) * (R - 60)), fill=YEL if wob < 5 else CORAL, width=12 * Z)
    scenes.disc(d, cx, cy, 26, WHITE)
    text(d, cx, cy + 90, f"{val:4.1f}°", 110, YEL if wob < 5 else CORAL, k_in(lt, 0.3))
    earth(d, cx, cy - 150, 70, k_in(lt, 0.5), tilt=val)
    pill(d, cx, cy + 210, "STABLE THANKS TO THE MOON" if wob < 5 else "NO MOON: WILD SWINGS", CYAN if wob < 5 else CORAL, k_in(lt, 0.9), 36)
    return []

def mg_years(layer, d, P, t):
    bg(d, t); lt = P.lt
    k = ease_out(k_in(lt, 0.2, max(0.5, P.sd * 0.75)))
    text(d, W / 2, H * 0.17, f"{int(10_000_000 * k):,}", 120, YEL, k_in(lt, 0.1))
    text(d, W / 2, H * 0.24, "YEARS", 64, WHITE, k_in(lt, 0.2))
    x0, x1, y = 110, W - 110, H * 0.36
    d.rounded_rectangle(z(x0, y - 14, x1, y + 14), 14 * Z, fill=PANEL)
    d.rounded_rectangle(z(x0, y - 14, x0 + max(28, (x1 - x0) * k), y + 14), 14 * Z, fill=CYAN)
    for i in range(6):
        x = x0 + (x1 - x0) * i / 5; tilt = 23 + (30 * math.sin(i * 1.7) if i else 0) * k
        earth(d, x, y + 120, 48, k_in(lt, 0.3 + i * 0.12), tilt * 3)
        d.line(z(x - math.sin(math.radians(tilt)) * 75, y + 120 - math.cos(math.radians(tilt)) * 75,
                 x + math.sin(math.radians(tilt)) * 75, y + 120 + math.cos(math.radians(tilt)) * 75), fill=CORAL, width=4 * Z) if k_in(lt, 0.3 + i * 0.12) >= 1 else None
    return []

def mg_split(layer, d, P, t):
    lt = P.lt; s = ease_out(k_in(lt, 0.0, 0.5))
    d.rectangle(z(0, 0, W, H), fill=BG)
    d.rectangle(z(0, 0, W / 2 * s, H), fill=(40, 110, 200)); d.rectangle(z(W - W / 2 * s, 0, W, H), fill=(220, 70, 40))
    out = []
    emoji(out, "🥶", W * 0.25, H * 0.27, 230, k_in(lt, 0.4)); emoji(out, "🥵", W * 0.75, H * 0.27, 230, k_in(lt, 0.9))
    pill(d, W * 0.25, H * 0.42, "ICE AGES", WHITE, k_in(lt, 0.6), 50, (40, 110, 200))
    pill(d, W * 0.75, H * 0.42, "HEATWAVES", WHITE, k_in(lt, 1.1), 50, (220, 70, 40))
    for i in range(8):
        x = W * 0.05 + (i * 61) % (W * 0.4); y = (t * (110 + i * 9) + i * 230) % H
        emoji(out, "❄️", x, y, 60, 1)
    return out

def mg_recap(layer, d, P, t):
    bg(d, t); lt = P.lt
    text(d, W / 2, H * 0.10, "WITHOUT THE MOON", 64, YEL, k_in(lt, 0.05))
    rows = P("rows", "🌑|DARKER NIGHTS|🌊|WEAKER TIDES|🌍|A WOBBLING PLANET").split("|")
    out = []
    for i in range(len(rows) // 2):
        y = H * (0.20 + i * 0.105); k = k_in(lt, 0.4 + i * 0.9 * P("gap", 1.0), 0.5)
        if k <= 0: continue
        x0 = 110 - (1 - ease_out(k)) * 600
        d.rounded_rectangle(z(x0, y - 70, x0 + W - 220, y + 70), 70 * Z, fill=PANEL)
        emoji(out, rows[2 * i], x0 + 75, y, 100, k)
        text(d, x0 + 160, y, rows[2 * i + 1], 54, WHITE, k, anchor="lm", bgcol=PANEL)
    return out

KITS = {k: v for k, v in globals().items() if k.startswith("mg_")}
scenes.KITS.update(KITS)
