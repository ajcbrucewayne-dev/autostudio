"""Step 1 (normal python): voice lines -> wav + timing/amplitude json for Blender."""
import json, os, sys
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engine"))
import render
FPS3 = 24
def main(script, out):
    sc = json.load(open(script)); os.makedirs(out, exist_ok=True)
    t = 0.4; segs = []; parts = []
    for ln in sc["lines"]:
        a = render.tts(ln["say"], ln.get("voice", "am_puck"), ln.get("speed", 1.1))
        segs.append({"t0": t, "t1": t + len(a) / render.SR, "say": ln["say"], "act": ln.get("act", ""),
                     "words": render.word_times(ln["say"], t, len(a) / render.SR)})
        parts.append((t, a)); t += len(a) / render.SR + ln.get("pause", 0.35)
    total = t + 0.6; n = int(total * render.SR); vo = np.zeros(n, np.float32)
    for t0, a in parts: s0 = int(t0 * render.SR); vo[s0:s0 + len(a)] += a
    music = render.synth_music("whatif", n) * 0.08
    mix = vo + music; mix = mix / np.abs(mix).max() * 0.9
    sf.write(os.path.join(out, "audio.wav"), mix, render.SR)
    nf = int(total * FPS3); hop = render.SR // FPS3
    env = np.array([np.sqrt(np.mean(vo[i * hop:(i + 1) * hop] ** 2)) for i in range(nf)])
    env = np.clip(env / np.percentile(env[env > 0], 90), 0, 1)
    json.dump({"fps": FPS3, "frames": nf, "segs": segs, "amp": env.round(3).tolist()}, open(os.path.join(out, "timing.json"), "w"))
    print("frames", nf, "sec", round(total, 1))
if __name__ == "__main__": main(sys.argv[1], sys.argv[2])
