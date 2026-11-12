"""The daily job: for each channel, get N scripts (queued first, then AI-written), render, upload scheduled.

python engine/daily.py            # full run (needs secrets)
python engine/daily.py --no-upload
"""
import datetime as dt, json, os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render

ROOT = render.ROOT
PER_DAY = int(os.environ.get("VIDEOS_PER_CHANNEL", "2"))
# publish times in UTC (15:00, 19:00, 23:00 UTC = good US afternoon/evening slots)
SLOTS = ["15:00", "19:00", "23:00"]
CHANNELS = [c for c in os.environ.get("CHANNELS", "whatif,skits,darkhistory").split(",") if c]

def main(upload=True):
    state_dir = os.path.join(ROOT, "state"); os.makedirs(state_dir, exist_ok=True)
    tomorrow = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)).date()
    report = []
    for ch in CHANNELS:
        used_f = os.path.join(state_dir, f"used_{ch}.txt")
        used = open(used_f).read().splitlines() if os.path.exists(used_f) else []
        qdir = os.path.join(ROOT, "scripts", ch, "queue"); os.makedirs(qdir, exist_ok=True)
        queue = sorted(f for f in os.listdir(qdir) if f.endswith(".json"))[:PER_DAY]
        scripts = [(f, json.load(open(os.path.join(qdir, f)))) for f in queue]
        if len(scripts) < PER_DAY and os.environ.get("GEMINI_API_KEY"):
            import writer
            for s in writer.write(ch, PER_DAY - len(scripts), used):
                scripts.append((None, s))
        out_dir = os.path.join(ROOT, "out", str(tomorrow), ch); os.makedirs(out_dir, exist_ok=True)
        for i, (qf, s) in enumerate(scripts):
            name = f"{ch}_{tomorrow}_{i + 1}"
            os.makedirs(os.path.join(out_dir, "src"), exist_ok=True)
            path = os.path.join(out_dir, "src", name + ".json"); json.dump(s, open(path, "w"), ensure_ascii=False, indent=1)
            try:
                mp4 = render.render(path, out_dir)
            except Exception as e:
                report.append(f"FAILED render {name}: {e}"); continue
            meta = json.load(open(os.path.join(out_dir, name + ".json")))
            if upload and os.environ.get(f"YT_REFRESH_TOKEN_{ch.upper()}"):
                import youtube
                when = f"{tomorrow}T{SLOTS[i % len(SLOTS)]}:00Z"
                try:
                    vid = youtube.upload(ch, mp4, meta, when); report.append(f"{ch}: {meta['title']} -> {vid} @ {when}")
                except Exception as e:
                    report.append(f"FAILED upload {name}: {e}")
            else:
                report.append(f"{ch}: rendered {mp4}")
            used.append(s.get("topic", s.get("title", "")))
            if qf: shutil.move(os.path.join(qdir, qf), os.path.join(ROOT, "scripts", ch, os.path.basename(qf)))
        open(used_f, "w").write("\n".join(used))
    print("\n".join(report))
    open(os.path.join(ROOT, "out", "report.txt"), "w").write("\n".join(report))

if __name__ == "__main__":
    main(upload="--no-upload" not in sys.argv)
