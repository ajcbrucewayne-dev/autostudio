"""Free AI illustrations via Pollinations (no key). Same style + character sheet every time for consistency."""
import os, sys, time, urllib.parse, urllib.request
STYLE = ("Pixar style 3D animated movie still, cinematic lighting, soft volumetric light, rich colors, "
         "shallow depth of field, highly detailed, vertical composition")
LEO = ("Leo, a 9-year-old boy with dark curly hair, big brown eyes, light-brown skin, "
       "wearing a mustard-yellow hoodie and brown shorts")
def generate(scene, out, seed=7, with_leo=True, w=768, h=1344, model=None):
    prompt = f"{STYLE}, {LEO + ', ' if with_leo else ''}{scene}"
    q = {"width": w, "height": h, "seed": seed, "nologo": "true", "enhance": "false"}
    if model: q["model"] = model
    url = "https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt) + "?" + urllib.parse.urlencode(q)
    for i in range(4):
        try:
            data = urllib.request.urlopen(url, timeout=180).read()
            if len(data) > 5000: open(out, "wb").write(data); return out
        except Exception as e: print("retry", i, e, file=sys.stderr); time.sleep(5 * (i + 1))
    raise RuntimeError("image failed")
if __name__ == "__main__": print(generate(sys.argv[1], sys.argv[2]))
