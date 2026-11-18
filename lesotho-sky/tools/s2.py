"""Blend EOX Sentinel-2 cloudless 2016 (z12) into the detail albedo where available (feathered)."""
import glob, math, os, re
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates, distance_transform_edt
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); A = os.path.join(HERE, 'assets'); SRC = os.path.join(HERE, '..', 'assets', 's2', 'lesotho')
fs = glob.glob(os.path.join(SRC, '12_*.jpg')); xy = [tuple(map(int, re.findall(r'12_(\d+)_(\d+)', f)[0])) for f in fs]
x0, x1 = min(x for x, _ in xy), max(x for x, _ in xy); y0, y1 = min(y for _, y in xy), max(y for _, y in xy)
mos = np.zeros(((y1 - y0 + 1) * 256, (x1 - x0 + 1) * 256, 3), np.float32); have = np.zeros(mos.shape[:2], bool)
for f, (x, y) in zip(fs, xy):
    a = np.asarray(Image.open(f).convert('RGB'), np.float32) / 255; mos[(y - y0) * 256:(y - y0 + 1) * 256, (x - x0) * 256:(x - x0 + 1) * 256] = a
    have[(y - y0) * 256:(y - y0 + 1) * 256, (x - x0) * 256:(x - x0 + 1) * 256] = True
GW, GH = 2320, 2000; lon = 26.8 + (np.arange(GW) + .5) / GW * 2.9; lat = -28.4 - (np.arange(GH) + .5) / GH * 2.5
LO, LA = np.meshgrid(lon, lat); n = 2 ** 12
X = (LO + 180) / 360 * n * 256 - x0 * 256; Y = (1 - np.log(np.tan(np.radians(LA)) + 1 / np.cos(np.radians(LA))) / math.pi) / 2 * n * 256 - y0 * 256
inside = (X >= 0) & (X < mos.shape[1] - 1) & (Y >= 0) & (Y < mos.shape[0] - 1)
s2 = np.dstack([map_coordinates(mos[..., c], [Y, X], order=1, mode='nearest') for c in range(3)])
ok = inside & (map_coordinates(have.astype(float), [Y, X], order=0, mode='constant') > .5)
w = np.clip(distance_transform_edt(ok) / 40, 0, 1)[..., None]           # 40-px feather
g = s2.mean(-1, keepdims=True); s2 = np.clip((g + (s2 - g) * 1.05 - .5) * 1.08 + .5, 0, 1) * np.array([1.04, 1., .93])   # match the warm grade
base = np.asarray(Image.open(os.path.join(A, 'albedo_d.jpg')).convert('RGB'), np.float32) / 255
out = base * (1 - w) + s2 * w
Image.fromarray((out * 255).astype(np.uint8)).save(os.path.join(A, 'albedo_d_s2.jpg'), quality=92); print('s2 coverage', ok.mean())
