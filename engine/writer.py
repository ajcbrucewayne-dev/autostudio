"""AI scriptwriter: asks a free LLM (Google Gemini free tier) for new scripts in AutoStudio JSON format.

Needs env GEMINI_API_KEY (free at aistudio.google.com). Optional GEMINI_MODEL.
"""
import json, os, re, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
ANIMS = "pop, float, spin, shake, zoom, grow, pulse, slide_l, slide_r, fall, fade_in, fade_out, boom, shrink, drift (combine with +, e.g. pop+float)"

BRIEF = {
    "whatif": """Channel "What If?": 30-45 second science/space/body/world hypotheticals for a general audience.
Tone: curious, punchy, surprising. Every claim must be scientifically accurate; use "could"/"about" when uncertain.
Narrator only (speaker "N"). Host mascot "Blip" is drawn automatically; set scene "mood" to happy|shock|sad|angry|smug.
Visual items per scene: planets {"planet":"earth|moon|sun|mars|jupiter|venus|#hex","r":60-280,"x","y"},
emoji {"emoji":"🌊","s":150-500,"x","y"}, text {"text":"SHORT CAPS","size":80-140,"color":"#hex"}, counter {"counter":[from,to],"suffix":" km","size":120-220}.
Keep items in x 0.15-0.85, y 0.22-0.50. Scene "fx": "", "flash", "shake" or "flash+shake".""",
    "skits": """Channel "Blob Life": 12-25 second relatable comedy skits with two blob characters.
A = "Bo" (yellow, the relatable everyday person), B = pink (plays whatever the joke needs: brain, mom, boss, friend, phone, cat...).
Use speaker "A" or "B" each scene (rarely "N" for a narrator). Short spoken lines, fast timing, a clear punchline at the end.
Every scene needs: "set" one of bedroom|office|kitchen|school|street|phone|store|gym, "banner" (the setup, e.g. "ME vs MY BRAIN at 3AM", same in every scene, plain text NO emoji),
"mood" {"A":..,"B":..} each happy|shock|sad|angry|smug. Optional "props": [{"emoji":"📱","s":150-250,"x":0.3-0.7,"y":0.28-0.36,"anim":".."}], "fx", "pause" (seconds).
Humor must be clean, universal, no real people or brands.""",
    "darkhistory": """Channel "Dark Pages": 40-55 second true dark/strange history stories, cinematic narrator.
STRICTLY TRUE, well-documented events only. Say "accounts claim" for contested details. No gore descriptions, no real living people.
Narrator only (speaker "N"). Write years in words the narrator can read (e.g. "fifteen eighteen").
Every scene has "stamp" (short caps date/place/chapter text, max 24 chars, e.g. "JULY 1518 · STRASBOURG") and 1-3 emoji items
(rendered as sepia engravings) {"emoji":"🕯️","s":200-520,"x","y","anim":"fade_in+zoom"}; may use counter items. fx "flash" for shocking beats.""",
}

def example(channel):
    d = os.path.join(ROOT, "scripts", channel)
    f = sorted(x for x in os.listdir(d) if x.endswith(".json"))[0]
    return open(os.path.join(d, f)).read()

def prompt(channel, n, used):
    return f"""You write viral YouTube Shorts scripts for an animated channel. Output STRICT JSON only.
{BRIEF[channel]}
Animations ("anim"): {ANIMS}. Items may have "delay" (seconds after scene start).
Rules: hook in the very first line (curiosity or shock); 6-9 scenes; each "say" 4-25 words; end with a payoff or a loop back to the start.
Title max 70 chars with 1 emoji and #shorts. Description 1-2 lines plus 4 hashtags. 5-8 tags.
Do NOT reuse these topics: {', '.join(used[-150:]) or 'none'}.
Here is one complete example script in the required format:
{example(channel)}
Return a JSON object: {{"scripts": [ ...{n} new scripts, each with "channel":"{channel}", "topic" (2-5 words), "title","description","tags","scenes"... ]}}"""

def call_gemini(text):
    key = os.environ["GEMINI_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={key}"
    body = json.dumps({"contents": [{"parts": [{"text": text}]}],
                       "generationConfig": {"responseMimeType": "application/json", "temperature": 1.0}}).encode()
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, body, {"Content-Type": "application/json"})
            r = json.load(urllib.request.urlopen(req, timeout=180))
            return r["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            print("gemini retry", attempt, e, file=sys.stderr); time.sleep(20 * (attempt + 1))
    raise RuntimeError("Gemini failed")

def valid(s, channel):
    try:
        assert s["channel"] == channel and 4 <= len(s["scenes"]) <= 12 and s.get("title")
        for sc in s["scenes"]:
            assert isinstance(sc.get("say", ""), str) and len(sc.get("say", "")) < 260
            if channel == "skits": assert sc.get("speaker", "A") in "ABN"
        return True
    except Exception: return False

def write(channel, n, used):
    out = []
    for _ in range(3):
        raw = call_gemini(prompt(channel, n - len(out), used))
        raw = re.sub(r"^```(json)?|```$", "", raw.strip())
        for s in json.loads(raw).get("scripts", []):
            if valid(s, channel) and len(out) < n: out.append(s); used.append(s.get("topic", s["title"]))
        if len(out) >= n: break
    return out

if __name__ == "__main__":
    ch, n = sys.argv[1], int(sys.argv[2])
    print(json.dumps(write(ch, n, []), indent=1, ensure_ascii=False))
