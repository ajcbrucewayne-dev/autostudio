#!/bin/bash
# Render the realistic North Sentinel film and mux it with the mastered soundtrack (shared with the isometric cut).
set -e
P=/home/user/autostudio/ns-real
cd /root/lemo-opuscar && rm -rf $P/out/video.mp4 $P/out/.video_segs-*
LEMO_ANGLE=swiftshader node core/render/video.mjs $P --fps 24 --workers 3 --size 1080x1920 --out $P/out/video.mp4 > $P/out/render_full.log 2>&1
cd $P && ffmpeg -y -loglevel error -i out/video.mp4 -i out/master.wav -map 0:v -map 1:a -vf "noise=alls=3:allf=t" -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -t 51.5 -movflags +faststart north-sentinel-3d.mp4
ffmpeg -hide_banner -i north-sentinel-3d.mp4 -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I:|Peak:)"
ffmpeg -hide_banner -i north-sentinel-3d.mp4 -vf blackdetect=d=0.3 -an -f null - 2>&1 | grep blackdetect || true
cp north-sentinel-3d.mp4 /home/user/OTM_north_sentinel_3d.mp4
echo NSR_DONE
