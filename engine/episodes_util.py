"""Small helpers shared by episodes."""
import numpy as np
import cairo
W, H = 1080, 1920

def paint_rgba(c, rgba):
    """paint an (H, W, 4) uint8 RGBA numpy image onto the cairo context in screen space"""
    a = rgba[..., 3:4].astype(np.float32) / 255
    pm = np.dstack([(rgba[..., 2::-1].astype(np.float32) * a).astype(np.uint8), rgba[..., 3]])
    S = cairo.ImageSurface.create_for_data(bytearray(np.ascontiguousarray(pm).tobytes()), cairo.FORMAT_ARGB32, W, H)
    c.save(); c.identity_matrix(); c.set_source_surface(S); c.paint(); c.restore()
