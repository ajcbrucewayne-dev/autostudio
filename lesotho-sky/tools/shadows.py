"""Bake soft sun shadows (same sun as the page: azimuth 315°, elevation 24°, relief ×6) for both grids."""
import os, numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); D = os.path.join(HERE, 'data'); A = os.path.join(HERE, 'assets')
EX, EL, AZ = 6.0, np.radians(15), np.radians(300)
def bake(H, cell_x_m, cell_y_m, K, out):
    H = np.maximum(H, 0) * EX; gh, gw = H.shape; yy, xx = np.mgrid[0:gh, 0:gw].astype(np.float32)
    sx, sy = np.sin(AZ), -np.cos(AZ)          # toward the sun in grid steps (x east, y down = south)
    step_m = 1.0; ux, uy = sx / cell_x_m, sy / cell_y_m; s = 1 / max(abs(ux), abs(uy)); ux *= s; uy *= s; step_m = s
    lit = np.ones_like(H); tanE = np.tan(EL)
    for k in range(1, K + 1):
        Hs = map_coordinates(H, [yy + uy * k, xx + ux * k], order=1, mode='nearest')
        d = k * step_m; over = (Hs - H - d * tanE) / (d * .035 + 30)     # penumbra widens with distance
        lit = np.minimum(lit, np.clip(1 - over, 0, 1))
    Image.fromarray((lit * 255).astype(np.uint8)).save(out); print(out, lit.mean())
HD = np.load(os.path.join(D, 'HD.npy')); HR = np.load(os.path.join(D, 'HR.npy'))
cl = np.cos(np.radians(29.3))
bake(HD, 111320 * cl * .00125, 111320 * .00125, 220, os.path.join(A, 'shadow_d.png'))
bake(HR, 111320 * cl * .01, 111320 * .01, 60, os.path.join(A, 'shadow_r.png'))
