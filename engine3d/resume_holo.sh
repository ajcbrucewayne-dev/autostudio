#!/bin/bash
# resume the hologram render: skips frames already on disk, then mixes + assembles
set -e
cd /home/user/autostudio
for i in 0 1 2 3 4 5; do
  mkdir -p out/holo/s$i
  /home/user/bpyenv/bin/python engine3d/holo3d.py out/holo/timing.json $i out/holo/s$i >> out/holo/render$i.log 2>&1
done
python3 engine3d/mix_holo.py out/holo && python3 engine3d/assemble_holo.py out/holo /home/user/moon_hologram_storybook_v2.mp4
echo DONE
