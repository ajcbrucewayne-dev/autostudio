"""Step 3: upscale rendered frames to 1080x1920, burn captions, add audio -> mp4."""
import glob, json, os, subprocess, sys
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engine"))
import render
d, out = sys.argv[1], sys.argv[2]
T = json.load(open(os.path.join(d, "timing.json"))); fps = T["fps"]
frames = sorted(glob.glob(os.path.join(d, "frames", "f_*.jpg")))
groups = [g for s in T["segs"] for g in render.build_groups([tuple(w) for w in s["words"]])]
ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920", "-r", str(fps),
    "-i", "-", "-i", os.path.join(d, "audio.wav"), "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
    "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
for i, f in enumerate(frames):
    t = i / fps; fr = Image.open(f).convert("RGB").resize((1080, 1920), Image.LANCZOS)
    for g in groups:
        if g[0][1] <= t < g[-1][2] + 0.15: render.draw_caption(fr, g, t, "skits"); break
    ff.stdin.write(fr.tobytes())
ff.stdin.close(); ff.wait(); print("OK", out)
