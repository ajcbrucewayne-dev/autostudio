"""Edit the hologram storybook: cold open (the Moon shattering, cut from the rendered film), VHS rewind scrub,
then the continuous film. Bloom glow, captions, sound-designed audio -> mp4.
python3 assemble_holo.py out/holo out.mp4
"""
import glob, json, os, re, subprocess, sys
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engine"))
import render

d, out = sys.argv[1], sys.argv[2]
T = json.load(open(os.path.join(d, "timing.json"))); fps = T["fps"]
CU = json.load(open(os.path.join(d, "cues.json"))); OFF = CU["off"]; NF = CU["film_frames"]
film = {int(re.findall(r"f_(\d+)", p)[0]): p for p in glob.glob(os.path.join(d, "s*", "f_*.jpg"))}
assert len(film) >= NF - 2, f"missing frames: {len(film)}/{NF}"
COLD_SRC = CU["cues"].get("cold_src")  # film source for the cold open (else: the Moon shatter)
tv_film = CU["cues"]["shatter"] - 0.15 - OFF if "shatter" in CU["cues"] else None
fidx = lambda ft: min(NF, max(1, int(round(ft * fps)) + 1))

def bloom(im):
    small = im.resize((im.width // 4, im.height // 4), Image.BILINEAR)
    g1 = small.point(lambda v: max(0, v - 110) * 2).filter(ImageFilter.GaussianBlur(5))
    g2 = small.point(lambda v: max(0, v - 140)).filter(ImageFilter.GaussianBlur(18))
    return ImageChops.add(ImageChops.add(im, g1.resize(im.size, Image.BILINEAR)), g2.resize(im.size, Image.BILINEAR))

cache = {}
def load(i):
    if i not in cache:
        if len(cache) > 8: cache.clear()
        cache[i] = bloom(Image.open(film[i]).convert("RGB")).resize((1080, 1920), Image.LANCZOS)
    return cache[i].copy()

def vhs(im, k, strength):
    r, g, b = im.split(); s = int(10 + 18 * strength)
    im = Image.merge("RGB", (ImageChops.offset(r, s, 0), g, ImageChops.offset(b, -s, 0)))
    a = np.asarray(im).copy(); rng = np.random.default_rng(k)
    for _ in range(5):  # tearing bands
        y = rng.integers(0, 1900); h = rng.integers(8, 60); a[y:y + h] = np.roll(a[y:y + h], rng.integers(-80, 80), axis=1)
    a[::4] = (a[::4] * 0.75).astype(np.uint8)  # scanlines
    a = np.clip(a.astype(np.int16) + rng.integers(-18, 18, a.shape[:2])[..., None], 0, 255).astype(np.uint8)
    im = Image.fromarray(a); dr = ImageDraw.Draw(im)
    for x0 in (70, 120):  # rewind icon
        dr.polygon([(x0 + 50, 110), (x0, 140), (x0 + 50, 170)], fill=(255, 255, 255))
    dr.text((190, 140), "REWIND", font=render.font(render.FONT_SANS, 54), fill=(255, 255, 255), anchor="lm")
    return im

audio = os.path.join(d, "audio_fx.wav") if os.path.exists(os.path.join(d, "audio_fx.wav")) else os.path.join(d, "audio.wav")
ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920", "-r", str(fps),
    "-i", "-", "-i", audio, "-c:v", "libx264", "-crf", "17", "-preset", "slow", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)

sh = {s["beat"]: s for s in T["shots"]}
if COLD_SRC is not None:
    tw = sh["cold"]["t0"]; tv_film = COLD_SRC - OFF
else:
    tw = next(w[1] for w in sh["cold"]["words"] if w[0].lower().startswith("vanish"))
cold_end_film = tv_film + (sh["cold"]["t0"] + sh["cold"]["frames"] / fps - tw)
pre = sh["cold"]["frames"] + sh["rewind"]["frames"]
gi = 0
for s in T["shots"]:
    groups = render.build_groups([tuple(w) for w in s["words"]])
    for k in range(s["frames"]):
        t = gi / fps
        if s["beat"] == "cold":
            im = load(fidx(tv_film + (t - tw)))
            if k < 3: im = Image.blend(im, Image.new("RGB", im.size, (255, 255, 255)), 0.6 - 0.2 * k)  # flash-in
        elif s["beat"] == "rewind":
            u = k / max(1, s["frames"] - 1); ft = cold_end_film * (1 - u) ** 1.4
            im = vhs(load(fidx(ft)), k, 1 - u)
        else:
            im = load(min(NF, gi - pre + 1))
        for g in groups:
            if g[0][1] <= t < g[-1][2] + 0.15: render.draw_caption(im, g, t, "whatif", None, 0.80); break
        ff.stdin.write(im.tobytes()); gi += 1
ff.stdin.close(); ff.wait(); print("OK", out, gi, "frames")
