"""Textures and meshes for the page: region (0.01 deg) and Lesotho detail (0.00125 deg)."""
import json, os
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, distance_transform_edt
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); D = os.path.join(HERE, 'data'); A = os.path.join(HERE, 'assets')
HR, HD, mL, mLd = (np.load(os.path.join(D, n + '.npy')) for n in ('HR', 'HD', 'mL', 'mLd'))
EXN = 3.0
def normal(H, kmx, kmz, sig=1.0):
    L = gaussian_filter(np.maximum(H, 0), sig); gy, gx = np.gradient(L / 1000 * EXN)
    n = np.dstack([-gx / kmx, np.ones_like(gx), -gy / kmz]); n /= np.linalg.norm(n, axis=2, keepdims=True); return ((n * .5 + .5) * 255).astype(np.uint8)
cl = np.cos(np.radians(29.3))
Image.fromarray(normal(HR, 111.32 * cl * .01, 111.32 * .01)).save(os.path.join(A, 'normal_r.png'))
Image.fromarray(normal(HD, 111.32 * cl * .00125, 111.32 * .00125, 1.5)).save(os.path.join(A, 'normal_d.png'))
# height textures (16-bit split into R/G) for the water depth
def htex(H, path):
    v = np.clip(H + 12000, 0, 65535).astype(np.uint16); Image.fromarray(np.dstack([(v >> 8).astype(np.uint8), (v & 255).astype(np.uint8), np.zeros_like(v, np.uint8)])).save(path)
htex(HR, os.path.join(A, 'height_r.png')); htex(HD, os.path.join(A, 'height_d.png'))
# albedo: Blue Marble crop (lon 14..36, lat -20..-36), graded warm; sea shaded by depth
bm = np.asarray(Image.open(os.path.join(D, 'raw', 'bluemarble_sa.jpg')).convert('RGB').resize((2200, 1600), Image.LANCZOS), np.float32) / 255
g = bm.mean(-1, keepdims=True); alb = g + (bm - g) * .9; alb = np.clip((alb - .5) * 1.1 + .5, 0, 1) * np.array([1.05, 1., .92])
land = HR > .5; dist = distance_transform_edt(~land) * 1.0
deep, shallow = np.array([14, 34, 48]) / 255, np.array([31, 90, 92]) / 255
k = (np.clip(-HR / 3000, 0, 1) * .6 + np.clip(dist / 120, 0, 1) * .4)[..., None]
alb = np.where(land[..., None], alb, shallow * (1 - k) + deep * k)
Image.fromarray((np.clip(alb, 0, 1) * 255).astype(np.uint8)).save(os.path.join(A, 'albedo_r.jpg'), quality=90)
# detail albedo: the same imagery upsampled over the detail box
x0, x1 = (26.8 - 14) / 22 * 2200, (29.7 - 14) / 22 * 2200; y0, y1 = (-20 + 28.4) / 16 * 1600, (-20 + 30.9) / 16 * 1600
ad = Image.fromarray((np.clip(alb, 0, 1) * 255).astype(np.uint8)).crop((int(x0), int(y0), int(x1) + 1, int(y1) + 1)).resize((2320, 2000), Image.BICUBIC)
ad.save(os.path.join(A, 'albedo_d.jpg'), quality=90)
Image.fromarray((mL * 255).astype(np.uint8)).save(os.path.join(A, 'mask_r.png')); Image.fromarray((mLd * 255).astype(np.uint8)).save(os.path.join(A, 'mask_d.png'))
# meshes (float32 land+sea heights in metres)
def mesh(H, w, h, name):
    Image.fromarray(H).resize((w, h), Image.BILINEAR); a = np.asarray(Image.fromarray(H).resize((w, h), Image.BILINEAR), np.float32); a.astype('<f4').tofile(os.path.join(A, name)); return a
mesh(HR, 734, 534, 'mesh_r.bin'); mesh(HD, 581, 501, 'mesh_d.bin')
# extremes inside Lesotho (detail grid)
Hm = np.where(mLd, HD, np.nan); j, i = np.unravel_index(np.nanargmin(Hm), Hm.shape); J, I = np.unravel_index(np.nanargmax(Hm), Hm.shape)
ll = lambda i, j: [26.8 + (i + .5) / 2320 * 2.9, -28.4 - (j + .5) / 2000 * 2.5]
meta = {'R': [14, 36, -36, -20], 'Dt': [26.8, 29.7, -30.9, -28.4], 'mesh_r': [734, 534], 'mesh_d': [581, 501], 'lat0': -29.3,
        'low': ll(i, j) + [float(HD[j, i])], 'high': ll(I, J) + [float(HD[J, I])]}
json.dump(meta, open(os.path.join(A, 'meta.json'), 'w'), indent=1); print(meta)
