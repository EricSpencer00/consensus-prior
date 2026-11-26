#!/bin/bash
# Release held jobs once their model download exits 0.
L=$WORK/consensus/dl-rep2.log
for p in "Qwen3.8-Flash-Next 208002" "Kimi-K2.6 208003"; do set -- $p
  until grep -q "/$1 " $L; do sleep 60; done
  grep -q "exit=0 .*/$1 " $L && qrls $2 && echo "released $2" || echo "download failed $1"
done
