"""Svalbard mix: Kokoro voice (bm_lewis) at out/starts.json over Kevin MacLeod "Comfortable Mystery" (CC BY 3.0), ducked, plus a few hits."""
import json, subprocess, sys, numpy as np, soundfile as sf
sys.path.insert(0, '/root/lemo-opuscar')
from core.audio.sfx import SR, add, t_, noise, bp, lp, env_exp
DUR = 54.6; N = int(DUR * SR); ST = json.load(open('out/starts.json'))
mus = subprocess.run(['ffmpeg', '-v', 'error', '-i', '../assets/music/Comfortable_Mystery_(ISRC_USUAN1100287).mp3', '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'], capture_output=True).stdout
m = np.frombuffer(mus, np.float32).reshape(-1, 2).copy(); m = np.tile(m, (int(np.ceil(N / len(m))), 1))[:N]
m /= np.abs(m).max(); voice = np.zeros((N, 2), np.float32)
for k, t in ST.items():
    v, sr = sf.read(f'out/voice/{k}.wav', dtype='float32')
    if sr != SR: from scipy.signal import resample_poly; v = resample_poly(v, SR, sr, axis=0).astype(np.float32)
    v = v if v.ndim == 1 else v.mean(1); add(voice, v, t, .707, 0)
env = np.abs(voice[:, 0]); w = int(.25 * SR); c = np.concatenate([[0], np.cumsum(env > .01)]); i = np.arange(N); env = (c[np.minimum(i + w // 2, N)] - c[np.maximum(i - w // 2, 0)]) / w
duck = 1 - .35 * np.clip(env * 3, 0, 1); m *= (.22 * duck)[:, None]
m[:int(.4 * SR)] *= np.linspace(0, 1, int(.4 * SR))[:, None]; m[-int(2 * SR):] *= np.linspace(1, 0, int(2 * SR))[:, None]
fx = np.zeros((N, 2), np.float32)
def sub(f=46, d=1.4, v=1.0): tt = t_(d); return (np.sin(2 * np.pi * (f + 30 * np.exp(-tt * 12)) * tt) * np.exp(-tt * 3.2) * v).astype(np.float32)
def whoosh(d=.7): x = bp(noise(d), 400, 3000) * np.sin(np.pi * t_(d) / d) ** 2; return (x / np.abs(x).max() * .5).astype(np.float32)
def zip_(d=.25): x = bp(noise(d), 2000, 7000) * env_exp(d, .05); return (x / np.abs(x).max() * .4).astype(np.float32)
for t in [0.1, ST['l03'], ST['l06'], ST['l07'], ST['l08']]: add(fx, sub(), t, .55, 0)
for t in [ST['l02'] - .3, ST['l03'] - .6, ST['l05'] + 3.8, ST['l07'] + .6, ST['l07'] + 4.4]: add(fx, whoosh(), t, .35, 0)
for i in range(14): add(fx, zip_(), ST['l04'] + .3 + i * .26, .16, (i % 3 - 1) * .4)
for i in range(5): add(fx, zip_(), ST['l05'] + .3 + i * .22, .3, 0)
mix = voice + m + fx
mix /= max(1, np.abs(mix).max() / .95); sf.write('out/mix.wav', mix, SR); print('ok', len(mix) / SR)
