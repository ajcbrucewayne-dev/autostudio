#!/bin/bash
# Monday video: waits for any running Moon render, then renders (resumable), mixes and assembles.
set -e
cd /home/user/autostudio
while pgrep -f run_holo3.sh > /dev/null; do sleep 60; done
D=out/sound
for i in 0 1 2 3 4 5 6; do
  mkdir -p $D/s$i
  /home/user/bpyenv/bin/python engine3d/holo_sound.py $D/timing.json $i $D/s$i >> $D/render$i.log 2>&1
done
python3 engine3d/mix_holo.py $D && python3 engine3d/assemble_holo.py $D /home/user/whatif_01_sound_walking_speed.mp4
echo DONE
