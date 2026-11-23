"""Diorama cells for North Sentinel Island: terrain (AWS z12) + Sentinel-2 (EOX 2016, z13). Classes: jungle, beach, reef (shallow water)."""
import glob, json, math, os, re, numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates, binary_dilation, label
B = [92.08, 92.36, 11.44, 11.66]; GW, GH = 112, 88
lon = B[0] + (np.arange(GW) + .5) / GW * (B[1] - B[0]); lat = B[3] - (np.arange(GH) + .5) / GH * (B[3] - B[2]); LO, LA = np.meshgrid(lon, lat)
def merc(LO, LA, z): n = 2 ** z; return (LO + 180) / 360 * n * 256, (1 - np.log(np.tan(np.radians(LA)) + 1 / np.cos(np.radians(LA))) / math.pi) / 2 * n * 256
def mosaic(files, z, ext):
    xy = [tuple(map(int, re.findall(rf'{z}_(\d+)_(\d+)\.{ext}', os.path.basename(f))[0])) for f in files]; x0 = min(a for a, _ in xy); y0 = min(b for _, b in xy)
    x1 = max(a for a, _ in xy); y1 = max(b for _, b in xy); mos = np.zeros(((y1 - y0 + 1) * 256, (x1 - x0 + 1) * 256, 3), np.float32)
    for f, (x, y) in zip(files, xy): mos[(y - y0) * 256:(y - y0 + 1) * 256, (x - x0) * 256:(x - x0 + 1) * 256] = np.asarray(Image.open(f).convert('RGB'), np.float32)
    return mos, x0, y0
def sample(mos, x0, y0, z, sub=5):   # average sub x sub samples inside each cell
    acc = 0
    for i in range(sub):
        for j in range(sub):
            lo = LO + (i + .5) / sub * (B[1] - B[0]) / GW - (B[1] - B[0]) / GW / 2; la = LA + (j + .5) / sub * (B[3] - B[2]) / GH - (B[3] - B[2]) / GH / 2
            X, Y = merc(lo, la, z); acc = acc + np.dstack([map_coordinates(mos[..., c], [Y - y0 * 256, X - x0 * 256], order=1, mode='nearest') for c in range(mos.shape[2])])
    return acc / sub / sub
T, tx0, ty0 = mosaic(glob.glob('data/t12/12_*.png'), 12, 'png'); Hm = T[..., 0] * 256 + T[..., 1] + T[..., 2] / 256 - 32768
S, sx0, sy0 = mosaic(glob.glob('../assets/s2/northsentinel/13_*.jpg'), 13, 'jpg')
H = sample(Hm[..., None], tx0, ty0, 12)[..., 0]; A = sample(S, sx0, sy0, 13) / 255
r, g, b = A[..., 0], A[..., 1], A[..., 2]; br = A.mean(-1)
land = (g > b * 1.0) & (br < .55) & (g > .12) | (H > 3)                     # vegetation / land
lab, n = label(land); sz = np.bincount(lab.ravel()); sz[0] = 0; land = lab == sz.argmax()     # keep the island
beach = land & ~binary_dilation(~land, iterations=0) if False else (land & binary_dilation(~land, iterations=1) & (br > .32))
reef = ~land & (b > r * 1.05) & (br > .28) & binary_dilation(land, iterations=4)
cells = []
for j in range(GH):
    for i in range(GW):
        if land[j, i]: cells.append([round(float(LO[j, i]), 5), round(float(LA[j, i]), 5), 'beach' if beach[j, i] else 'jungle', round(float(max(H[j, i], 0)), 1)])
        elif reef[j, i]: cells.append([round(float(LO[j, i]), 5), round(float(LA[j, i]), 5), 'reef', 0])
rng = np.random.default_rng(4); trees = []
for lo, la, cls, h in cells:
    if cls == 'jungle':
        for k in range(2 if rng.random() < .6 else 1): trees.append([lo + rng.uniform(-.0011, .0011), la + rng.uniform(-.0011, .0011), float(rng.uniform(.8, 1.3)), int(rng.integers(0, 3))])
ys, xs = np.nonzero(land); cen = [float(LO[ys, xs].mean()), float(LA[ys, xs].mean())]
json.dump({'grid': [GW, GH], 'box': B, 'cells': cells, 'trees': trees, 'centre': cen, 'land_km2': float(land.sum() * (.0025 * 111.32 * math.cos(math.radians(11.55))) * (.0025 * 111.32))},
          open('assets/diorama.json', 'w'))
print('cells', len(cells), 'land', int(land.sum()), 'beach', int(beach.sum()), 'reef', int(reef.sum()), 'trees', len(trees), 'centre', cen)
