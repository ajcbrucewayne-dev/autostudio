"""Realistic 3D map assets for a film: Sentinel-2 albedo + AWS terrain for a wide region and a detail box.
usage: prep.py <film>   (configs below; writes <film>/assets/*)
Outputs: albedo_{r,d}.jpg, normal_{r,d}.png, height_{r,d}.png (metres + 12000, 16-bit in R/G), shadow_{r,d}.png, mesh_{r,d}.bin, mask_d.png, meta.json"""
import glob, json, math, os, re, sys
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates, gaussian_filter, label, binary_closing
Image.MAX_IMAGE_PIXELS = None
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = {
  'ns-real': dict(R=[91.75, 93.15, 10.85, 12.35], D=[92.12, 92.33, 11.47, 11.65], tr=('ns_r', 10), td=('ns_d', 13), sr=('ns_region', 11), sd=('ns_island14', 14),
                  px_r=2000, px_d=2400, mesh_r=(420, 450), mesh_d=(520, 446), ex=4.0, sun=(300, 28), mask='island', grade=(1.08, 1.25), gamma=.62),
  'sv-real': dict(R=[13.6, 17.6, 77.95, 78.55], D=[15.36, 15.74, 78.185, 78.27], tr=('sv_r', 10), td=('sv_d12', 12), sr=('sv_region', 10), sd=('sv_detail', 13),
                  px_r=2400, px_d=2000, mesh_r=(560, 420), mesh_d=(520, 640), ex=1.6, sun=(25, 24), shadows=False, delight=.42, spike_wide=41, mask=None, grade=(1.1, 1.08), gamma=.68, warm=(1.06, 1.0, .9)),
}
film = sys.argv[1]; C = CFG[film]; OUT = os.path.join(ROOT, film, 'assets'); os.makedirs(OUT, exist_ok=True)
def merc(LO, LA, z): n = 2 ** z; return (LO + 180) / 360 * n * 256, (1 - np.log(np.tan(np.radians(LA)) + 1 / np.cos(np.radians(LA))) / math.pi) / 2 * n * 256
def mosaic(d, z, ext, heights=False):
    fs = glob.glob(os.path.join(d, f'{z}_*.{ext}')); xy = [tuple(map(int, re.findall(rf'{z}_(\d+)_(\d+)', os.path.basename(f))[0])) for f in fs]
    x0 = min(a for a, _ in xy); y0 = min(b for _, b in xy); x1 = max(a for a, _ in xy); y1 = max(b for _, b in xy)
    M = np.zeros(((y1 - y0 + 1) * 256, (x1 - x0 + 1) * 256, 3), np.float32)
    for f, (x, y) in zip(fs, xy): M[(y - y0) * 256:(y - y0 + 1) * 256, (x - x0) * 256:(x - x0 + 1) * 256] = np.asarray(Image.open(f).convert('RGB'), np.float32)
    if heights: M = M[..., 0] * 256 + M[..., 1] + M[..., 2] / 256 - 32768
    return M, x0, y0
def resample(M, x0, y0, z, box, w, h):     # equirect grid (row 0 = north) sampled from a web-mercator mosaic
    lon = box[0] + (np.arange(w) + .5) / w * (box[1] - box[0]); lat = box[3] - (np.arange(h) + .5) / h * (box[3] - box[2]); LO, LA = np.meshgrid(lon, lat)
    X, Y = merc(LO, LA, z); X -= x0 * 256; Y -= y0 * 256
    if M.ndim == 2: return map_coordinates(M, [Y, X], order=1, mode='nearest')
    return np.dstack([map_coordinates(M[..., c], [Y, X], order=1, mode='nearest') for c in range(3)])
def grade(a, con, sat):
    g = a.mean(-1, keepdims=True); a = g + (a - g) * sat; return np.clip((a - .5) * con + .5, 0, 1)
def normal(H, cx, cz, ex, sig):
    L = gaussian_filter(np.maximum(H, 0), sig); gy, gx = np.gradient(L * ex)
    n = np.dstack([-gx / cx, np.ones_like(gx), -gy / cz]); n /= np.linalg.norm(n, axis=2, keepdims=True); return ((n * .5 + .5) * 255).astype(np.uint8)
def shadows(H, cx, cz, ex, az, el, K):
    H = np.maximum(H, 0) * ex; gh, gw = H.shape; yy, xx = np.mgrid[0:gh, 0:gw].astype(np.float32)
    ux, uy = np.sin(az) / cx, -np.cos(az) / cz; s = 1 / max(abs(ux), abs(uy)); ux *= s; uy *= s; tanE = np.tan(el); lit = np.ones_like(H)
    for k in range(1, K + 1):
        Hs = map_coordinates(H, [yy + uy * k, xx + ux * k], order=1, mode='nearest'); d = k * s
        lit = np.minimum(lit, np.clip(1 - (Hs - H - d * tanE) / (d * .035 + 25), 0, 1))
    return lit
def htex(H, path):
    v = np.clip(H + 12000, 0, 65535).astype(np.uint16); Image.fromarray(np.dstack([(v >> 8).astype(np.uint8), (v & 255).astype(np.uint8), np.zeros_like(v, np.uint8)])).save(path)
meta = {'R': C['R'], 'D': C['D'], 'ex': C['ex'], 'sun': C['sun'], 'lat0': (C['R'][2] + C['R'][3]) / 2}
for key, box, (td, tz), (sd, sz), px, msz in [('r', C['R'], C['tr'], C['sr'], C['px_r'], C['mesh_r']), ('d', C['D'], C['td'], C['sd'], C['px_d'], C['mesh_d'])]:
    kx = 111320 * math.cos(math.radians((box[2] + box[3]) / 2)); w = px; h = int(round(px * (box[3] - box[2]) * 111320 / ((box[1] - box[0]) * kx)))
    T, tx0, ty0 = mosaic(os.path.join(ROOT, 'geo3d', 'data', td), tz, 'png', True); H = resample(T, tx0, ty0, tz, box, w, h)
    from scipy.ndimage import median_filter
    Md = median_filter(H, 7); bad = np.abs(H - Md) > C.get('spike', 250); H[bad] = Md[bad]
    if key == 'd' and C.get('spike_wide'):   # detail vs the coarse regional terrain: anything >250 m above it is a tile artefact
        Tr, rx0, ry0 = mosaic(os.path.join(ROOT, 'geo3d', 'data', C['tr'][0]), C['tr'][1], 'png', True); Hr = gaussian_filter(resample(Tr, rx0, ry0, C['tr'][1], box, w, h), 6)
        b2 = (H - Hr) > 250; H[b2] = Hr[b2]; print('detail vs region fixed', int(b2.sum()))
    print(key, 'spikes fixed', int(bad.sum()))
    S, sx0, sy0 = mosaic(os.path.join(ROOT, 'assets', 's2', sd), sz, 'jpg'); A = grade((resample(S, sx0, sy0, sz, box, w, h) / 255) ** C.get('gamma', 1), *C['grade'])
    cx = (box[1] - box[0]) * kx / w; cz = (box[3] - box[2]) * 111320 / h
    if C.get('warm'): A = np.clip(A * np.array(C['warm']), 0, 1)
    if C.get('delight'):     # lift the shadows baked into the photo (low Arctic sun): equalise local brightness
        L = gaussian_filter(A.mean(-1), 18 if key == 'd' else 10); gain = np.clip((C['delight'] / np.maximum(L, .02)) ** .85, 1, 3.2)
        A = np.clip(A * gain[..., None], 0, 1)
    Image.fromarray((A * 255).astype(np.uint8)).save(os.path.join(OUT, f'albedo_{key}.jpg'), quality=92)
    Image.fromarray(normal(H, cx, cz, C['ex'], 1.0 if key == 'r' else 1.4)).save(os.path.join(OUT, f'normal_{key}.png'))
    htex(H, os.path.join(OUT, f'height_{key}.png'))
    lit = shadows(H, cx, cz, C['ex'], math.radians(C['sun'][0]), math.radians(C['sun'][1]), 160 if key == 'd' else 80) if C.get('shadows', True) else np.ones_like(H)
    Image.fromarray((lit * 255).astype(np.uint8)).save(os.path.join(OUT, f'shadow_{key}.png'))
    Hm = np.asarray(Image.fromarray(H.astype(np.float32)).resize(msz, Image.BILINEAR), np.float32); Hm.astype('<f4').tofile(os.path.join(OUT, f'mesh_{key}.bin'))
    meta['mesh_' + key] = list(msz); meta['tex_' + key] = [w, h]; meta['hmax_' + key] = float(H.max())
    if key == 'd' and C['mask'] == 'island':   # the island: vegetation or above sea, largest blob
        br = A.mean(-1); land = ((A[..., 1] > A[..., 2] * 1.0) & (br < .6) & (br > .08)) | (H > 4)
        lab, n = label(land); sz2 = np.bincount(lab.ravel()); sz2[0] = 0; m = binary_closing(lab == sz2.argmax(), iterations=3)
        Image.fromarray((gaussian_filter(m.astype(np.float32), 1.2) * 255).astype(np.uint8)).save(os.path.join(OUT, 'mask_d.png'))
        ys, xs = np.nonzero(m); meta['island_centre'] = [float(box[0] + (xs.mean() + .5) / w * (box[1] - box[0])), float(box[3] - (ys.mean() + .5) / h * (box[3] - box[2]))]
        meta['island_km2'] = float(m.sum() * cx * cz / 1e6)
    print(key, w, h, 'H', float(H.min()), float(H.max()))
json.dump(meta, open(os.path.join(OUT, 'meta.json'), 'w'), indent=1); print(meta)
