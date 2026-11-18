"""Score + foley + narration for "The Town You Can't Drive To" → out/mix.wav. F# mixolydian, 100 bpm. Cue map: TREATMENT.md §5.
Instruments: VSCO 2 CE and VCSL (CC0). Voice: Kokoro bm_lewis."""
import os, re, sys, json
import numpy as np, soundfile as sf
LIB = os.environ.get('LIB', '/root/lemo-opuscar'); sys.path.insert(0, LIB)
from core.audio import sampler as S
from core.audio.sfx import SR, add, limit, compress, noise, brown, lp, hp, bp, whoosh, env_exp, t_
HERE = os.path.dirname(os.path.abspath(__file__))
EV = json.load(open(os.path.join(HERE, 'events.json'))); DUR = EV['dur']; ev = EV['ev']; N = int(DUR * SR)
S.seed(5); BEAT = .6
at = lambda n: [e for e in ev if e['type'] == n]
E1 = lambda n, k=0: at(n)[k]['t']
M = []
# hook: a high bowed shimmer while the line ignites, a low hit when the tip lights
M += [(0.0, 'vibraphone_bowed', 'C#6', 3.8, .3, .3, .7), (0.2, 'vibraphone_bowed', 'F#5', 3.6, .26, -.3, .6)]
for e in at('hit'): M += [(e['t'], 'timpani', 'F#2', 2.6, .85, 0, 1.1), (e['t'], 'horn_stac', 'F#2', .6, .8, -.1, .9), (e['t'], 'cellos', 'F#2', 3.5, .5, 0, .7)]
for e in at('chime'): M.append((e['t'], 'hand_chimes', S.name(e.get('note', 78)), 2.5, .55, .2, .9))
for e, p in zip(at('tick2'), ['C#6', 'F#6']): M.append((e['t'], 'glockenspiel', p, 1.2, .45, -.2, .7))
# 1846: frame drum + low strings; the line flashes again
y46 = E1('drum', 0)
M += [(y46, 'timpani', 'C#2', 2.2, .7, 0, .9), (y46, 'cellos', 'F#2', 7.0, .45, -.2, .7), (y46, 'contrabass', 'F#1', 7.0, .45, .2, .6), (y46 + .5, 'vibraphone_bowed', 'A#4', 6.0, .25, .2, .5)]
for j, p in enumerate(['F#3', 'A#3', 'C#4', 'E4', 'F#4']): M.append((E1('ignite', 1) + j * BEAT / 2, 'harp', p, 2.0, .5, -.3 + .15 * j, .7))
# the drive: a pizzicato road pulse and a plucked ostinato; a chime at each border
dv = E1('drive'); t = dv; k = 0
while t < 39.6:
    M.append((t, 'contrabass_pizz', ['F#1', 'C#2', 'E2', 'C#2'][k % 4], .5, .6 + .1 * (k % 4 == 0), 0, 1.0))
    M.append((t + BEAT / 2, 'violins_pizz', ['F#4', 'A#4', 'C#5', 'E5', 'C#5', 'A#4'][k % 6], .3, .45, .25 * ((k % 2) * 2 - 1), .7)); t += BEAT; k += 1
for e, p in zip(at('xing'), ['C#6', 'F#6']): M += [(e['t'], 'hand_chimes', p, 2.4, .6, 0, 1.0)]
# four crossings: four glockenspiel notes as the counter lands
c4 = E1('count')
for j, p in enumerate(['F#5', 'A#5', 'C#6', 'F#6']): M.append((c4 - .2 + j * .32, 'glockenspiel', p, 1.0, .55, -.3 + .2 * j, .8))
# 2020: everything stops; a single drum; then a thin pedal
y20 = E1('slam')
M += [(y20, 'timpani', 'F#2', 3.0, .9, 0, 1.2), (y20 + .2, 'cellos', 'F#2', 5.0, .4, 0, .6), (E1('drum', 1), 'timpani', 'C#2', 2.0, .6, 0, .8)]
# the question: resolve on F# major with harp and horns
rs = E1('resolve')
for j, p in enumerate(['F#3', 'C#4', 'F#4', 'A#4', 'C#5', 'E5', 'F#5']): M.append((rs + j * BEAT / 2, 'harp', p, 3.5, .5, -.3 + .1 * j, .75))
M += [(rs + .2, 'horn', 'F#3', 5.0, .45, -.1, .7), (rs + .2, 'horn', 'A#3', 5.0, .4, .1, .6), (rs, 'cellos', 'F#2', 7.5, .45, 0, .7),
      (rs + 2.4, 'hand_chimes', 'A#5', 3.5, .45, .2, .7), (rs + 4.0, 'vibraphone_bowed', 'F#5', 3.5, .28, 0, .5)]
music = S.render(M, dur=DUR, master=False)
fd = S.hit('frame_drum', 'large', .85)
for tt in [y46, y46 + 2.4, dv, dv + 2.4, y20, rs]: add(music, fd, tt, .7, 0)
music = S.room(music, size=.5, mix=.2)
def suck(buf, t0, t1, depth=.08):
    a, b = int(t0 * SR), int(t1 * SR); w = np.ones(len(buf)); f = int(.04 * SR); w[a:b] = depth; w[a - f:a] = np.linspace(1, depth, f); w[b:b + f] = np.linspace(depth, 1, f); buf *= w[:, None]
for e in at('suck'): suck(music, e['t'], e['t'] + .43)
# the closure: the music drops away for ~1.5 s after the slam
a, b = int((y20 + .35) * SR), int((y20 + 1.9) * SR); music[a:b] *= np.linspace(.35, 1, b - a)[:, None]
music[-int(1.6 * SR):] *= np.linspace(1, 0, int(1.6 * SR))[:, None] ** 1.5

fx = np.zeros((N, 2), np.float32)
def tick(v=1.0): d = .05; x = bp(noise(d), 2500, 6500) * env_exp(d, .006); return (x / np.abs(x).max() * v).astype(np.float32)
def shimmer(d=1.8):
    tt = t_(d); x = sum(np.sin(2 * np.pi * f * tt + 3 * np.sin(2 * np.pi * 7 * tt)) for f in (1760, 2217, 2637)) * np.exp(-tt * 1.6) * np.minimum(1, tt / .05); return (x / 3 * .5).astype(np.float32)
def sub(f=48, d=1.2, v=1.0): tt = t_(d); return (np.sin(2 * np.pi * (f + 30 * np.exp(-tt * 12)) * tt) * np.exp(-tt * 3.2) * v).astype(np.float32)
for e in at('ignite'):
    add(fx, shimmer(), e['t'], .3, 0)
    for i in range(16): add(fx, tick(.35), e['t'] + i * .13, .35, .6 - .08 * i)        # the line runs east → west
for e in at('hit'): add(fx, sub(46, 1.4, .8), e['t'], .8, 0)
add(fx, sub(42, 1.8, .9), y20, .9, 0)
for e in at('whoosh'): add(fx, whoosh(.9, .9), e['t'] - .3, .35, 0)
# sea and wind under everything (the coast)
tt = np.arange(N) / SR
sea = lp(brown(DUR), 900); sea = sea / np.abs(sea).max(); swell = .5 + .5 * np.sin(2 * np.pi * .11 * tt) ** 2
sea = (sea * (.05 + .03 * swell)).astype(np.float32); fx[:, 0] += sea; fx[:, 1] += np.roll(sea, 400)
air = hp(brown(DUR), 200); air = lp(air, 3000); air = (air / np.abs(air).max() * .03).astype(np.float32); fx[:, 0] += np.roll(air, 200); fx[:, 1] += air
# a soft engine/road bed during the drive
n = int((39.6 - dv) * SR); road = lp(noise(39.6 - dv)[:n], 220) * np.minimum(1, np.linspace(0, 6, n)) * np.minimum(1, np.linspace(6, 0, n))
add(fx, (road / np.abs(road).max() * .5).astype(np.float32), dv, .25, 0)

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
