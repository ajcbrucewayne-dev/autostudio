"""Height grids (equirectangular) from terrarium tiles, country masks, and measurements for FACTS.md.
Region: lon 14..36E, lat 36..20S (z8). Detail: lon 26.8..29.7E, lat 30.9..28.4S (z10)."""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import map_coordinates
sys.path.insert(0, os.path.dirname(__file__)); from shp2json import read_dbf, read_shp
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); D = os.path.join(HERE, 'data'); A = os.path.join(HERE, 'assets')
def grid(z, tdir, lon0, lon1, lat0, lat1, GW, GH):
    lon = lon0 + (np.arange(GW) + .5) / GW * (lon1 - lon0); lat = lat1 - (np.arange(GH) + .5) / GH * (lat1 - lat0)
    LO, LA = np.meshgrid(lon, lat); n = 2 ** z
    X = (LO + 180) / 360 * n * 256; Y = (1 - np.log(np.tan(np.radians(LA)) + 1 / np.cos(np.radians(LA))) / math.pi) / 2 * n * 256
    tx0, ty0, tx1, ty1 = int(X.min() // 256), int(Y.min() // 256), int(X.max() // 256), int(Y.max() // 256)
    mos = np.zeros(((ty1 - ty0 + 1) * 256, (tx1 - tx0 + 1) * 256), np.float32)
    for tx in range(tx0, tx1 + 1):
        for ty in range(ty0, ty1 + 1):
            a = np.asarray(Image.open(os.path.join(tdir, f'{z}_{tx}_{ty}.png')).convert('RGB'), np.float32)
            mos[(ty - ty0) * 256:(ty - ty0 + 1) * 256, (tx - tx0) * 256:(tx - tx0 + 1) * 256] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
    return map_coordinates(mos, [Y - ty0 * 256 - .5, X - tx0 * 256 - .5], order=1).astype(np.float32)
R = dict(lon0=14, lon1=36, lat0=-36, lat1=-20); Dt = dict(lon0=26.8, lon1=29.7, lat0=-30.9, lat1=-28.4)
HR = grid(8, os.path.join(D, 'tiles8'), R['lon0'], R['lon1'], R['lat0'], R['lat1'], 2200, 1600)       # 0.01 deg
HD = grid(10, os.path.join(D, 'tiles10'), Dt['lon0'], Dt['lon1'], Dt['lat0'], Dt['lat1'], 2320, 2000) # 0.00125 deg (~130 m)
base = os.path.join(D, 'raw', 'ne_10m_admin_0_countries_chn'); recs, shps = read_dbf(base + '.dbf'), read_shp(base + '.shp')
def rings(adm): return [r for d, s in zip(recs, shps) if d['ADMIN'] == adm for r in s[1]]
def mask(rs, b, GW, GH):   # even-odd fill so holes (Lesotho inside South Africa) stay empty
    m = np.zeros((GH, GW), bool)
    for r in rs:
        im = Image.new('1', (GW, GH), 0); ImageDraw.Draw(im).polygon([((x - b['lon0']) / (b['lon1'] - b['lon0']) * GW, (b['lat1'] - y) / (b['lat1'] - b['lat0']) * GH) for x, y in r], fill=1)
        m ^= np.asarray(im, bool)
    return m
LSO, ZAF = rings('Lesotho'), rings('South Africa')
mL, mZ = mask(LSO, R, 2200, 1600), mask(ZAF, R, 2200, 1600); mLd = mask(LSO, Dt, 2320, 2000)
lat = R['lat1'] - (np.arange(1600) + .5) / 1600 * 16; w = np.cos(np.radians(lat))[:, None] * np.ones((1, 2200))   # area weights
meas = {'zaf_below': {}, 'lso_min_m': float(HD[mLd].min()), 'lso_max_m': float(HD[mLd].max()), 'lso_p01_m': float(np.percentile(HD[mLd], 1)),
        'lso_share_above_1800': float((HD[mLd] > 1800).mean()), 'lso_share_above_2000': float((HD[mLd] > 2000).mean())}
for h in (200, 500, 1000, 1200, 1345, 1400, 1500):
    meas['zaf_below'][h] = float((w * ((HR < h) & mZ)).sum() / (w * mZ).sum())
json.dump(meas, open(os.path.join(HERE, 'data', 'measure.json'), 'w'), indent=1); print(json.dumps(meas, indent=1))
np.save(os.path.join(D, 'HR.npy'), HR); np.save(os.path.join(D, 'HD.npy'), HD)
np.save(os.path.join(D, 'mL.npy'), mL); np.save(os.path.join(D, 'mZ.npy'), mZ); np.save(os.path.join(D, 'mLd.npy'), mLd)
json.dump({'LSO': [[[round(a, 4), round(b, 4)] for a, b in r] for r in LSO], 'R': R, 'Dt': Dt}, open(os.path.join(A, 'lesotho.json'), 'w'))
