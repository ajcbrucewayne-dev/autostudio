"""Score + foley + narration for "Kingdom in the Sky" → out/mix.wav. D dorian, 92 bpm. Cue map: TREATMENT.md §5.
Instruments: VSCO 2 CE and VCSL (CC0). Voice: Kokoro bm_lewis."""
import os, re, sys, json
import numpy as np, soundfile as sf
LIB = os.environ.get('LIB', '/root/lemo-opuscar'); sys.path.insert(0, LIB)
from core.audio import sampler as S
from core.audio.sfx import SR, add, limit, compress, noise, brown, lp, hp, bp, whoosh, env_exp, t_
HERE = os.path.dirname(os.path.abspath(__file__))
EV = json.load(open(os.path.join(HERE, 'events.json'))); DUR = EV['dur']; ev = EV['ev']; N = int(DUR * SR)
S.seed(11); BEAT = 60 / 92
at = lambda n: [e for e in ev if e['type'] == n]
E1 = lambda n, k=0: at(n)[k]['t']
DOR = ['D', 'E', 'F', 'G', 'A', 'B', 'C']
M = []
# opening: airy bowed vibraphone + a low cello pedal; a chime on "Britain's highest mountain"
M += [(0.0, 'vibraphone_bowed', 'A5', 4.4, .3, .25, .7), (0.3, 'vibraphone_bowed', 'D5', 4.2, .28, -.25, .6), (0.0, 'cellos', 'D2', 7.0, .42, 0, .7),
      (E1('chime', 0), 'hand_chimes', 'G5', 2.5, .55, .3, .9)]
ig = E1('ignite', 0)
for j, p in enumerate(['D3', 'F3', 'A3', 'C4', 'E4', 'A4']): M.append((ig - .1 + j * BEAT / 2, 'harp', p, 2.5, .5, -.3 + .12 * j, .75))
M += [(E1('chime', 1), 'hand_chimes', 'D5', 2.5, .55, -.2, .9), (ig, 'cellos', 'D2', 6.0, .4, -.2, .6), (ig, 'contrabass', 'D1', 6.0, .4, .2, .5)]
# the rising sea: pizzicato pulse + a spiccato ostinato that climbs one step per 200 m
r1 = E1('rise', 0); k1400 = E1('land', 1)
t = r1; k = 0
while t < 26.0:
    M.append((t, 'contrabass_pizz', ['D1', 'A1', 'D2', 'A1'][k % 4], .5, .6 + .1 * (k % 4 == 0), 0, 1.0)); t += BEAT; k += 1
def level_at(tt):     # same shape as LEVEL() between rise and 1,400 (linear enough for the ostinato's step)
    if tt <= r1: return 0
    if tt >= k1400: return 1400
    k1000 = E1('land', 0)
    return 1000 * min(1, (tt - r1) / (k1000 - r1)) if tt < k1400 - .6 else 1000 + 400 * (tt - (k1400 - .6)) / .6
t = r1; k = 0
while t < 25.6:
    step = min(7, int(level_at(t) / 200)); deg = DOR[step % 7]; octv = 2 + (step >= 6) * 0
    M.append((t, 'cellos_spic', f'{deg}{3 if step >= 5 else 2}', BEAT / 2 * .9, .5 + .1 * (k % 4 == 0), .2 * ((k % 2) * 2 - 1), .9)); t += BEAT / 2; k += 1
for e in at('land'): M += [(e['t'], 'timpani', 'D2' if e['t'] < 17 else 'A2', 2.5, .85, 0, 1.1), (e['t'], 'horn_stac', 'D3', .6, .7, -.1, .8)]
for e, p in zip(at('tick2'), ['A5', 'D6']): M.append((e['t'], 'glockenspiel', p, 1.2, .5, .2, .8))
M += [(E1('chime', 2), 'hand_chimes', 'A5', 3.0, .6, 0, 1.0), (E1('chime', 2), 'vibraphone', 'D5', 2.5, .45, -.2, .7)]
# the extremes: low bowed pedal, then a horn swell for the summit
M += [(26.0, 'cellos', 'D2', 6.2, .42, -.2, .7), (26.0, 'vibraphone_bowed', 'F4', 3.6, .25, .2, .5)]
pk = E1('swell'); M += [(pk - .3, 'horn', 'D3', 2.8, .6, -.15, .9), (pk - .3, 'horn', 'A3', 2.8, .5, .15, .8), (pk, 'glockenspiel', 'D6', 1.5, .4, .3, .6)]
# history: frame drum on downbeats, a descending cello line; timpani on the years
d2 = E1('drain', 0)
for j, p in enumerate(['D2', 'C2', 'A#1', 'A1', 'D2']): M.append((d2 + j * 2.8, 'cellos', p, 2.9, .42, -.15, .7))
for e in at('drum'): M += [(e['t'], 'timpani', 'D2', 2.0, .7, 0, .9)]
M += [(E1('ignite', 1), 'hand_chimes', 'E6', 2.5, .45, .3, .7)]
# ending: the sea rises once more; resolve on D (major third: the sky)
rs = E1('resolve')
for j, p in enumerate(['D3', 'A3', 'D4', 'F#4', 'A4', 'E5', 'F#5']): M.append((rs + j * BEAT / 2, 'harp', p, 3.5, .5, -.3 + .1 * j, .75))
M += [(rs, 'horn', 'D3', 4.5, .45, -.1, .7), (rs, 'horn', 'F#3', 4.5, .4, .1, .6), (rs, 'cellos', 'D2', 7.5, .45, 0, .7), (rs, 'contrabass', 'D1', 7.5, .45, 0, .6),
      (rs + 1.3, 'hand_chimes', 'F#5', 3.5, .5, .2, .8), (rs + 2.6, 'hand_chimes', 'A5', 3.5, .45, -.2, .7), (rs + 3.9, 'vibraphone_bowed', 'D5', 4.0, .28, 0, .5)]
music = S.render(M, dur=DUR, master=False)
fd = S.hit('frame_drum', 'large', .85)
for tt in [ig, E1('land', 0), k1400, d2 + 2.8, d2 + 5.6, d2 + 8.4, d2 + 11.2, rs]: add(music, fd, tt, .7, 0)
music = S.room(music, size=.55, mix=.22)
def suck(buf, t0, t1, depth=.08):
    a, b = int(t0 * SR), int(t1 * SR); w = np.ones(len(buf)); f = int(.04 * SR); w[a:b] = depth; w[a - f:a] = np.linspace(1, depth, f); w[b:b + f] = np.linspace(depth, 1, f); buf *= w[:, None]
suck(music, E1('suck'), k1400 - .02)
music[-int(1.6 * SR):] *= np.linspace(1, 0, int(1.6 * SR))[:, None] ** 1.5

# foley
fx = np.zeros((N, 2), np.float32)
def tick(v=1.0): d = .05; x = bp(noise(d), 2500, 6500) * env_exp(d, .006); return (x / np.abs(x).max() * v).astype(np.float32)
for e in at('tick'): add(fx, tick(.45), e['t'], .4, 0)
def shimmer(d=1.8):
    tt = t_(d); x = sum(np.sin(2 * np.pi * f * tt + 3 * np.sin(2 * np.pi * 7 * tt)) for f in (1760, 2217, 2637)) * np.exp(-tt * 1.6) * np.minimum(1, tt / .05); return (x / 3 * .5).astype(np.float32)
for e in at('ignite'): add(fx, shimmer(), e['t'], .3, 0)
def sub(f=48, d=1.2, v=1.0): tt = t_(d); return (np.sin(2 * np.pi * (f + 30 * np.exp(-tt * 12)) * tt) * np.exp(-tt * 3.2) * v).astype(np.float32)
for e in at('land'): add(fx, sub(46, 1.4, .8), e['t'], .8, 0)
add(fx, whoosh(.9, .9), E1('whoosh') - .3, .4, 0)
# water: a swell that rises with the sea (filtered noise; cutoff climbs), and a falling sweep when it drains
tt = np.arange(N) / SR
def wbed(t0, t1, up=True):
    n = int((t1 - t0) * SR); x = brown((t1 - t0) + .01)[:n]; x = x / np.abs(x).max()
    k = np.linspace(0, 1, n) if up else np.linspace(1, 0, n)
    y = np.zeros(n, np.float32)
    for i, (a, b) in enumerate(zip(np.linspace(0, n, 9)[:-1].astype(int), np.linspace(0, n, 9)[1:].astype(int))):
        y[a:b] = lp(x[a:b], 300 + 2200 * k[(a + b) // 2]) * (.25 + .75 * k[(a + b) // 2])
    return y
add(fx, wbed(r1, k1400 + .4), r1, .35, -.2); add(fx, wbed(E1('rise', 1), E1('rise', 1) + 3.0), E1('rise', 1), .3, .2)
add(fx, wbed(d2, d2 + 1.5, False), d2, .3, 0)
# air: thin mountain wind throughout, a little stronger in the low shots
air = hp(brown(DUR), 150); air = lp(air, 2600); air = air / np.abs(air).max()
lvl = .045 + .03 * ((tt > 25.5) & (tt < 32.5)) * (1 + .5 * np.sin(2 * np.pi * .21 * tt))
air = (air * lvl).astype(np.float32); fx[:, 0] += air; fx[:, 1] += np.roll(air, 300)

# voice
vdir = os.path.join(HERE, 'out', 'voice'); voice = np.zeros((N, 2), np.float32); venv = np.zeros(N, np.float32)
for lid, t0 in re.findall(r"\['(l\d+)', ([\d.]+),", open(os.path.join(HERE, 'timeline.js')).read()):
    x, sr = sf.read(os.path.join(vdir, lid + '.wav'), dtype='float32'); x = x if x.ndim == 1 else x.mean(1)
    if sr != SR:
        import soxr; x = soxr.resample(x, sr, SR).astype(np.float32)
    x = compress(x / max(1e-6, np.abs(x).max()) * .9, thr=.22, ratio=3.2)
    a = int(float(t0) * SR); b = min(N, a + len(x)); voice[a:b, 0] += x[:b - a]; voice[a:b, 1] += x[:b - a]; venv[a:b] = 1
k = int(.12 * SR); venv = np.convolve(venv, np.ones(k) / k, 'same'); duck = (1 - .5 * venv)[:, None]
rms = lambda x: float(np.sqrt(np.mean(x ** 2)) + 1e-9)
vr = rms(voice[venv > .5]); mr = rms(music[venv > .5]); music *= (vr / mr) * 10 ** (-7 / 20)
mix = voice + music * duck + fx
mix = hp(mix.T, 32).T.astype(np.float32); mix = limit(mix / max(1e-6, np.abs(mix).max()) * .89, .89)
sf.write(os.path.join(HERE, 'out', 'mix.wav'), mix, SR, subtype='PCM_24')
print('mix', DUR, 's; voice over music (dB)', round(20 * np.log10(vr / rms(music[venv > .5] * duck[venv > .5])), 1))
