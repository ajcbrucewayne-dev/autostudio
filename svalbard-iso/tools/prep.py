"""Svalbard diorama cells from AWS terrain (z12): Longyearbyen, Platåberget and the Global Seed Vault.
Classes by height and slope: tundra (valley floor), shore, rock (steep), snow (high/plateau). Sea = everything at or below 0 m."""
import glob, json, math, os, re, numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates, binary_dilation, label, uniform_filter
B = [15.38, 15.72, 78.19, 78.265]; GW, GH = 65, 71
lon = B[0] + (np.arange(GW) + .5) / GW * (B[1] - B[0]); lat = B[3] - (np.arange(GH) + .5) / GH * (B[3] - B[2]); LO, LA = np.meshgrid(lon, lat)
def merc(LO, LA, z): n = 2 ** z; return (LO + 180) / 360 * n * 256, (1 - np.log(np.tan(np.radians(LA)) + 1 / np.cos(np.radians(LA))) / math.pi) / 2 * n * 256
fs = glob.glob('data/t12/12_*.png'); xy = [tuple(map(int, re.findall(r'12_(\d+)_(\d+)', os.path.basename(f))[0])) for f in fs]
x0 = min(a for a, _ in xy); y0 = min(b for _, b in xy); x1 = max(a for a, _ in xy); y1 = max(b for _, b in xy)
T = np.zeros(((y1 - y0 + 1) * 256, (x1 - x0 + 1) * 256, 3), np.float32)
for f, (x, y) in zip(fs, xy): T[(y - y0) * 256:(y - y0 + 1) * 256, (x - x0) * 256:(x - x0 + 1) * 256] = np.asarray(Image.open(f).convert('RGB'), np.float32)
Hm = T[..., 0] * 256 + T[..., 1] + T[..., 2] / 256 - 32768
acc = 0
for i in range(4):
    for j in range(4):
        lo = LO + ((i + .5) / 4 - .5) * (B[1] - B[0]) / GW; la = LA + ((j + .5) / 4 - .5) * (B[3] - B[2]) / GH; X, Y = merc(lo, la, 12)
        acc = acc + map_coordinates(Hm, [Y - y0 * 256, X - x0 * 256], order=1, mode='nearest')
H = acc / 16
from scipy.ndimage import median_filter
Med = median_filter(H, 5); spike = (H - Med) > 120; print('spikes', int(spike.sum())); H[spike] = Med[spike]
KX = 111.32 * math.cos(math.radians(78.225)); cw = (B[1] - B[0]) / GW * KX * 1000; ch = (B[3] - B[2]) / GH * 111320
gy, gx = np.gradient(H, ch, cw); slope = np.degrees(np.arctan(np.hypot(gx, gy)))
land = H > 1.5
lab, n = label(land); sz = np.bincount(lab.ravel()); sz[0] = 0; land &= sz[lab] > 6
shore = land & binary_dilation(~land, iterations=1) & (H < 25)
snow = land & ((H > 330) | ((H > 230) & (slope < 9)))
rock = land & ~snow & (slope > 22)
cls = np.where(~land, 'sea', np.where(shore, 'shore', np.where(snow, 'snow', np.where(rock, 'rock', 'tundra'))))
cells = [[round(float(LO[j, i]), 5), round(float(LA[j, i]), 5), str(cls[j, i]), round(float(H[j, i]), 1)] for j in range(GH) for i in range(GW) if land[j, i]]
print('land', int(land.sum()), {c: int((cls == c).sum()) for c in ['shore', 'snow', 'rock', 'tundra']}, 'Hmax', H.max(), 'cell m', cw, ch)
V = [15.4911, 78.2357]; vi = np.argmin(abs(lon - V[0])); vj = np.argmin(abs(lat - V[1])); print('vault cell H', H[vj, vi], cls[vj, vi], 'slope', slope[vj, vi])
json.dump({'grid': [GW, GH], 'box': B, 'cells': cells, 'cell_m': [cw, ch], 'vault': V}, open('assets/diorama.json', 'w'))
# quick map
img = np.zeros((GH, GW, 3), np.uint8); col = {'sea': (40, 110, 170), 'shore': (220, 210, 170), 'snow': (245, 248, 252), 'rock': (120, 110, 105), 'tundra': (140, 150, 100)}
for c, v in col.items(): img[cls == c] = v
img[vj, vi] = (255, 0, 0); Image.fromarray(img).resize((GW * 5, GH * 5), Image.NEAREST).save('out/classmap.png')
