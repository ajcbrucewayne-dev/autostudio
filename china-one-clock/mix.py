"""Score + foley + narration for "One Clock" → out/mix.wav (48 kHz stereo). Cue map: TREATMENT.md §6.
F# minor, 96 bpm (bar = 2.5 s). Hook in free time; grid from 3.9 s.
Instruments: VSCO 2 CE and VCSL (CC0). Voice: Kokoro bm_lewis."""
import os, re, sys, json
import numpy as np, soundfile as sf
LIB = os.environ.get('LIB', '/root/lemo-opuscar'); sys.path.insert(0, LIB)
from core.audio import sampler as S
from core.audio.sfx import SR, add, limit, compress, noise, brown, lp, hp, bp, thump, whoosh, click, env_exp, t_
HERE = os.path.dirname(os.path.abspath(__file__))
EV = json.load(open(os.path.join(HERE, 'events.json')))
DUR = EV['dur']; ev = EV['ev']; N = int(DUR * SR)
S.seed(7)
BAR = 2.5; B8 = BAR / 8; G0 = 3.9
def at(name): return [e for e in ev if e['type'] == name]
E1 = lambda name: at(name)[0]['t']

# ------------------------------------------------------------------ music
M = []                                    # (t, inst, pitch, dur, vel, pan[, gain])
# hook: a thin high bowed vibraphone + a pedal shimmer, nothing else until the hit
M += [(0.0, 'vibraphone_bowed', 'C#6', 3.2, .32, .25, .7), (0.4, 'vibraphone_bowed', 'F#5', 2.8, .28, -.25, .6)]
hit = E1('hit')
M += [(hit, 'timpani', 'F#2', 3.0, .95, 0, 1.3), (hit, 'horn_stac', 'F#2', .6, .9, -.1, 1.0), (hit, 'horn_stac', 'C#3', .6, .85, .1, .9),
      (hit, 'cellos', 'F#2', 3.4, .7, -.2, .8), (hit, 'contrabass', 'F#1', 3.4, .75, .2, .8)]
# width (3.9–10.0): low pizzicato pulse on quarters, cello pedal; a chime on "four hours"
for k in range(int((10.0 - G0) / (BAR / 4))):
    t = G0 + k * BAR / 4
    M.append((t, 'contrabass_pizz', ['F#1', 'F#2', 'C#2', 'F#2'][k % 4], .5, .62 + .1 * (k % 4 == 0), 0, 1.0))
M += [(G0, 'cellos', 'F#2', 6.3, .45, -.2, .7), (E1('chime'), 'hand_chimes', 'A5', 2.5, .6, .3, .9), (E1('chime') + .3, 'hand_chimes', 'E6', 2.2, .45, -.3, .7)]
# history (10.0–17.0): airy pad, then half a bar of silence and a horn swell under the amber ring
M += [(10.0, 'vibraphone_bowed', 'A4', 5.0, .4, -.3, .8), (10.0, 'vibraphone_bowed', 'C#5', 5.0, .35, .3, .7), (10.0, 'vibraphone_bowed', 'E5', 5.0, .3, 0, .6),
      (10.0, 'cellos', 'D2', 5.0, .4, -.1, .6)]
bj = E1('shimmer')
M += [(bj, 'horn', 'F#3', 2.6, .6, -.15, .9), (bj, 'horn', 'C#4', 2.6, .5, .15, .8), (bj + .1, 'cellos', 'F#2', 2.6, .5, 0, .7)]
for i, p in enumerate(['F#5', 'A5', 'C#6', 'E6', 'F#6']): M.append((bj + .15 + i * B8, 'glockenspiel', p, 1.2, .45, -.4 + .2 * i, .6))
# sweep (17.6–26.9): cello spiccato ostinato, 8ths then 16ths (acceleration by subdivision); harp; a chime per city at its dawn
pat = ['F#2', 'C#3', 'A2', 'C#3', 'F#2', 'E3', 'C#3', 'A2']; t = 17.6; k = 0
while t < 26.7:
    step = B8 if t < 22.4 else B8 / 2
    M.append((t, 'cellos_spic', pat[k % 8], step * .9, .55 + .12 * (k % 4 == 0) + .15 * (t > 22.4), .15 * ((k % 2) * 2 - 1), .95)); t += step; k += 1
for j in range(8): M.append((17.6 + j * BAR / 2, 'harp', ['F#3', 'A3', 'C#4', 'E4'][j % 4], 1.5, .45, -.3, .6))
scale = ['F#5', 'A5', 'B5', 'C#6', 'E6', 'F#6']
for e in at('dawn'): M.append((e['t'], 'hand_chimes', scale[e['i'] % 6], 2.4, .62, -.35 + .14 * e['i'], 1.0))
# landing on Kashgar: timpani, frame drum; then the pedal (28–34.4) with a glock note per clock
ten = E1('thump')
M += [(ten, 'timpani', 'C#3', 2.5, .85, 0, 1.1), (ten, 'cellos', 'F#2', 7.2, .45, -.2, .7), (ten, 'contrabass', 'F#1', 7.2, .5, .2, .7),
      (ten + .2, 'vibraphone_bowed', 'C#5', 6.8, .25, .3, .5)]
for e in at('glock'): M.append((e['t'], 'glockenspiel', S.name(e.get('note', 84)), 1.5, .55, -.2 if e['note'] > 80 else .2, .8))
# ending (34.6–43): resolve: harp arpeggio F#m → D(add9) → F#m, frame drum on the downbeat, chimes
r = E1('resolve')
M += [(r, 'cellos', 'D2', 4.0, .45, -.2, .7), (r + 4.0, 'cellos', 'F#2', 4.4, .45, -.2, .7), (r, 'contrabass', 'D1', 4.0, .45, .2, .6), (r + 4.0, 'contrabass', 'F#1', 4.4, .45, .2, .6)]
for j, p in enumerate(['D3', 'A3', 'E4', 'F#4', 'A4', 'E5']): M.append((r + j * B8, 'harp', p, 2.5, .5, -.3 + .1 * j, .7))
for j, p in enumerate(['F#3', 'C#4', 'F#4', 'A4', 'C#5', 'F#5']): M.append((r + 4.0 + j * B8, 'harp', p, 3.0, .5, -.3 + .1 * j, .7))
M += [(r + 4.0, 'hand_chimes', 'F#5', 3.5, .5, 0, .8), (r + 4.0, 'vibraphone_bowed', 'C#5', 4.2, .3, .2, .5)]
music = S.render(M, dur=DUR, master=False)
fd = S.hit('frame_drum', 'large', .9)
for tt, gn in [(hit, 1.0), (ten, .9), (r, .7), (r + 4.0, .8)]: add_at = add(music, fd, tt, gn * .9, 0)
music = S.room(music, size=.55, mix=.22)
# the suck-out before "Beijing time" (−25 dB for ~0.45 s) and before the hook hit
def suck(buf, t0, t1, depth=.06):
    a, b = int(t0 * SR), int(t1 * SR); w = np.ones(len(buf)); f = int(.04 * SR)
    w[a:b] = depth; w[a - f:a] = np.linspace(1, depth, f); w[b:b + f] = np.linspace(depth, 1, f); buf *= w[:, None]
suck(music, E1('suck'), bj - .02); suck(music, hit - .32, hit - .01, .15)
music[-int(1.4 * SR):] *= np.linspace(1, 0, int(1.4 * SR))[:, None] ** 1.5

# ------------------------------------------------------------------ foley + ambience
fx = np.zeros((N, 2), np.float32)
def tick(v=1.0):
    d = .05; x = bp(noise(d), 2500, 6500) * env_exp(d, .006); return (x / np.abs(x).max() * v).astype(np.float32)
for e in at('tick'): add(fx, tick(.5), e['t'], .5, 0)
def sub(f=48, d=1.2, v=1.0):
    tt = t_(d); return (np.sin(2 * np.pi * (f + 30 * np.exp(-tt * 12)) * tt) * np.exp(-tt * 3.2) * v).astype(np.float32)
add(fx, sub(46, 1.6, .9), hit, .9, 0); add(fx, sub(52, 1.3, .8), ten, .8, 0)
# ruler ratchet: dry ticks dividing as the line grows
rt = E1('ratchet'); n = 22
for i in range(n): add(fx, tick(.35 + .3 * i / n), rt + 1.3 * (1 - (1 - i / n) ** 1.6), .45, -.4 + .8 * i / n)
# electric shimmer under the ring
def shimmer(d=1.8):
    tt = t_(d); x = sum(np.sin(2 * np.pi * f * tt + 3 * np.sin(2 * np.pi * 7 * tt)) for f in (1760, 2217, 2637)) * np.exp(-tt * 1.6) * np.minimum(1, tt / .05)
    return (x / 3 * .5).astype(np.float32)
add(fx, shimmer(), bj, .35, 0)
# the rewind: a rising noise scan, reversed
rw = E1('rewind'); w = whoosh(.8, 1.0)[::-1].copy(); add(fx, hp(w, 400).astype(np.float32), rw, .5, 0)
add(fx, whoosh(1.0, .8), 17.7, .35, 0)
# air bed: thin high air that thickens in the low shots, mountain wind at Kashgar
air = hp(brown(DUR), 120); air = lp(air, 2400); air = air / np.abs(air).max()
tt = np.arange(N) / SR
lvl = .05 + .05 * np.clip((tt - 17.6) / 1.5, 0, 1) * (tt < 34.4) + .04 * ((tt > 26.5) & (tt < 34.4)) * (1 + .5 * np.sin(2 * np.pi * .23 * tt))
air = (air * lvl).astype(np.float32); fx[:, 0] += air; fx[:, 1] += np.roll(air, 300)

# ------------------------------------------------------------------ voice
vdir = os.path.join(HERE, 'out', 'voice'); voice = np.zeros((N, 2), np.float32); venv = np.zeros(N, np.float32)
tl = open(os.path.join(HERE, 'timeline.js')).read()
for lid, t0 in re.findall(r"\['(l\d+)', ([\d.]+),", tl):
    x, sr = sf.read(os.path.join(vdir, lid + '.wav'), dtype='float32'); x = x if x.ndim == 1 else x.mean(1)
    if sr != SR:
        import soxr; x = soxr.resample(x, sr, SR).astype(np.float32)
    x = compress(x / max(1e-6, np.abs(x).max()) * .9, thr=.22, ratio=3.2)
    a = int(float(t0) * SR); b = min(N, a + len(x)); voice[a:b, 0] += x[:b - a]; voice[a:b, 1] += x[:b - a]; venv[a:b] = 1
# duck: music −6 dB under the voice, with smooth edges
k = int(.12 * SR); venv = np.convolve(venv, np.ones(k) / k, 'same')
duck = (1 - .5 * venv)[:, None]

def rms(x): return float(np.sqrt(np.mean(x ** 2)) + 1e-9)
vr = rms(voice[venv > .5]); mr = rms(music[venv > .5])
music *= (vr / mr) * 10 ** (-7 / 20) * 1.0          # voice ~10 dB (RMS) over the music where it speaks
mix = voice + music * duck + fx * 1.0
# keep the low end in check (20–40 Hz)
mix = hp(mix.T, 32).T.astype(np.float32)
mix = limit(mix / max(1e-6, np.abs(mix).max()) * .89, .89)
os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
sf.write(os.path.join(HERE, 'out', 'mix.wav'), mix, SR, subtype='PCM_24')
json.dump(S.credits(sorted({m[1] for m in M} | {'frame_drum'})), open(os.path.join(HERE, 'out', 'instr_credits.json'), 'w'), indent=1)
print('mix', round(DUR, 2), 's; voice/music RMS dB', round(20 * np.log10(vr / rms(music[venv > .5] * duck[venv > .5])), 1))
