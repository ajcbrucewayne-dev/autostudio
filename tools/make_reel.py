"""Portfolio reel for the Fiverr gig: 16:9 frame, vertical samples on the right, style labels on the left, synth music bed."""
import os, subprocess, sys
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw
sys.path.insert(0, "/home/user/autostudio/engine"); import render
FPS, W, H = 30, 1920, 1080; OUT = sys.argv[1]
BG = (10, 16, 30); MINT = (46, 214, 160); YEL = (255, 204, 0); WHITE = (255, 255, 255); MUTED = (150, 160, 190)
F = lambda s: render.font(render.FONT_SANS, s)
def clip(path, a, b):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(a), "-t", str(b - a), "-i", path, "-vf", f"fps={FPS},scale=608:1080",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    n = len(raw) // (608 * 1080 * 3); return [Image.frombytes("RGB", (608, 1080), raw[i * 608 * 1080 * 3:(i + 1) * 608 * 1080 * 3]) for i in range(n)]
H_ = "/home/user/"
SECTIONS = [
 ("3D CINEMATIC", "Cinematic hologram storytelling", ["Story-driven science & product videos", "Custom 3D character", "Sound design included"], MINT,
  [(H_ + "moon_hologram_storybook_v2.mp4", a, b) for a, b in ((0.4, 3.0), (13.0, 16.0), (21.0, 24.0), (29.0, 31.6), (34.6, 37.2))]),
 ("BUSINESS EXPLAINERS", "Clean 2D motion graphics", ["Charts, counters, icons", "Your logo & brand colors", "Ads, Reels, Shorts, websites"], YEL,
  [(H_ + "autostudio/out/demo/biz_compound.mp4", a, b) for a, b in ((1.5, 4.8), (12.0, 15.0), (20.5, 24.0), (26.0, 29.0))]),
 ("EDUCATIONAL SHORTS", "Fast, punchy facts that keep viewers watching", ["Word-synced captions", "Natural AI voiceover", "Vertical 9:16 or 16:9"], (90, 170, 255),
  [(H_ + "option2_full_motion_graphics.mp4", a, b) for a, b in ((1.0, 5.0), (12.0, 16.0))] + [(H_ + "option1_leo_plus_motion_graphics.mp4", 6.0, 10.0)]),
]
WAV = "/tmp/claude-0/-home-user/de5d2c9b-5dce-5617-85be-ac39cb5a91b2/scratchpad/reel.wav"
dur = 4 + 5 + sum(b - a for *_, clips in SECTIONS for _, a, b in clips)
mus = render.synth_music("whatif", int((dur + 0.5) * render.SR)); mus = mus / np.abs(mus).max() * 0.6
fd = int(1.5 * render.SR); mus[-fd:] *= np.linspace(1, 0, fd); sf.write(WAV, mus.astype(np.float32), render.SR)
ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                       "-i", WAV, "-c:v", "libx264", "-crf", "20", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
class _Sink:
    n = 0
    def append(self, im): ff.stdin.write(im.tobytes()); self.n += 1
frames = _Sink()
def card(lines, n):
    for i in range(n):
        im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im); k = min(1, i / 12)
        for j, (s, sz, col) in enumerate(lines):
            c = tuple(int(BG[q] + (col[q] - BG[q]) * k) for q in range(3)); d.text((W / 2, H * (0.36 + j * 0.13)), s, font=F(sz), fill=c, anchor="mm")
        frames.append(im)
card([("ANIMATED EXPLAINER VIDEOS", 92, WHITE), ("3D  •  2D  •  CHARACTERS  •  VOICEOVER", 50, MINT), ("script → voice → animation → sound, done for you", 36, MUTED)], 4 * FPS)
for title, sub, bullets, col, clips in SECTIONS:
    def _gen():
        for c in clips: yield from clip(*c)
    for i, f in enumerate(_gen()):
        im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im); k = min(1, i / 10)
        im.paste(f, (W - 608 - 160, 0)); d.rectangle((W - 608 - 164, 0, W - 608 - 160, H), fill=col)
        x = 140; d.text((x, 300), title, font=F(78), fill=col, anchor="lm"); d.text((x, 385), sub, font=F(38), fill=WHITE, anchor="lm")
        for j, b in enumerate(bullets):
            if i > 12 + j * 10: d.ellipse((x, 488 + j * 80, x + 18, 506 + j * 80), fill=col); d.text((x + 40, 497 + j * 80), b, font=F(36), fill=MUTED, anchor="lm")
        frames.append(im)
card([("FROM $50  •  FAST DELIVERY", 80, WHITE), ("Commercial use included", 46, MINT), ("Message me with your idea to get started", 40, MUTED)], 5 * FPS)
ff.stdin.close(); ff.wait(); print("OK", OUT, round(frames.n / FPS, 1), "s")
