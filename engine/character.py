"""Blip 2.0: expressive 2D hero character with arms, legs, eyebrows, antenna and poses.

draw_blip(frame, x, y, size, pose, t, mouth=0.0, look=(0,0), facing=1)
Poses: idle, look_up, shock, point, sad, scared, wave, cheer, think, cling
"""
import math
from PIL import Image, ImageDraw

SS = 2
BODY = (56, 214, 196); BODY_DK = (24, 140, 132); BODY_LT = (140, 245, 230); LINE = (14, 60, 64)
BELLY = (190, 252, 240); IRIS = (70, 120, 255); CHEEK = (255, 140, 160)

POSES = {  # (left arm angle, right arm angle, elbow bend) degrees: 0 = straight down, 90 = sideways, 180 = up
    "idle": (14, 14, 20), "look_up": (16, 16, 10), "shock": (150, 150, 120), "point": (25, 120, 0),
    "sad": (6, 6, 0), "scared": (165, 165, 20), "wave": (25, 150, 40), "cheer": (160, 160, 10),
    "think": (25, 140, 140), "cling": (110, 110, 30),
}

def _arm(d, sx, sy, ang, bend, side, L, w, wave_t=0.0):
    a = math.radians(ang) * side
    ex, ey = sx + math.sin(a) * L * 0.55, sy + math.cos(a) * L * 0.55
    a2 = a + math.radians(bend) * side + wave_t
    hx, hy = ex + math.sin(a2) * L * 0.5, ey + math.cos(a2) * L * 0.5
    d.line((sx, sy, ex, ey, hx, hy), fill=LINE, width=int(w + 8 * SS), joint="curve")
    d.line((sx, sy, ex, ey, hx, hy), fill=BODY, width=int(w), joint="curve")
    r = w * 0.85
    d.ellipse((hx - r, hy - r, hx + r, hy + r), fill=BODY, outline=LINE, width=4 * SS)

def draw_blip(frame, x, y, size, pose="idle", t=0.0, mouth=0.0, look=(0.0, 0.0), facing=1, alpha=1.0):
    """x,y = feet position in frame pixels; size = body height in px."""
    S = size * SS; Wd, Hd = int(S * 2.4), int(S * 2.4)
    im = Image.new("RGBA", (Wd, Hd), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cx, base = Wd / 2, Hd * 0.86
    la, ra, bend = POSES.get(pose, POSES["idle"])
    shake = math.sin(t * 40) * S * 0.015 if pose in ("scared", "shock") else 0
    bob = math.sin(t * 3.0) * S * 0.015
    squash = 1 + 0.03 * math.sin(t * 3.0)
    bw, bh = S * 0.42 * (2 - squash), S * 0.5 * squash
    by = base - S * 0.16 - 2 * bh + bob
    cx += shake
    # shadow + legs
    d.ellipse((cx - bw * 0.9, base - S * 0.04, cx + bw * 0.9, base + S * 0.05), fill=(0, 0, 0, 70))
    for side in (-1, 1):
        lx = cx + side * bw * 0.42; step = math.sin(t * 9) * S * 0.04 * side if pose == "scared" else 0
        d.rounded_rectangle((lx - S * 0.07, by + bh * 1.6, lx + S * 0.07, base - S * 0.04 + step), S * 0.05, fill=BODY_DK, outline=LINE, width=4 * SS)
        d.ellipse((lx - S * 0.13 + side * S * 0.03, base - S * 0.1 + step, lx + S * 0.13 + side * S * 0.03, base + step), fill=BODY_DK, outline=LINE, width=4 * SS)
    # antenna
    ax0, ay0 = cx + S * 0.05, by + bh * 0.04
    sway = math.sin(t * 4) * S * 0.06
    ax1, ay1 = ax0 + S * 0.1 + sway, ay0 - S * 0.22
    d.line((ax0, ay0, ax0 + S * 0.05 + sway * 0.5, ay0 - S * 0.16, ax1, ay1), fill=LINE, width=6 * SS, joint="curve")
    glow = 0.6 + 0.4 * math.sin(t * 5)
    for k, a in ((2.2, 40), (1.6, 80)):
        r = S * 0.05 * k; d.ellipse((ax1 - r, ay1 - r, ax1 + r, ay1 + r), fill=(255, 230, 90, int(a * glow)))
    r = S * 0.05; d.ellipse((ax1 - r, ay1 - r, ax1 + r, ay1 + r), fill=(255, 220, 80), outline=LINE, width=3 * SS)
    # arms behind body for some poses
    L, aw = S * 0.46, S * 0.1
    sh_y = by + bh * 0.95
    wave_t = math.sin(t * 10) * 0.5 if pose == "wave" else (math.sin(t * 12) * 0.15 if pose == "cheer" else 0)
    arms = lambda: [_arm(d, cx + side * bw * 0.82, sh_y, (la if side < 0 else ra), bend if not (pose == "point" and side < 0) else 15,
                         side, L, aw, wave_t if side > 0 else (wave_t if pose == "cheer" else 0)) for side in (-1, 1)]
    # body
    box = (cx - bw, by, cx + bw, by + bh * 2)
    d.ellipse(box, fill=BODY_DK, outline=LINE, width=6 * SS)
    d.ellipse((cx - bw * 0.93, by + bh * 0.02, cx + bw * 0.86, by + bh * 1.86), fill=BODY)
    d.ellipse((cx - bw * 0.55, by + bh * 1.0, cx + bw * 0.55, by + bh * 1.85), fill=BELLY)
    d.ellipse((cx - bw * 0.6, by + bh * 0.18, cx - bw * 0.15, by + bh * 0.48), fill=BODY_LT)
    arms()
    # face
    fy = by + bh * 0.78; lx, ly = look
    if pose == "look_up": ly = -1
    er = S * 0.115; eh = er * (1.3 if pose in ("shock", "scared") else 1.12)
    for side in (-1, 1):
        ex = cx + side * bw * 0.36 + facing * S * 0.02
        d.ellipse((ex - er, fy - eh, ex + er, fy + eh), fill="white", outline=LINE, width=4 * SS)
        ir = er * (0.55 if pose in ("shock", "scared") else 0.68)
        px, py = ex + lx * er * 0.35 + facing * er * 0.1, fy + ly * eh * 0.4
        d.ellipse((px - ir, py - ir, px + ir, py + ir), fill=IRIS)
        pr = ir * 0.55; d.ellipse((px - pr, py - pr, px + pr, py + pr), fill=(12, 16, 30))
        hr = ir * 0.32; d.ellipse((px - ir * 0.45 - hr, py - ir * 0.45 - hr, px - ir * 0.45 + hr, py - ir * 0.45 + hr), fill="white")
        hr2 = hr * 0.5; d.ellipse((px + ir * 0.35 - hr2, py + ir * 0.3 - hr2, px + ir * 0.35 + hr2, py + ir * 0.3 + hr2), fill="white")
        # brows
        byw = fy - eh - S * 0.06
        inner = {"shock": -0.06, "scared": -0.08, "sad": -0.07, "think": 0.03, "point": 0.02}.get(pose, 0.0)
        if pose == "think" and side < 0: inner = -0.05
        x0, x1 = ex - er * 0.9, ex + er * 0.9
        yi = byw + S * inner  # inner end height
        yo = byw
        if side < 0: d.line((x0, yo, x1, yi), fill=LINE, width=7 * SS)
        else: d.line((x0, yi, x1, yo), fill=LINE, width=7 * SS)
        d.ellipse((ex - er * 0.8, fy + eh * 0.95, ex + er * 0.5, fy + eh * 1.35), fill=CHEEK) if side < 0 else \
            d.ellipse((ex - er * 0.5, fy + eh * 0.95, ex + er * 0.8, fy + eh * 1.35), fill=CHEEK)
    my = fy + eh + S * 0.1; mw = S * 0.1
    o = max(mouth, {"shock": 0.9, "scared": 0.7, "cheer": 0.6}.get(pose, 0.0))
    if o > 0.1:
        d.ellipse((cx - mw * (0.7 + 0.3 * o), my - mw * 0.2, cx + mw * (0.7 + 0.3 * o), my + mw * (0.3 + 1.1 * o)), fill=(90, 20, 40), outline=LINE, width=4 * SS)
        d.ellipse((cx - mw * 0.45, my + mw * (0.1 + 0.7 * o), cx + mw * 0.45, my + mw * (0.25 + 1.05 * o)), fill=(240, 100, 120))
    elif pose == "sad":
        d.arc((cx - mw, my, cx + mw, my + mw * 1.2), 200, 340, fill=LINE, width=6 * SS)
    elif pose == "think":
        d.line((cx - mw * 0.6, my + mw * 0.3, cx + mw * 0.7, my + mw * 0.1), fill=LINE, width=6 * SS)
    else:
        d.chord((cx - mw, my - mw * 0.6, cx + mw, my + mw * 0.7), 10, 170, fill=(90, 20, 40), outline=LINE, width=4 * SS)
    if facing < 0: im = im.transpose(Image.FLIP_LEFT_RIGHT)
    im = im.resize((Wd // SS, Hd // SS), Image.LANCZOS)
    if alpha < 1: im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    frame.paste(im, (int(x - im.width / 2), int(y - im.height * 0.86)), im)
