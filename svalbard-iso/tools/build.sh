#!/bin/bash
set -e
while pgrep -f "ns-iso/tools/build.sh" >/dev/null; do sleep 30; done
P=/home/user/autostudio/svalbard-iso
cd /root/lemo-opuscar && rm -rf $P/out/video.mp4 $P/out/.video_segs-*
LEMO_ANGLE=swiftshader node core/render/video.mjs $P --fps 24 --workers 3 --size 1080x1920 --out $P/out/video.mp4 > $P/out/render_full.log 2>&1
cd $P
J=$(ffmpeg -hide_banner -i out/mix.wav -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
g(){ echo "$J" | python3 -c "import json,sys;print(json.load(sys.stdin)['$1'])"; }
ffmpeg -y -loglevel error -i out/mix.wav -af "loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=$(g input_i):measured_TP=$(g input_tp):measured_LRA=$(g input_lra):measured_thresh=$(g input_thresh):offset=$(g target_offset):linear=true,aresample=48000,apad,atrim=0:54.6" out/master.wav
ffmpeg -y -loglevel error -i out/video.mp4 -i out/master.wav -map 0:v -map 1:a -vf "noise=alls=3:allf=t" -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -t 54.6 -movflags +faststart the-doomsday-vault.mp4
ffmpeg -hide_banner -i the-doomsday-vault.mp4 -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I:|Peak:)"
ffmpeg -hide_banner -i the-doomsday-vault.mp4 -vf blackdetect=d=0.3 -an -f null - 2>&1 | grep blackdetect || true
cp the-doomsday-vault.mp4 /home/user/OTM_svalbard_vault.mp4
echo SV_DONE
