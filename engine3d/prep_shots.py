"""Voice + timing for a multi-shot 3D video. Writes timing.json (per-shot frame counts, words) and audio.wav."""
import json, os, sys
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engine"))
import render
FPS3 = 24
def main(script, out):
    sc = json.load(open(script)); os.makedirs(out, exist_ok=True)
    voice, speed = render.CHANNELS["whatif"]["voices"]["N"]
    t = 0.3; shots = []; parts = []
    for s in sc["shots"]:
        a = render.tts(s["say"], voice, speed); t0 = t + 0.3
        dur = 0.3 + len(a) / render.SR + s.get("pause", 0.6)
        shots.append(dict(s, t0=t, frames=int(round(dur * FPS3)), words=render.word_times(s["say"], t0, len(a) / render.SR)))
        parts.append((t0, a)); t += shots[-1]["frames"] / FPS3
    n = int((t + 0.2) * render.SR); vo = np.zeros(n, np.float32)
    for t0, a in parts: vo[int(t0 * render.SR):int(t0 * render.SR) + len(a)] += a
    wh = render.whoosh("whatif"); sfx = np.zeros(n, np.float32)
    for s in shots[1:]:
        w0 = max(0, int(s["t0"] * render.SR) - len(wh) // 2); sfx[w0:w0 + len(wh)] += wh[:n - w0]
    mus = render.synth_music("whatif", n)
    sf.write(os.path.join(out, "vo.wav"), vo, render.SR); sf.write(os.path.join(out, "music.wav"), mus, render.SR)
    mix = vo + mus * 0.10 + sfx * 0.12
    sf.write(os.path.join(out, "audio.wav"), (mix / np.abs(mix).max() * 0.9).astype(np.float32), render.SR)
    json.dump({**{k: v for k, v in sc.items() if k != "shots"}, "fps": FPS3, "shots": shots}, open(os.path.join(out, "timing.json"), "w"), indent=1)
    print([(s["env"], s["frames"]) for s in shots], "total s", round(t, 1))
if __name__ == "__main__": main(sys.argv[1], sys.argv[2])
