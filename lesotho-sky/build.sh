#!/bin/sh
# One command: events → picture → score/foley/voice mix → master. Run from anywhere.
set -e
LIB=${LIB:-/root/lemo-opuscar}
HERE=$(cd "$(dirname "$0")" && pwd)
export LIB
[ -f "$LIB/core/render/video.mjs" ] || { echo "set LIB to the library folder"; exit 1; }
cd "$LIB"
"$LIB/.venv/bin/python" core/audio/sampler.py --need "$HERE/mix.py"
[ -f "$HERE/out/voice/dur.json" ] || "$LIB/.venv/bin/python" core/tts/tts.py "$HERE/lines.json" "$HERE/out/voice"
node core/render/events.mjs "$HERE" --size 1080x1920
LEMO_ANGLE=${LEMO_ANGLE:-swiftshader} node core/render/video.mjs "$HERE" --fps 24 --workers ${WORKERS:-3} --size 1080x1920 --out "$HERE/out/video.mp4"
"$LIB/.venv/bin/python" "$HERE/mix.py"
# mastering (ffmpeg 6 here: mux.sh needs 7) — two-pass loudnorm in mux.sh, then a brightening grade
sh core/render/mux.sh "$HERE/out/video.mp4" "$HERE/out/mix.wav" "$HERE/out/muxed.mp4" 24 1
ffmpeg -y -loglevel error -i "$HERE/out/muxed.mp4" -vf "curves=all='0/0.02 0.2/0.34 0.5/0.66 0.8/0.88 1/1',eq=saturation=1.12" -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a copy "$HERE/kingdom-in-the-sky.mp4"
"$LIB/.venv/bin/python" core/render/srt.py "$HERE/out/cues.json" "$HERE/subtitles_en.srt"
ffmpeg -y -loglevel error -ss 24.5 -i "$HERE/kingdom-in-the-sky.mp4" -frames:v 1 -q:v 2 "$HERE/poster.jpg"
