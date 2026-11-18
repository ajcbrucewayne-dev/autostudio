"""AWS Terrain Tiles (terrarium PNG, free with attribution) for a lon/lat box at one zoom."""
import math, os, sys, urllib.request, time
z = int(sys.argv[1]); lon0, lat0, lon1, lat1 = map(float, sys.argv[2:6]); out = sys.argv[6]
def tx(lon): return int((lon + 180) / 360 * 2 ** z)
def ty(lat): r = math.radians(lat); return int((1 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2 * 2 ** z)
os.makedirs(out, exist_ok=True); log = open(os.path.join(out, 'fetch.log'), 'a'); n = 0
for x in range(tx(lon0), tx(lon1) + 1):
    for y in range(ty(lat1), ty(lat0) + 1):
        f = os.path.join(out, f'{z}_{x}_{y}.png')
        if os.path.exists(f): continue
        url = f'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png'
        for k in range(4):
            try: urllib.request.urlretrieve(url, f); break
            except Exception as e: time.sleep(2 * (k + 1))
        log.write(f'{time.strftime("%Y-%m-%d")} {url}\n'); n += 1
print('fetched', n)
