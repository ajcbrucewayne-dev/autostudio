"""Leo: an original curious-kid character (flat 2D), drawn procedurally with poses.

draw_kid(frame, x, y_feet, height_px, pose, t, look=None, facing=1)
Poses: idle, telescope, wonder, look_up, shock, point, sad, run, cheer, relieved, wave
"""
import math
from PIL import Image, ImageDraw

SS = 2
SKIN = (233, 176, 132); SKIN_DK = (196, 132, 92); HAIR = (52, 32, 24); HAIR_LT = (90, 58, 40)
HOOD = (255, 190, 50); HOOD_DK = (214, 140, 20); SHORTS = (52, 98, 200); SHOE = (230, 60, 60); LINE = (40, 26, 20)
IRIS = (92, 54, 24)

# (L shoulder, L bend, R shoulder, R bend) degrees from straight down (positive = outward), head tilt, look(x,y)
POSES = {
    "idle": ((12, 10, 12, 10), 0, (0, 0)),
    "telescope": ((20, 30, 118, 22), -6, (0.8, -0.6)),
    "wonder": ((14, 8, 60, 150), -6, (0.4, -0.9)),
    "look_up": ((16, 12, 16, 12), -12, (0.2, -1.0)),
    "shock": ((100, 120, 100, 120), 0, (0, 0)),
    "point": ((14, 10, 115, 0), -4, (0.8, -0.5)),
    "sad": ((5, 0, 5, 0), 6, (0, 0.7)),
    "run": ((30, 70, 30, 70), 4, (1, 0)),
    "cheer": ((160, 15, 160, 15), -4, (0, -0.3)),
    "relieved": ((12, 10, 35, 125), -10, (0.2, -0.8)),
    "wave": ((14, 10, 150, 25), 0, (0, 0)),
}

def _limb(d, p0, a1, l1, a2, l2, side, color, width, outline=LINE):
    r1, r2 = math.radians(a1), math.radians(a1 + a2)
    p1 = (p0[0] + side * math.sin(r1) * l1, p0[1] + math.cos(r1) * l1)
    p2 = (p1[0] + side * math.sin(r2) * l2, p1[1] + math.cos(r2) * l2)
    d.line((p0, p1, p2), fill=outline, width=int(width + 5 * SS), joint="curve")
    d.line((p0, p1, p2), fill=color, width=int(width), joint="curve")
    return p2

def _star(d, cx, cy, r, fill):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5; rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=fill)

def _head(U, pose, t, look, blink):
    hw, hh = int(64 * U), int(70 * U)
    im = Image.new("RGBA", (hw, hh), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cx, cy = hw / 2, hh * 0.56
    rx, ry = 22 * U, 24 * U
    # back hair
    d.ellipse((cx - rx - 2 * U, cy - ry - 3 * U, cx + rx + 2 * U, cy + ry * 0.4), fill=HAIR)
    # ears
    for s in (-1, 1):
        d.ellipse((cx + s * rx - 4 * U, cy - 2 * U, cx + s * rx + 4 * U, cy + 8 * U), fill=SKIN, outline=LINE, width=int(2 * U))
    d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=SKIN, outline=LINE, width=int(2.2 * U))
    # curly fringe
    for i in range(11):
        a = math.radians(195 + i * 15)
        hx, hy = cx + math.cos(a) * rx * 0.95, cy + math.sin(a) * ry * 0.92
        r = 7.5 * U if i % 2 else 8.5 * U
        d.ellipse((hx - r, hy - r, hx + r, hy + r), fill=HAIR)
    for i in range(5):
        hx, hy = cx - 12 * U + i * 6 * U, cy - ry * 0.78 + (2 * U if i % 2 else 0)
        d.ellipse((hx - 6 * U, hy - 5 * U, hx + 6 * U, hy + 5 * U), fill=HAIR)
    d.arc((cx - 8 * U, cy - ry - 4 * U, cx + 2 * U, cy - ry + 6 * U), 200, 320, fill=HAIR_LT, width=int(2 * U))
    # eyes
    wide = pose in ("shock",); ey = cy + 2 * U; lx, ly = look
    for s in (-1, 1):
        ex = cx + s * 8.5 * U
        erx, ery = 5.2 * U, (7.2 if wide else 6.2) * U
        if blink and not wide:
            d.arc((ex - erx, ey - 2 * U, ex + erx, ey + 3 * U), 200, 340, fill=LINE, width=int(1.8 * U))
        else:
            d.ellipse((ex - erx, ey - ery, ex + erx, ey + ery), fill="white", outline=LINE, width=int(1.6 * U))
            ir = (3.2 if wide else 3.9) * U
            px, py = ex + lx * 1.6 * U, ey + ly * 2.2 * U
            d.ellipse((px - ir, py - ir, px + ir, py + ir), fill=IRIS)
            pr = ir * 0.55; d.ellipse((px - pr, py - pr, px + pr, py + pr), fill=(15, 10, 8))
            hr = ir * 0.38; d.ellipse((px - ir * 0.4 - hr, py - ir * 0.45 - hr, px - ir * 0.4 + hr, py - ir * 0.45 + hr), fill="white")
            hr = ir * 0.18; d.ellipse((px + ir * 0.4 - hr, py + ir * 0.35 - hr, px + ir * 0.4 + hr, py + ir * 0.35 + hr), fill="white")
        # brows
        by = ey - 9.5 * U
        lift = {"shock": -2.5, "look_up": -1.5, "wonder": -1.5 if s > 0 else 0.5, "telescope": -1, "sad": 0}.get(pose, 0) * U
        inner = {"sad": -2.0, "shock": -1.0, "wonder": 1.0 if s < 0 else -1.0}.get(pose, 0) * U
        x_in, x_out = ex - s * 4.5 * U, ex + s * 4.5 * U
        d.line((x_in, by + lift + inner, x_out, by + lift + (1.5 * U if pose == "sad" else 0)), fill=HAIR, width=int(2.4 * U))
        d.ellipse((ex - 4.5 * U, ey + 6.5 * U, ex + 4.5 * U, ey + 9.5 * U), fill=(240, 140, 130))
    # nose
    d.arc((cx - 2.2 * U, cy + 5 * U, cx + 2.2 * U, cy + 9 * U), 20, 160, fill=SKIN_DK, width=int(1.6 * U))
    # mouth
    my = cy + 13 * U
    if pose in ("shock",):
        d.ellipse((cx - 3.5 * U, my - 2 * U, cx + 3.5 * U, my + 6 * U), fill=(110, 30, 40), outline=LINE, width=int(1.4 * U))
    elif pose in ("look_up", "telescope"):
        d.ellipse((cx - 2.2 * U, my - 1 * U, cx + 2.2 * U, my + 3 * U), fill=(110, 30, 40), outline=LINE, width=int(1.2 * U))
    elif pose in ("cheer", "run", "point", "wave"):
        d.chord((cx - 6 * U, my - 3 * U, cx + 6 * U, my + 6 * U), 0, 180, fill=(110, 30, 40), outline=LINE, width=int(1.4 * U))
        d.chord((cx - 3.5 * U, my + 1.5 * U, cx + 3.5 * U, my + 5.5 * U), 180, 360, fill=(240, 110, 120))
    elif pose == "sad":
        d.arc((cx - 5 * U, my + 1 * U, cx + 5 * U, my + 7 * U), 200, 340, fill=LINE, width=int(1.6 * U))
    elif pose == "wonder":
        d.line((cx - 3 * U, my + 2 * U, cx + 3.5 * U, my + 1 * U), fill=LINE, width=int(1.6 * U))
    else:
        d.arc((cx - 5.5 * U, my - 3 * U, cx + 5.5 * U, my + 3.5 * U), 20, 160, fill=LINE, width=int(1.8 * U))
    return im

def draw_kid(frame, x, y, height, pose="idle", t=0.0, look=None, facing=1, alpha=1.0):
    U = height * SS / 100.0
    cw, ch = int(130 * U), int(135 * U)
    im = Image.new("RGBA", (cw, ch), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    (la, lb, ra, rb), tilt, lk = POSES.get(pose, POSES["idle"])
    look = look or lk
    cx = cw / 2; foot = ch - 6 * U
    bob = (abs(math.sin(t * 8)) * 6 * U if pose in ("cheer", "run") else math.sin(t * 2.2) * 0.6 * U)
    oy = -bob
    d.ellipse((cx - 20 * U, foot - 3 * U, cx + 20 * U, foot + 3 * U), fill=(0, 0, 0, 60))
    hip = foot - 30 * U + oy; sh_y = hip - 33 * U
    # legs
    for s in (-1, 1):
        if pose == "run":
            a = 35 * math.sin(t * 12 + (0 if s > 0 else math.pi))
            p0 = (cx + s * 6 * U, hip); r = math.radians(a)
            fx, fy = p0[0] + math.sin(r) * 26 * U, p0[1] + math.cos(r) * 26 * U
            pts = (p0, (fx, fy))
        else:
            pts = ((cx + s * 6 * U, hip), (cx + s * 7 * U, foot - 4 * U + oy))
            fx, fy = pts[-1]
        d.line(pts, fill=LINE, width=int(9 * U), joint="curve"); d.line(pts, fill=SKIN, width=int(6.5 * U), joint="curve")
        d.rounded_rectangle((fx - 7 * U + s * 2 * U, fy - 4 * U, fx + 7 * U + s * 2 * U, fy + 3.5 * U), 3 * U, fill=SHOE, outline=LINE, width=int(1.6 * U))
        d.rectangle((fx - 6.5 * U + s * 2 * U, fy + 1.2 * U, fx + 6.5 * U + s * 2 * U, fy + 2.5 * U), fill="white")
    # shorts
    d.rounded_rectangle((cx - 15 * U, hip - 7 * U, cx + 15 * U, hip + 9 * U), 4 * U, fill=SHORTS, outline=LINE, width=int(1.8 * U))
    d.line((cx, hip, cx, hip + 9 * U), fill=LINE, width=int(1.4 * U))
    if pose == "telescope":
        mx, my = cx + 34 * U, sh_y - 34 * U
        for k in (-1, 0, 1):
            d.line((mx, my, mx + k * 12 * U, foot), fill=(70, 70, 80), width=int(2 * U))
    # torso (hoodie)
    body = [(cx - 15 * U, sh_y + 1 * U), (cx + 15 * U, sh_y + 1 * U), (cx + 16 * U, hip - 2 * U), (cx - 16 * U, hip - 2 * U)]
    d.polygon(body, fill=HOOD, outline=LINE, width=int(2 * U))
    d.rounded_rectangle((cx - 15.5 * U, hip - 6 * U, cx + 15.5 * U, hip), 2 * U, fill=HOOD_DK)
    d.arc((cx - 9 * U, hip - 17 * U, cx + 9 * U, hip - 3 * U), 0, 180, fill=HOOD_DK, width=int(1.6 * U))
    _star(d, cx, sh_y + 12 * U, 4.5 * U, (255, 255, 255))
    d.line((cx - 3 * U, sh_y + 1 * U, cx - 4 * U, sh_y + 8 * U), fill=LINE, width=int(1 * U))
    d.line((cx + 3 * U, sh_y + 1 * U, cx + 4 * U, sh_y + 8 * U), fill=LINE, width=int(1 * U))
    # arms
    for s, (a, b) in ((-1, (la, lb)), (1, (ra, rb))):
        if pose == "run":
            a = 30 + 35 * math.sin(t * 12 + (math.pi if s > 0 else 0)); b = 70
        if pose == "wave" and s > 0: b = 25 + 25 * math.sin(t * 10)
        if pose == "cheer": a += 8 * math.sin(t * 10)
        hand = _limb(d, (cx + s * 14 * U, sh_y + 4 * U), a, 16 * U, b, 15 * U, s, HOOD, 7 * U)
        d.ellipse((hand[0] - 4 * U, hand[1] - 4 * U, hand[0] + 4 * U, hand[1] + 4 * U), fill=SKIN, outline=LINE, width=int(1.4 * U))
    # neck + head
    d.rectangle((cx - 4 * U, sh_y - 5 * U, cx + 4 * U, sh_y + 2 * U), fill=SKIN)
    blink = (t % 3.3) < 0.12
    head = _head(U, pose, t, look, blink)
    if tilt: head = head.rotate(-tilt * 1.0, resample=Image.BICUBIC, center=(head.width / 2, head.height * 0.9))
    im.alpha_composite(head, (int(cx - head.width / 2), int(sh_y - head.height * 0.93)))
    if pose == "telescope":
        ex_, ey_ = cx + 13 * U, sh_y - 24 * U; tx, ty = cx + 52 * U, sh_y - 50 * U
        d.line((ex_, ey_, tx, ty), fill=LINE, width=int(9 * U)); d.line((ex_, ey_, tx, ty), fill=(90, 110, 200), width=int(6.5 * U))
        d.ellipse((tx - 5 * U, ty - 5 * U, tx + 5 * U, ty + 5 * U), fill=(200, 230, 255), outline=LINE, width=int(1.4 * U))
        d.ellipse((ex_ - 3 * U, ey_ - 3 * U, ex_ + 3 * U, ey_ + 3 * U), fill=(40, 40, 50))
    # re-draw hands for poses that touch the face (in front of head)
    if pose in ("shock", "wonder", "relieved", "telescope"):
        for s, (a, b) in ((-1, (la, lb)), (1, (ra, rb))):
            if pose != "shock" and s < 0: continue
            hand = _limb(d, (cx + s * 14 * U, sh_y + 4 * U), a, 16 * U, b, 15 * U, s, HOOD, 7 * U)
            d.ellipse((hand[0] - 4 * U, hand[1] - 4 * U, hand[0] + 4 * U, hand[1] + 4 * U), fill=SKIN, outline=LINE, width=int(1.4 * U))
    if facing < 0: im = im.transpose(Image.FLIP_LEFT_RIGHT)
    im = im.resize((cw // SS, ch // SS), Image.LANCZOS)
    if alpha < 1: im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    frame.paste(im, (int(x - im.width / 2), int(y - im.height + 6 * U / SS)), im)
