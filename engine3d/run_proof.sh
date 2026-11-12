#!/bin/bash
# Render every shot of a multi-shot 3D video, then assemble.
cd /home/user/autostudio
D=out/proof3d
for i in 0 1 2 3; do
  env=$(python3 -c "import json;print(json.load(open('$D/timing.json'))['shots'][$i]['env'])")
  mkdir -p $D/s$i; rm -f $D/s$i/f_*.jpg
  /home/user/bpyenv/bin/python engine3d/${env}3d.py $D/timing.json $i $D/s$i > $D/s$i.log 2>&1
  echo "shot $i done $(ls $D/s$i | grep -c f_)"
done
