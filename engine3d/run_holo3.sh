#!/bin/bash
# v3 render (resumable: skips frames already on disk), then sound mix + assembly
set -e
cd /home/user/autostudio
D=out/holo3
for i in 0 1 2 3 4 5 6 7; do
  mkdir -p $D/s$i
  /home/user/bpyenv/bin/python engine3d/holo3d.py $D/timing.json $i $D/s$i >> $D/render$i.log 2>&1
done
python3 engine3d/mix_holo.py $D && python3 engine3d/assemble_holo.py $D /home/user/moon_hologram_storybook_v3.mp4
echo DONE
