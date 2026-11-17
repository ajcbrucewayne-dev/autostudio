"""Build the film's data: equirectangular grids over lon 60..150E, lat 0..60N.
height.png (16-bit, metres+11000), albedo.jpg (graded, sea shaded by depth), china_mask.png, china.json (outline rings + SCS dashes)."""
import json, math, os, sys, glob
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(__file__)); from shp2json import read_dbf, read_shp
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); D = os.path.join(HERE, 'data'); A = os.path.join(HERE, 'assets'); os.makedirs(A, exist_ok=True)
LON0, LON1, LAT0, LAT1 = 60.0, 150.0, 0.0, 60.0
GW, GH = 2700, 1800                                    # 30 px / degree grid
lon = LON0 + (np.arange(GW) + 0.5) / GW * (LON1 - LON0); lat = LAT1 - (np.arange(GH) + 0.5) / GH * (LAT1 - LAT0)
# ---- height from terrarium z6 tiles (Web Mercator) sampled at lon/lat
z = 6; n = 2 ** z
LO, LA = np.meshgrid(lon, lat)
X = (LO + 180) / 360 * n * 256; Y = (1 - np.log(np.tan(np.radians(LA)) + 1 / np.cos(np.radians(LA))) / math.pi) / 2 * n * 256
tx0, ty0 = int(X.min() // 256), int(Y.min() // 256); tx1, ty1 = int(X.max() // 256), int(Y.max() // 256)
mos = np.zeros(((ty1 - ty0 + 1) * 256, (tx1 - tx0 + 1) * 256), np.float32)
for tx in range(tx0, tx1 + 1):
    for ty in range(ty0, ty1 + 1):
        a = np.asarray(Image.open(os.path.join(D, 'tiles', f'{z}_{tx}_{ty}.png')).convert('RGB'), np.float32)
        mos[(ty - ty0) * 256:(ty - ty0 + 1) * 256, (tx - tx0) * 256:(tx - tx0 + 1) * 256] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
from scipy.ndimage import map_coordinates
H = map_coordinates(mos, [Y - ty0 * 256 - 0.5, X - tx0 * 256 - 0.5], order=1).astype(np.float32)
Image.fromarray(np.clip(H + 11000, 0, 65535).astype(np.uint16)).save(os.path.join(A, 'height.png'))
print('height', H.min(), H.max())
# ---- albedo: Blue Marble crop (lon 60..150, lat 0..60 at 66.7 px/deg) resized to 2x grid, graded warm; sea by depth
bm = Image.open(os.path.join(D, 'raw', 'bluemarble_asia.jpg')).convert('RGB').resize((GW * 2, GH * 2), Image.LANCZOS)
alb = np.asarray(bm, np.float32) / 255
Hb = np.asarray(Image.fromarray(H).resize((GW * 2, GH * 2), Image.BILINEAR), np.float32)
land = Hb > 0.5
g = alb.mean(-1, keepdims=True); alb = g + (alb - g) * 0.85                       # a little less saturation
alb = np.clip((alb - 0.5) * 1.12 + 0.5, 0, 1); alb = alb * np.array([1.06, 1.0, 0.9])   # more contrast, warm
from scipy.ndimage import distance_transform_edt
dist = distance_transform_edt(~land) * (111.0 * 0.5 / 30)                        # km from coast (approx)
deep, shallow = np.array([0x0E, 0x22, 0x30]) / 255, np.array([0x1F, 0x5A, 0x5C]) / 255
k = np.clip(np.maximum(-Hb, 0) / 3000, 0, 1)[..., None] * 0.6 + np.clip(dist / 250, 0, 1)[..., None] * 0.4
sea = shallow * (1 - k) + deep * k; sea = sea * 0.75 + alb * 0.25 * (1 - k)
alb = np.where(land[..., None], alb, sea)
Image.fromarray((np.clip(alb, 0, 1) * 255).astype(np.uint8)).save(os.path.join(A, 'albedo.jpg'), quality=90)
# ---- China (Natural Earth 1:10m, China view: includes Taiwan) + South China Sea dashed line
base = os.path.join(D, 'raw', 'ne_10m_admin_0_countries_chn')
recs, shps = read_dbf(base + '.dbf'), read_shp(base + '.shp')
rings = [r for d, s in zip(recs, shps) if d['ADMIN'] == 'China' for r in s[1]]
mask = Image.new('L', (GW, GH), 0); dr = ImageDraw.Draw(mask)
def px(p): return ((p[0] - LON0) / (LON1 - LON0) * GW, (LAT1 - p[1]) / (LAT1 - LAT0) * GH)
from shp2json import read_shp as _r
for r in rings: dr.polygon([px(p) for p in r], fill=255)
mask.save(os.path.join(A, 'china_mask.png'))
dash = [s[1][0] for s in read_shp(os.path.join(D, 'raw', 'ne_10m_admin_0_boundary_lines_maritime_indicator_chn.shp'))]
def simp(r, tol=0.03):   # light decimation for ribbons
    out = [r[0]]
    for p in r[1:]:
        if abs(p[0] - out[-1][0]) + abs(p[1] - out[-1][1]) > tol: out.append(p)
    return [[round(a, 3), round(b, 3)] for a, b in out]
big = sorted(rings, key=len, reverse=True)
json.dump({'rings': [simp(r) for r in rings if len(r) > 8], 'dash': [[[round(a, 3), round(b, 3)] for a, b in d] for d in dash],
           'box': [LON0, LON1, LAT0, LAT1]}, open(os.path.join(A, 'china.json'), 'w'))
print('rings', len(rings), 'kept', sum(len(r) > 8 for r in rings), 'dashes', len(dash))
