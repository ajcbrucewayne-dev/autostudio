"""Realistic globe renderer (orthographic projection of NASA Blue Marble, public domain) for map-style shots.

render_globe(lon, lat, radius_px, cx, cy, sun=(…)) -> RGBA uint8 (H, W, 4) layer, fast numpy sampling.
lonlat_to_screen(lon, lat, lon0, lat0, radius_px, cx, cy) -> (x, y, visible) for pinning labels.
"""
import math, os
import numpy as np
from PIL import Image

W, H = 1080, 1920
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TEX = {}
TEXTURES = {"earth": "earth_bluemarble_3840.jpg", "mars": "mars/Mars_Viking_MDIM21_ClrMosaic_1km.jpg"}
def tex(name="earth"):
    if name not in _TEX:
        t = np.asarray(Image.open(os.path.join(ROOT, "assets", TEXTURES[name])).convert("RGB")).astype(np.float32) / 255
        t = t.copy(); t[:, :2] = t[:, 2:3]; t[:, -2:] = t[:, -3:-2]          # hide the seam at the 180° meridian
        _TEX[name] = t
    return _TEX[name]

def _rot(lon0, lat0):
    lo, la = math.radians(lon0), math.radians(lat0)
    # rotate so that (lon0, lat0) faces the viewer (+z)
    Ry = np.array([[math.cos(lo), 0, -math.sin(lo)], [0, 1, 0], [math.sin(lo), 0, math.cos(lo)]])
    Rx = np.array([[1, 0, 0], [0, math.cos(la), -math.sin(la)], [0, math.sin(la), math.cos(la)]])
    return Rx @ Ry

def render_globe(lon0, lat0, R, cx=W / 2, cy=H / 2, sun=(-0.5, 0.45, 0.75), atmo=True, night=0.18, tint=None, planet="earth"):
    t = tex(planet); th, tw, _ = t.shape
    atmo_col = np.array([1.0, 0.6, 0.4]) if planet == "mars" else np.array([0.45, 0.7, 1.0])
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
        col = col * (1 - 0.35 * rim[:, None]) + atmo_col * 0.45 * rim[:, None] * (0.3 + lam[:, None])
        if tint is not None: col = col * (1 - tint[3]) + np.array(tint[:3]) * tint[3]
        out[inside, :3] = col; out[inside, 3] = 1
        edge = np.clip((1 - np.sqrt(d2)) * R / 1.5, 0, 1); out[..., 3] *= np.where(inside, edge, 0)
    if atmo:  # soft atmospheric halo outside the disc
        r = np.sqrt(d2); halo = np.clip(1 - (r - 1) / 0.06, 0, 1) * (r > 1) * 0.85
        a = out[..., 3]; out[..., :3] = out[..., :3] * a[..., None] + atmo_col * halo[..., None] * (1 - a[..., None])
        out[..., 3] = np.maximum(a, halo)
    return (np.clip(out, 0, 1) * 255).astype(np.uint8)

def lonlat_to_screen(lon, lat, lon0, lat0, R, cx=W / 2, cy=H / 2):
    la, lo = math.radians(lat), math.radians(lon)
    w = np.array([math.cos(la) * math.sin(lo), math.sin(la), math.cos(la) * math.cos(lo)])
    v = _rot(lon0, lat0) @ w
    return cx + v[0] * R, cy - v[1] * R, v[2] > 0

# ------------------------------------------------------------------ vector overlays (Natural Earth borders, public domain)
import json as _json
_GEO = {}
def _features(src):
    if src not in _GEO:
        _GEO[src] = _json.load(open(os.path.join(ROOT, "assets", "geo", src + ".geojson")))["features"]
    return _GEO[src]

def rings(name, src="ne_50m_admin_0_countries", key=("NAME", "ADMIN", "name")):
    """outer rings [(lon, lat) array, ...] of the feature whose name matches"""
    out = []
    for f in _features(src):
        p = f["properties"]
        if any(p.get(k) == name for k in key):
            g = f["geometry"]; polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
            out += [np.array(poly[0], np.float32) for poly in polys]
    return out

def project(lon, lat, lon0, lat0, R, cx=W / 2, cy=H / 2):
    """vectorised lonlat_to_screen: arrays in, (x, y, visible) arrays out"""
    la, lo = np.radians(lat), np.radians(lon)
    w = np.stack([np.cos(la) * np.sin(lo), np.sin(la), np.cos(la) * np.cos(lo)])
    v = _rot(lon0, lat0) @ w
    return cx + v[0] * R, cy - v[1] * R, v[2] > 0

def region_path(c, ring_list, lon0, lat0, R, cx=W / 2, cy=H / 2, min_pts=4):
    """add projected rings to the cairo path (rings partly on the far side are skipped)"""
    c.new_path(); n = 0
    for r in ring_list:
        x, y, vis = project(r[:, 0], r[:, 1], lon0, lat0, R, cx, cy)
        if vis.mean() < 0.98 or len(x) < min_pts: continue
        c.move_to(x[0], y[0])
        for a, b in zip(x[1:], y[1:]): c.line_to(a, b)
        c.close_path(); n += 1
    return n

def fill_region(c, ring_list, lon0, lat0, R, col, alpha=0.75, cx=W / 2, cy=H / 2, edge=(1, 1, 1), glow_w=18):
    """GeoGlobeTales-style flat colour fill with a soft glowing edge"""
    if alpha <= 0.01 or not region_path(c, ring_list, lon0, lat0, R, cx, cy): return
    c.set_source_rgba(*col, alpha); c.fill_preserve()
    c.set_source_rgba(*col, 0.35 * alpha); c.set_line_width(glow_w); c.set_line_join(1); c.stroke_preserve()
    c.set_source_rgba(*edge, 0.9 * alpha); c.set_line_width(3); c.stroke()

def meridian_band(c, lon_a, lon_b, lat_a, lat_b, lon0, lat0, R, cx=W / 2, cy=H / 2, steps=24):
    """path for a lon/lat box (used for time-zone bands, clipped by a country path)"""
    lats = np.linspace(lat_a, lat_b, steps); lons = np.linspace(lon_a, lon_b, steps)
    lon = np.concatenate([np.full(steps, lon_a), lons, np.full(steps, lon_b), lons[::-1]])
    lat = np.concatenate([lats, np.full(steps, lat_b), lats[::-1], np.full(steps, lat_a)])
    x, y, _ = project(lon, lat, lon0, lat0, R, cx, cy)
    c.new_path(); c.move_to(x[0], y[0])
    for a, b in zip(x[1:], y[1:]): c.line_to(a, b)
    c.close_path()
