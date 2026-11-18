"""Apparent sunrise (NOAA approximation, -0.833 deg) in Beijing time (UTC+8) for 21 Dec; also used by the page via sun.json."""
import math, json, sys
def solar(N, utc_h):
    g = 2 * math.pi / 365 * (N - 1 + (utc_h - 12) / 24)
    eqt = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g) - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    dec = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g) + 0.000907 * math.sin(2 * g)
           - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    return eqt, dec
def sunrise_bj(lat, lon, N=355):
    eqt, dec = solar(N, 0)
    ha = math.degrees(math.acos(math.cos(math.radians(90.833)) / (math.cos(math.radians(lat)) * math.cos(dec)) - math.tan(math.radians(lat)) * math.tan(dec)))
    return 720 - 4 * (lon + ha) - eqt + 480
if __name__ == '__main__':
    eqt, dec = solar(355, 0); print(json.dumps({'eqt_min': eqt, 'dec_rad': dec}))
