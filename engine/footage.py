"""Real-footage layer for the cartoon/cinematic engine: play a video clip inside a scene.

clip = Clip("assets/footage/x.webm", start=3.0)       # start = offset (s) into the source video
clip.draw(c, t_local, x, y, w, h, zoom=1.0, focus=(0.5, 0.5), radius=36, border=True)
clip.draw_fill(c, t_local)                           # 'blurred fill' backdrop: zoomed + blurred copy filling the screen
Frames are decoded sequentially through an ffmpeg pipe (re-seeks only when time jumps), so it stays memory-light.
"""
import math, os, subprocess
import numpy as np
import cairo
from PIL import Image, ImageFilter

W, H = 1080, 1920

class Clip:
    def __init__(self, path, start=0.0, fps=30, size=(1280, 720)):
        self.path, self.start, self.fps = path, start, fps
        self.w, self.h = size; self.proc = None; self.idx = -10; self.frame = None
        self._blur_cache = (None, None)

    def _open(self, t):
        if self.proc: self.proc.kill()
        self.proc = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-ss", f"{self.start + t:.3f}", "-i", self.path,
                                      "-vf", f"scale={self.w}:{self.h},fps={self.fps}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                                     stdout=subprocess.PIPE)
        self.idx = int(round(t * self.fps)) - 1

    def get(self, t):
        want = int(round(max(0.0, t) * self.fps))
        if want == self.idx and self.frame is not None: return self.frame
        if self.proc is None or want < self.idx or want > self.idx + 5: self._open(want / self.fps)
        while self.idx < want:
            buf = self.proc.stdout.read(self.w * self.h * 3)
            if len(buf) < self.w * self.h * 3:            # past the end: hold the last frame
                return self.frame if self.frame is not None else np.zeros((self.h, self.w, 3), np.uint8)
            self.frame = np.frombuffer(buf, np.uint8).reshape(self.h, self.w, 3); self.idx += 1
        return self.frame

    @staticmethod
    def _surface(rgb):
        h, w, _ = rgb.shape
        bgra = np.dstack([rgb[..., ::-1], np.full((h, w), 255, np.uint8)])
        return cairo.ImageSurface.create_for_data(bytearray(np.ascontiguousarray(bgra).tobytes()), cairo.FORMAT_RGB24, w, h)

    def draw(self, c, t, x, y, w, h, zoom=1.0, focus=(0.5, 0.5), radius=36, border=True, alpha=1.0):
        """draw the clip into the box (x, y, w, h), cropped to fill it; zoom > 1 punches in around focus (0..1 coords)"""
        f = self.get(t); fh, fw, _ = f.shape
        s = max(w / fw, h / fh) * zoom
        cx, cy = focus[0] * fw, focus[1] * fh
        ox = x + w / 2 - cx * s; oy = y + h / 2 - cy * s
        ox = min(x, max(x + w - fw * s, ox)); oy = min(y, max(y + h - fh * s, oy))   # keep the box covered
        c.save(); c.new_path(); _rrect(c, x, y, w, h, radius); c.clip()
        c.translate(ox, oy); c.scale(s, s); c.set_source_surface(self._surface(f)); c.get_source().set_filter(cairo.FILTER_GOOD)
        c.paint_with_alpha(alpha); c.restore()
        if border:
            c.new_path(); _rrect(c, x, y, w, h, radius); c.set_source_rgba(1, 1, 1, 0.9 * alpha); c.set_line_width(6); c.stroke()

    def draw_fill(self, c, t, darken=0.45, blur=24):
        """full-screen blurred, darkened copy of the clip (common Shorts backdrop for 16:9 footage)"""
        f = self.get(t)
        key = (self.idx // 2)
        if self._blur_cache[0] != key:
            im = Image.fromarray(f).resize((W // 6, int(W // 6 * 16 / 9)), Image.BILINEAR, box=_center_box(f.shape[1], f.shape[0], 9 / 16))
            im = im.filter(ImageFilter.GaussianBlur(blur / 6)).resize((W, H), Image.BILINEAR)
            a = (np.asarray(im).astype(np.float32) * (1 - darken)).astype(np.uint8)
            self._blur_cache = (key, a)
        c.save(); c.identity_matrix(); c.set_source_surface(self._surface(self._blur_cache[1])); c.paint(); c.restore()

def _center_box(fw, fh, aspect):
    w = fh * aspect
    return ((fw - w) / 2, 0, (fw + w) / 2, fh)

def _rrect(c, x, y, w, h, r):
    c.new_sub_path(); c.arc(x + w - r, y + r, r, -math.pi / 2, 0); c.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    c.arc(x + r, y + h - r, r, math.pi / 2, math.pi); c.arc(x + r, y + r, r, math.pi, 1.5 * math.pi); c.close_path()
