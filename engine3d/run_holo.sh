#!/bin/bash
# render all beats of the hologram storybook, then assemble
set -e
cd /home/user/autostudio
for i in 0 1 2 3 4 5; do
  mkdir -p out/holo/s$i; rm -f out/holo/s$i/f_*.jpg
  /home/user/bpyenv/bin/python engine3d/holo3d.py out/holo/timing.json $i out/holo/s$i > out/holo/render$i.log 2>&1
done
python3 engine3d/assemble.py out/holo /home/user/moon_hologram_storybook.mp4
