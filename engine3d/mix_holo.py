"""Sound design for the hologram storybook: voice + music stems + synthesized SFX on cue -> audio_fx.wav
python3 mix_holo.py out/holo   (needs vo.wav, music.wav, timing.json, cues.json)
"""
import json, os, sys
import numpy as np, soundfile as sf

d = sys.argv[1]
vo, SR = sf.read(os.path.join(d, "vo.wav")); mus, _ = sf.read(os.path.join(d, "music.wav"))
T = json.load(open(os.path.join(d, "timing.json"))); C = json.load(open(os.path.join(d, "cues.json")))["cues"]
n = len(vo); fx = np.zeros(n); rng = np.random.default_rng(3)
tt = lambda dur: np.arange(int(dur * SR)) / SR

def put(sig, t, g=1.0):
    i = int(t * SR)
    if i < 0: sig, i = sig[-i:], 0
    if i >= n: return
    j = min(n, i + len(sig)); fx[i:j] += g * sig[:j - i]

def fade(x, a=0.01, r=0.05):
    x = x.copy(); na, nr = max(1, int(a * SR)), max(1, int(r * SR)); x[:na] *= np.linspace(0, 1, na); x[-nr:] *= np.linspace(1, 0, nr); return x

def smoothn(x, k): return np.convolve(x, np.ones(k) / k, mode="same")
def chirp(f0, f1, dur, expo=True):
    t = tt(dur); f = f0 * (f1 / f0) ** (t / dur) if expo else f0 + (f1 - f0) * t / dur
    return np.sin(2 * np.pi * np.cumsum(f) / SR)

def hum(t0, t1):
    t = tt(t1 - t0); x = 0.6 * np.sin(2 * np.pi * 55 * t) + 0.3 * np.sin(2 * np.pi * 110 * t) + 0.12 * np.sin(2 * np.pi * 220.7 * t)
    x *= 0.8 + 0.2 * np.sin(2 * np.pi * 0.7 * t); x += 0.15 * smoothn(rng.standard_normal(len(t)), 40)
    put(fade(x, 0.6, 0.5), t0, 0.05)

def build(t):  # holographic materialise: rising sweep + sparkles
    x = chirp(240, 1700, 0.9) * np.linspace(0.2, 1, int(0.9 * SR)) ** 2
    for _ in range(14):
        s = np.sin(2 * np.pi * rng.uniform(2500, 6500) * tt(0.12)) * np.exp(-tt(0.12) * 35); put(s, t + rng.uniform(0.2, 1.0), 0.05)
    put(fade(x, 0.02, 0.15), t, 0.09)

def swish(t, g=0.28, dur=0.45):  # page flip
    no = rng.standard_normal(int(dur * SR)); no = no - smoothn(no, 6)  # high-passed
    e = np.sin(np.linspace(0, np.pi, len(no))) ** 2; put(no * e, t, g * 0.5)

def thump(t, g=0.5):
    x = np.sin(2 * np.pi * np.cumsum(70 * np.exp(-tt(0.35) * 4)) / SR) * np.exp(-tt(0.35) * 11); put(x, t, g)

def glitch(t, dur=1.0):
    k = 0.0
    while k < dur:
        L = rng.uniform(0.015, 0.06); f = rng.uniform(150, 2500)
        put(np.sign(np.sin(2 * np.pi * f * tt(L))) * 0.7 + 0.3 * rng.standard_normal(int(L * SR)), t + k, 0.07 * (0.5 + k / dur))
        k += L + rng.uniform(0.0, 0.07)

def shatter(t):
    boom = np.sin(2 * np.pi * np.cumsum(55 * np.exp(-tt(1.8) * 1.2) + 18) / SR) * np.exp(-tt(1.8) * 2.2)
    put(boom, t, 0.75)
    no = rng.standard_normal(int(0.5 * SR)); put((no - smoothn(no, 4)) * np.exp(-tt(0.5) * 9), t, 0.35)
    for _ in range(40):  # glass tinkles
        L = rng.uniform(0.15, 0.6); s = np.sin(2 * np.pi * rng.uniform(2800, 8000) * tt(L)) * np.exp(-tt(L) * rng.uniform(8, 20))
        put(s, t + rng.uniform(0, 0.9), 0.05)

def derez(t): put(fade(chirp(1600, 120, 1.1)) * np.linspace(1, 0.3, int(1.1 * SR)), t, 0.08)

def wash(t0, t1):
    no = smoothn(rng.standard_normal(int((t1 - t0) * SR)), 30); e = np.sin(np.linspace(0, np.pi, len(no))); put(no * e, t0, 0.5)

def tape_rewind(t0, dur):
    t = tt(dur); f = 300 + 2600 * (t / dur) ** 0.6 + 200 * np.sin(2 * np.pi * 9 * t)
    x = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.3 + 0.5 * np.sin(2 * np.pi * np.cumsum(f * 0.5) / SR)
    put(fade(x, 0.02, 0.2) * 0.9, t0, 0.07); swish(t0, 0.35, 0.5)

# ---- cold open (audio timeline): glitch, shatter on "vanished", then tape rewind
sh = {s["beat"]: s for s in T["shots"]}; FPS = T["fps"]
cold, rew = sh["cold"], sh["rewind"]
tw = next(w[1] for w in cold["words"] if w[0].lower().startswith("vanish"))
glitch(tw - 1.0, 1.0); shatter(tw + 0.15)
r0 = rew["t0"] + 0.3; tape_rewind(r0 - 0.15, rew["frames"] / FPS)
# ---- main story
hum(C["beam_on"], C["beam_off"] + 0.5); thump(C["open"] + 1.15, 0.45); swish(C["open"] + 0.2, 0.3, 0.8)
for t in C["flips"]: swish(t)
for t in C["builds"]: build(t)
wash(C["tide"][0], C["tide"][1] + 0.8)
glitch(C["glitch"], 1.0); shatter(C["shatter"]); derez(C["derez"]); thump(C["close"] + 1.25, 0.6)
if "fizzle" in C: glitch(C["fizzle"], 0.7); derez(C["fizzle"] + 0.6)
if "drain" in C: wash(C["drain"][0], C["drain"][1])
if "spawn" in C:
    for _ in range(18):
        L = rng.uniform(0.1, 0.3); put(np.sin(2 * np.pi * rng.uniform(1800, 4200) * tt(L)) * np.exp(-tt(L) * 18), C["spawn"] + rng.uniform(0, 2.2), 0.04)

# ---- music: a bit louder, ducked hard right after each shatter (a beat of silence)
g = np.full(n, 0.11)
for ts in (tw + 0.15, C["shatter"]):
    i0 = int(ts * SR); i1 = min(n, i0 + int(1.6 * SR)); g[i0:i1] = 0.02
    k = min(n, i1 + int(0.8 * SR)); g[i1:k] = np.linspace(0.02, 0.11, k - i1)
g = smoothn(g, 800)
mix = vo + mus[:n] * g + fx
mix = np.tanh(mix / np.abs(mix).max() * 1.6) / np.tanh(1.6) * 0.92
sf.write(os.path.join(d, "audio_fx.wav"), mix.astype(np.float32), SR)
print("mixed", round(n / SR, 1), "s")
