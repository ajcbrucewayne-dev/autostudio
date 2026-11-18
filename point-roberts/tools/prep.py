"""Grids, Sentinel-2 albedo, normals, shadows, Point Roberts outline. Region z10 terrain + z11 imagery; detail z13 terrain + z13 imagery."""
import glob, json, math, os, re, sys
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates, gaussian_filter, distance_transform_edt, binary_opening, label
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); D = os.path.join(HERE, 'data'); A = os.path.join(HERE, 'assets'); S2 = os.path.join(HERE, '..', 'assets', 's2')
R = [-124.3, -121.9, 48.45, 49.65]; DT = [-123.32, -122.68, 48.9, 49.16]
def lonlat(b, GW, GH):
    lon = b[0] + (np.arange(GW) + .5) / GW * (b[1] - b[0]); lat = b[3] - (np.arange(GH) + .5) / GH * (b[3] - b[2]); return np.meshgrid(lon, lat)
def merc(LO, LA, z): n = 2 ** z; return (LO + 180) / 360 * n * 256, (1 - np.log(np.tan(np.radians(LA)) + 1 / np.cos(np.radians(LA))) / math.pi) / 2 * n * 256
def mosaic(files, z, rx):
    xy = [tuple(map(int, re.findall(rx, os.path.basename(f))[0])) for f in files]; x0 = min(a for a, _ in xy); y0 = min(b for _, b in xy)
    x1 = max(a for a, _ in xy); y1 = max(b for _, b in xy); first = np.asarray(Image.open(files[0]))
    ch = 3 if first.ndim == 3 else 1; mos = np.zeros(((y1 - y0 + 1) * 256, (x1 - x0 + 1) * 256, ch), np.float32)
    for f, (x, y) in zip(files, xy):
        a = np.asarray(Image.open(f).convert('RGB'), np.float32); mos[(y - y0) * 256:(y - y0 + 1) * 256, (x - x0) * 256:(x - x0 + 1) * 256] = a
    return mos, x0, y0
def heights(tdir, z, b, GW, GH):
    fs = glob.glob(os.path.join(tdir, f'{z}_*.png')); mos, x0, y0 = mosaic(fs, z, rf'{z}_(\d+)_(\d+)')
    h = mos[..., 0] * 256 + mos[..., 1] + mos[..., 2] / 256 - 32768; LO, LA = lonlat(b, GW, GH); X, Y = merc(LO, LA, z)
    return map_coordinates(h, [Y - y0 * 256 - .5, X - x0 * 256 - .5], order=1, mode='nearest').astype(np.float32)
def imagery(sdir, z, b, GW, GH):
    fs = glob.glob(os.path.join(sdir, f'{z}_*.jpg')); mos, x0, y0 = mosaic(fs, z, rf'{z}_(\d+)_(\d+)'); LO, LA = lonlat(b, GW, GH); X, Y = merc(LO, LA, z)
    return np.dstack([map_coordinates(mos[..., c], [Y - y0 * 256 - .5, X - x0 * 256 - .5], order=1, mode='nearest') for c in range(3)]) / 255
RG, DG = (2400, 1200), (3200, 1300)
HR = heights(os.path.join(D, 't10'), 10, R, *RG); HD = heights(os.path.join(D, 't13'), 13, DT, *DG)
AR = imagery(os.path.join(S2, 'pointroberts_r'), 11, R, *RG); AD = imagery(os.path.join(S2, 'pointroberts_d'), 13, DT, *DG)
def grade(a): a = np.clip(a * 1.3, 0, 1) ** .78; g = a.mean(-1, keepdims=True); a = g + (a - g) * 1.12; return np.clip(a * np.array([1.03, 1., .95]), 0, 1)
for nm, a in (('albedo_r.jpg', grade(AR)), ('albedo_d.jpg', grade(AD))): Image.fromarray((a * 255).astype(np.uint8)).save(os.path.join(A, nm), quality=92)
cl = math.cos(math.radians(49)); EXN = 2.0
def normal(H, cx, cz, sig):
    L = gaussian_filter(np.maximum(H, 0), sig); gy, gx = np.gradient(L * EXN); n = np.dstack([-gx / cx, np.ones_like(gx), -gy / cz]); n /= np.linalg.norm(n, axis=2, keepdims=True)
    return ((n * .5 + .5) * 255).astype(np.uint8)
Image.fromarray(normal(HR, 111320 * cl * .001, 111320 * .001, 1.0)).save(os.path.join(A, 'normal_r.png'))
Image.fromarray(normal(HD, 111320 * cl * .0002, 111320 * .0002, 1.5)).save(os.path.join(A, 'normal_d.png'))
def htex(H, p): v = np.clip(H + 12000, 0, 65535).astype(np.uint16); Image.fromarray(np.dstack([(v >> 8).astype(np.uint8), (v & 255).astype(np.uint8), np.zeros_like(v, np.uint8)])).save(p)
htex(HR, os.path.join(A, 'height_r.png')); htex(HD, os.path.join(A, 'height_d.png'))
def mesh(H, w, h, nm): a = np.asarray(Image.fromarray(H).resize((w, h), Image.BILINEAR), np.float32); a.astype('<f4').tofile(os.path.join(A, nm))
mesh(HR, 600, 300, 'mesh_r.bin'); mesh(HD, 800, 325, 'mesh_d.bin')
# Point Roberts: land south of 49.0 N on the peninsula tip (detail grid)
LO, LA = lonlat(DT, *DG); land = HD > 1.0
pr = land & (LA < 49.0) & (LO > -123.11) & (LO < -122.99) & (LA > 48.95)
pr = binary_opening(pr, iterations=2); lab, n = label(pr); sizes = np.bincount(lab.ravel()); sizes[0] = 0; pr = lab == sizes.argmax()
Image.fromarray((pr * 255).astype(np.uint8)).save(os.path.join(A, 'mask_d.png'))
# outline: Moore-neighbour boundary trace (ordered), then thinned
def trace(m):
    H, W = m.shape; ys, xs = np.nonzero(m); i0 = np.argmin(ys * W + xs); y, x = ys[i0], xs[i0]
    nb = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]; out = [(y, x)]; d = 6; start = (y, x)
    for _ in range(200000):
        for k in range(8):
            dd = (d + 6 + k) % 8; ny, nx = y + nb[dd][0], x + nb[dd][1]
            if 0 <= ny < H and 0 <= nx < W and m[ny, nx]: y, x, d = ny, nx, dd; break
        if (y, x) == start: break
        out.append((y, x))
    return out
pts = trace(pr)
ring = [[round(float(LO[y, x]), 5), round(float(LA[y, x]), 5)] for y, x in pts[::4]]
area = pr.sum() * (111.32 * cl * .0002) * (111.32 * .0002)
meta = {'R': R, 'Dt': DT, 'mesh_r': [600, 300], 'mesh_d': [800, 325], 'lat0': 49.0, 'pr_area_km2': round(float(area), 2), 'pr_ring': ring + [ring[0]]}
json.dump(meta, open(os.path.join(A, 'meta.json'), 'w')); print('area km2', area, 'ring pts', len(ring))
np.save(os.path.join(D, 'HD.npy'), HD); np.save(os.path.join(D, 'HR.npy'), HR)
