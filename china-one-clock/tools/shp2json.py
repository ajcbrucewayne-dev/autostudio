"""Minimal shapefile (polygon / polyline) + dbf reader -> GeoJSON-like dict. Standard library only."""
import struct, json, sys
def read_dbf(path):
    b = open(path, 'rb').read(); n, hl, rl = struct.unpack('<xxxxIHH', b[:12])
    fields = []; o = 32
    while b[o] != 0x0D:
        name = b[o:o+11].split(b'\0')[0].decode(); ln = b[o+16]; fields.append((name, ln)); o += 32
    recs = []; o = hl
    for _ in range(n):
        r = b[o:o+rl]; o += rl; p = 1; d = {}
        for name, ln in fields: d[name] = r[p:p+ln].decode('utf-8', 'replace').strip(' \x00'); p += ln
        recs.append(d)
    return recs
def read_shp(path):
    b = open(path, 'rb').read(); o = 100; out = []
    while o < len(b):
        _, clen = struct.unpack('>ii', b[o:o+8]); o += 8; rec = b[o:o+clen*2]; o += clen*2
        st = struct.unpack('<i', rec[:4])[0]
        if st == 0: out.append(None); continue
        np_, npt = struct.unpack('<ii', rec[36:44]); parts = list(struct.unpack(f'<{np_}i', rec[44:44+4*np_])) + [npt]
        pts = struct.unpack(f'<{2*npt}d', rec[44+4*np_:44+4*np_+16*npt])
        rings = [[(pts[2*i], pts[2*i+1]) for i in range(parts[k], parts[k+1])] for k in range(np_)]
        out.append((st, rings))
    return out
if __name__ == '__main__':
    base, key, val, out = sys.argv[1:5]
    recs = read_dbf(base + '.dbf'); shps = read_shp(base + '.shp'); feats = []
    for r, s in zip(recs, shps):
        if s and (val == '*' or r.get(key) == val): feats.append({'props': r, 'type': s[0], 'rings': s[1]})
    json.dump(feats, open(out, 'w')); print(len(feats), 'features')
