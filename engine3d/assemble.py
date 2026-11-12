"""Join rendered 3D shots (crossfades), upscale to 1080x1920, captions + audio -> mp4."""
import glob, json, os, subprocess, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engine"))
import render
d, out = sys.argv[1], sys.argv[2]
T = json.load(open(os.path.join(d, "timing.json"))); fps = T["fps"]; XF = 6
seq = []
for i, s in enumerate(T["shots"]):
    fr = sorted(glob.glob(os.path.join(d, f"s{i}", "f_*.jpg")))
    seq.append((s, fr))
ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920", "-r", str(fps),
    "-i", "-", "-i", os.path.join(d, "audio.wav"), "-c:v", "libx264", "-crf", "17", "-preset", "slow", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
load = lambda p: Image.open(p).convert("RGB").resize((1080, 1920), Image.LANCZOS)
gi = 0
for si, (s, frames) in enumerate(seq):
    groups = render.build_groups([tuple(w) for w in s["words"]])
    for k, p in enumerate(frames):
        im = load(p)
        if si + 1 < len(seq) and k >= len(frames) - XF and seq[si + 1][1]:  # crossfade into next shot
            a = (k - (len(frames) - XF) + 1) / (XF + 1); im = Image.blend(im, load(seq[si + 1][1][0]), a)
        t = gi / fps
        if s["env"] == "space":
            ImageDraw.Draw(im).text((1040, 1860), "ocean bulge exaggerated", font=render.font(render.FONT_SANS, 30), fill=(170, 180, 210), anchor="rm")
        for g in groups:
            if g[0][1] <= t < g[-1][2] + 0.15: render.draw_caption(im, g, t, "whatif", None, 0.80); break
        ff.stdin.write(im.tobytes()); gi += 1
ff.stdin.close(); ff.wait(); print("OK", out, gi, "frames")
