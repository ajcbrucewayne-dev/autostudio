"""Business-explainer motion-graphics kits ("bz_*"): clean fintech look for client demos.
Registered into scenes.KITS. Same drawing conventions as mograph (1x coords, z() scaling).
"""
import math
import scenes
from scenes import z, W, H, Z, mix
from mograph import text, pill, arrow, k_in, emoji, WHITE, YEL, CYAN, CORAL, MUTED
from render import ease_out, ease_back

BG = (12, 24, 38); PANEL = (24, 44, 66); MINT = (46, 214, 160); GOLD = (255, 196, 61); SKY = (90, 170, 255)

def bg(d, t):
    d.rectangle(z(0, 0, W, H), fill=BG)
    for i in range(0, W + 1, 120): d.line(z(i, 0, i, H), fill=mix(BG, WHITE, 0.04), width=Z)
    for j in range(0, H + 1, 120): d.line(z(0, j, W, j), fill=mix(BG, WHITE, 0.04), width=Z)
    x = W * 0.8 + 50 * math.sin(t * 0.4); d.ellipse(z(x - 380, H * 0.15 - 380, x + 380, H * 0.15 + 380), fill=mix(BG, MINT, 0.05))

def T(d, x, y, s, size, col=WHITE, k=1.0, anchor="mm"): text(d, x, y, s, size, col, k, anchor, BG)
def money(v): return f"${v:,.0f}"
def fv(m, r, months): i = r / 12; return m * ((1 + i) ** months - 1) / i

def bz_hook(layer, d, P, t):
    bg(d, t); lt = P.lt; out = []
    T(d, W / 2, H * 0.17, "$100 / MONTH", 96, WHITE, k_in(lt, 0.1))
    k = ease_out(k_in(lt, 0.9, 2.2)); T(d, W / 2, H * 0.30, money(121997 * k), 150, MINT, k_in(lt, 0.8))
    arrow(d, W / 2, H * 0.205, W / 2, H * 0.255, GOLD, k_in(lt, 0.5), 12, 34)
    for i in range(7):  # coins popping
        kk = k_in(lt, 1.0 + i * 0.25, 0.4); emoji(out, "🪙", W * (0.2 + 0.1 * i), H * 0.42 - 30 * math.sin(i), 90, kk)
    pill(d, W / 2, H * 0.52, "HOW?", GOLD, k_in(lt, 2.6), 56)
    return out

VMAX = 1000 * (1.07 ** 15 - 1)
def bars(d, lt, vals, col, x0=140, x1=W - 140, base=H * 0.55, top=H * 0.22, start=0.3, step=0.12, labels=True, vmax=VMAX):
    n = len(vals); bw = (x1 - x0) / n * 0.7
    for i, v in enumerate(vals):
        k = ease_out(k_in(lt, start + i * step, 0.5)); x = x0 + (x1 - x0) * (i + 0.5) / n; h = (base - top) * v / vmax * k
        if h > 2: d.rounded_rectangle(z(x - bw / 2, base - h, x + bw / 2, base), int(14 * Z), fill=col)
        if labels and (i + 1) % 5 == 0: T(d, x, base + 40, f"YEAR {i + 1}", 32, MUTED, k_in(lt, start + i * step))

def bz_simple(layer, d, P, t):
    bg(d, t); lt = P.lt
    pill(d, W / 2, H * 0.11, "SIMPLE INTEREST", SKY, k_in(lt, 0.1), 52)
    bars(d, lt, [70 * i for i in range(1, 16)], SKY)
    T(d, W / 2, H * 0.63, "$1,000 at 7%: +$70 a year. Never more.", 46, WHITE, k_in(lt, 1.6))
    return []

def bz_compound(layer, d, P, t):
    bg(d, t); lt = P.lt; out = []
    pill(d, W / 2, H * 0.11, "COMPOUND INTEREST", MINT, k_in(lt, 0.1), 52)
    bars(d, lt, [70 * i for i in range(1, 16)], mix(BG, SKY, 0.35), start=0.1, step=0.0, labels=False)
    bars(d, lt, [1000 * (1.07 ** i - 1) for i in range(1, 16)], MINT, start=0.3)
    T(d, W / 2, H * 0.63, "Your earnings start earning too.", 50, WHITE, k_in(lt, 1.4))
    kk = k_in(lt, 2.4, 0.6); x = W * 0.15 + W * 0.7 * ease_out(k_in(lt, 2.4, 2.5)); r = 40 + 50 * ease_out(k_in(lt, 2.4, 2.5))
    if kk > 0:  # the snowball
        y = H * 0.74 - r + 8
        scenes.disc(d, x, y, r, mix(BG, WHITE, kk)); d.line(z(80, H * 0.74 + 8, W - 80, H * 0.74 + 8), fill=mix(BG, SKY, kk), width=6 * Z)
        T(d, W / 2, H * 0.80, "like a snowball", 44, MUTED, kk)
    return out

def bz_chart(layer, d, P, t):
    bg(d, t); lt = P.lt
    x0, x1, y0, y1 = 140, W - 120, H * 0.60, H * 0.20
    d.line(z(x0, y0, x1, y0), fill=MUTED, width=3 * Z); d.line(z(x0, y0, x0, y1), fill=MUTED, width=3 * Z)
    T(d, W / 2, H * 0.11, "$100/month · 7% a year", 54, WHITE, k_in(lt, 0.1))
    kx = ease_out(k_in(lt, 0.6, 4.0)); vmax = fv(100, 0.07, 360)
    pts_d, pts_t = [], []
    for m in range(0, int(360 * kx) + 1, 6):
        x = x0 + (x1 - x0) * m / 360
        pts_d.append((x * Z, (y0 - (y0 - y1) * 100 * m / vmax) * Z)); pts_t.append((x * Z, (y0 - (y0 - y1) * fv(100, 0.07, max(m, 1)) / vmax) * Z))
    if len(pts_t) > 1:
        d.polygon(pts_t + [(pts_t[-1][0], y0 * Z), (x0 * Z, y0 * Z)], fill=mix(BG, MINT, 0.25))
        d.line(pts_t, fill=MINT, width=8 * Z); d.line(pts_d, fill=SKY, width=6 * Z)
    m = int(360 * kx)
    T(d, x0 + 10, H * 0.66, f"YEAR {m // 12}", 44, MUTED, k_in(lt, 0.6), anchor="lm")
    pill(d, W * 0.33, H * 0.72, f"YOU PUT IN {money(100 * m)}", SKY, k_in(lt, 1.2), 40)
    pill(d, W * 0.62, H * 0.79, f"YOU HAVE {money(fv(100, 0.07, max(m, 1)))}", MINT, k_in(lt, 2.0), 48)
    T(d, W / 2, H * 0.88, "Example only · not financial advice", 30, MUTED, k_in(lt, 0.5))
    return []

def bz_late(layer, d, P, t):
    bg(d, t); lt = P.lt; out = []
    T(d, W / 2, H * 0.11, "START 10 YEARS LATER?", 64, CORAL, k_in(lt, 0.1))
    base, top = H * 0.58, H * 0.20
    for i, (lab, v, col) in enumerate((("START NOW", fv(100, 0.07, 360), MINT), ("START LATER", fv(100, 0.07, 240), CORAL))):
        x = W * (0.3 + 0.4 * i); k = ease_out(k_in(lt, 0.4 + i * 0.7, 1.0)); h = (base - top) * v / fv(100, 0.07, 360) * k
        d.rounded_rectangle(z(x - 110, top, x + 110, base), 24 * Z, fill=PANEL)
        if h > 4: d.rounded_rectangle(z(x - 110, base - h, x + 110, base), 24 * Z, fill=col)
        T(d, x, base - h - 50, money(v * k), 56, WHITE, k_in(lt, 0.5 + i * 0.7)); T(d, x, base + 50, lab, 40, MUTED, k_in(lt, 0.3 + i * 0.7))
    pill(d, W / 2, H * 0.70, "TIME = THE SECRET INGREDIENT", GOLD, k_in(lt, 2.4), 44)
    return out

def bz_cta(layer, d, P, t):
    bg(d, t); lt = P.lt; out = []
    T(d, W / 2, H * 0.24, "START SMALL.", 110, WHITE, k_in(lt, 0.1)); T(d, W / 2, H * 0.32, "START TODAY.", 110, MINT, k_in(lt, 0.6))
    k = k_in(lt, 1.2, 0.5)
    if k > 0:
        s = ease_back(k); w, h = 300 * s, 110 * s
        d.rounded_rectangle(z(W / 2 - w, H * 0.47 - h, W / 2 + w, H * 0.47 + h), int(30 * Z), outline=mix(BG, WHITE, k), width=4 * Z)
        T(d, W / 2, H * 0.47, "YOUR LOGO HERE", int(50 * s) + 1, WHITE, k)
    return out

KITS = {k: v for k, v in globals().items() if k.startswith("bz_")}
scenes.KITS.update(KITS)
