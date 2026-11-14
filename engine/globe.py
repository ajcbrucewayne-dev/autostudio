"""Realistic globe renderer (orthographic projection of NASA Blue Marble, public domain) for map-style shots.

render_globe(lon, lat, radius_px, cx, cy, sun=(…)) -> RGBA uint8 (H, W, 4) layer, fast numpy sampling.
lonlat_to_screen(lon, lat, lon0, lat0, radius_px, cx, cy) -> (x, y, visible) for pinning labels.
"""
import math, os
import numpy as np
from PIL import Image

W, H = 1080, 1920
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TEX = None
def tex():
    global _TEX
    if _TEX is None:
        _TEX = np.asarray(Image.open(os.path.join(ROOT, "assets", "earth_bluemarble_3840.jpg")).convert("RGB")).astype(np.float32) / 255
    return _TEX

def _rot(lon0, lat0):
    lo, la = math.radians(lon0), math.radians(lat0)
    # rotate so that (lon0, lat0) faces the viewer (+z)
    Ry = np.array([[math.cos(lo), 0, -math.sin(lo)], [0, 1, 0], [math.sin(lo), 0, math.cos(lo)]])
    Rx = np.array([[1, 0, 0], [0, math.cos(la), -math.sin(la)], [0, math.sin(la), math.cos(la)]])
    return Rx @ Ry

def render_globe(lon0, lat0, R, cx=W / 2, cy=H / 2, sun=(-0.5, 0.45, 0.75), atmo=True, night=0.18, tint=None):
    t = tex(); th, tw, _ = t.shape
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    nx = (xx - cx) / R; ny = -(yy - cy) / R; d2 = nx * nx + ny * ny
    inside = d2 <= 1.0
    out = np.zeros((H, W, 4), np.float32)
    if inside.any():
        nz = np.sqrt(np.clip(1 - d2, 0, 1))
        v = np.stack([nx[inside], ny[inside], nz[inside]], 1)              # view-space normal
        M = _rot(lon0, lat0).T                                             # view -> world
        w = v @ M.T
        lat = np.degrees(np.arcsin(np.clip(w[:, 1], -1, 1))); lon = np.degrees(np.arctan2(w[:, 0], w[:, 2]))
        u = ((lon + 180) / 360 * tw).astype(int) % tw; vv = np.clip(((90 - lat) / 180 * th).astype(int), 0, th - 1)
        col = t[vv, u]
        s = np.array(sun, np.float32); s /= np.linalg.norm(s)
        lam = np.clip(v @ s, 0, 1); light = night + (1 - night) * (0.25 + 0.75 * lam)
        col = col * light[:, None]
        rim = (1 - v[:, 2]) ** 3
        col = col * (1 - 0.35 * rim[:, None]) + np.array([0.35, 0.6, 1.0]) * 0.55 * rim[:, None] * (0.3 + lam[:, None])
        if tint is not None: col = col * (1 - tint[3]) + np.array(tint[:3]) * tint[3]
        out[inside, :3] = col; out[inside, 3] = 1
        edge = np.clip((1 - np.sqrt(d2)) * R / 1.5, 0, 1); out[..., 3] *= np.where(inside, edge, 0)
    if atmo:  # soft atmospheric halo outside the disc
        r = np.sqrt(d2); halo = np.clip(1 - (r - 1) / 0.06, 0, 1) * (r > 1) * 0.85
        a = out[..., 3]; out[..., :3] = out[..., :3] * a[..., None] + np.array([0.45, 0.7, 1.0]) * halo[..., None] * (1 - a[..., None])
        out[..., 3] = np.maximum(a, halo)
    return (np.clip(out, 0, 1) * 255).astype(np.uint8)

def lonlat_to_screen(lon, lat, lon0, lat0, R, cx=W / 2, cy=H / 2):
    la, lo = math.radians(lat), math.radians(lon)
    w = np.array([math.cos(la) * math.sin(lo), math.sin(la), math.cos(la) * math.cos(lo)])
    v = _rot(lon0, lat0) @ w
    return cx + v[0] * R, cy - v[1] * R, v[2] > 0
