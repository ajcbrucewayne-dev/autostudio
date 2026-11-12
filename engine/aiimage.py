"""Free AI illustrations via Cloudflare Workers AI (FLUX.1 schnell, free daily allowance).

Env: CF_ACCOUNT_ID (not secret) + CF_API_TOKEN (secret, "Workers AI" permission).
python engine/aiimage.py "Leo looks up at the full moon in a misty forest" out.jpg
"""
import base64, json, os, sys, urllib.request

MODEL = os.environ.get("CF_IMAGE_MODEL", "@cf/black-forest-labs/flux-1-schnell")
# One fixed style + character sheet keeps every image looking like the same film.
STYLE = ("cinematic 3D animated film still, soft volumetric lighting, warm rim light, rich colors, shallow depth of field, "
         "vertical 9:16 composition, highly detailed, family animation movie style")
LEO = ("Leo, a curious 9-year-old boy with dark curly hair, big brown eyes, light-brown skin, freckles, "
       "wearing a mustard-yellow hoodie with a small white star and an orange cape-like raincoat")

def generate(scene, out_path, seed=7, steps=4, with_leo=True):
    acct, tok = os.environ["CF_ACCOUNT_ID"], os.environ["CF_API_TOKEN"]
    prompt = f"{STYLE}. {LEO + '. ' if with_leo else ''}{scene}"
    req = urllib.request.Request(f"https://api.cloudflare.com/client/v4/accounts/{acct}/ai/run/{MODEL}",
                                 json.dumps({"prompt": prompt, "steps": steps, "seed": seed}).encode(),
                                 {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=120))
    if not r.get("success", True): raise RuntimeError(r.get("errors"))
    open(out_path, "wb").write(base64.b64decode(r["result"]["image"]))
    return out_path

if __name__ == "__main__":
    print(generate(sys.argv[1], sys.argv[2]))
