"""Diorama data: a ~290 m grid over the Point Roberts detail box. Each land cell gets a class (town / green / farm) from the
Sentinel-2 colours, a country (USA south of 49°N), and houses/trees are scattered with a fixed seed."""
import json, numpy as np
from PIL import Image
SRC = '../point-roberts'
HD = np.load(f'{SRC}/data/HD.npy')                       # 1300 x 3200 over lon -123.32..-122.68, lat 48.9..49.16
AL = np.asarray(Image.open(f'{SRC}/assets/albedo_d.jpg').convert('RGB'), np.float32) / 255
GW, GH = 160, 100                                          # 0.004 x 0.0026 deg cells
def pool(a, f):
    h, w = a.shape[:2]; a = a[:h - h % GH, :w - w % GW]; sh = (GH, a.shape[0] // GH, GW, a.shape[1] // GW) + a.shape[2:]
    return f(a.reshape(sh), axis=(1, 3))
H = pool(HD, np.median); A = pool(AL, np.mean)
land = H > 1.5
lat = 49.16 - (np.arange(GH) + .5) / GH * .26; lon = -123.32 + (np.arange(GW) + .5) / GW * .64
LO, LA = np.meshgrid(lon, lat)
r, g, b = A[..., 0], A[..., 1], A[..., 2]; br = A.mean(-1); sat = A.max(-1) - A.min(-1)
town = land & (br > .40) & (sat < .11)
green = land & ~town & (g > r * 1.02) & (br < .34)
farm = land & ~town & ~green
rng = np.random.default_rng(11); cells = []
for j in range(GH):
    for i in range(GW):
        if not land[j, i]: continue
        cls = 'town' if town[j, i] else 'green' if green[j, i] else 'farm'
        cells.append([round(float(LO[j, i]), 4), round(float(LA[j, i]), 4), cls, 1 if LA[j, i] < 49.0 else 0, round(float(min(H[j, i], 120)), 1)])
houses, trees = [], []
for lo, la, cls, us, h in cells:
    if cls == 'town' and rng.random() < .22: houses.append([lo + rng.uniform(-.001, .001), la + rng.uniform(-.0006, .0006), float(rng.uniform(1.0, 2.6)), int(rng.integers(0, 5)), float(rng.uniform(0, 3.14))])
    if cls == 'green' and rng.random() < .7:
        for k in range(int(rng.integers(1, 3))): trees.append([lo + rng.uniform(-.0016, .0016), la + rng.uniform(-.001, .001), float(rng.uniform(.7, 1.3)), int(rng.integers(0, 3))])
    if cls == 'farm' and rng.random() < .06: trees.append([lo + rng.uniform(-.0016, .0016), la + rng.uniform(-.001, .001), float(rng.uniform(.6, 1.0)), 0])
json.dump({'grid': [GW, GH], 'box': [-123.32, -122.68, 48.9, 49.16], 'cells': cells, 'houses': houses, 'trees': trees}, open('assets/diorama.json', 'w'))
print(len(cells), 'land cells', len(houses), 'houses', len(trees), 'trees', 'town', int(town.sum()), 'green', int(green.sum()), 'farm', int(farm.sum()))
