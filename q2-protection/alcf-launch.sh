#!/bin/bash
# Launch ALCF endpoint runs. Usage: alcf-launch.sh WORKERS
WORKERS=${1:-24}; cd $WORK/consensus/q2-protection
for s in "minerva muse-spark-bf16 muse-spark" "minerva inkling-2-small inkling-2-small" "tara mistral-large-4 mistral-large-4" "tara inkling-bf16 inkling" "tara nemotron-3-ultra nemotron-3-ultra" "tara beam-1.0-fp8 beam-1.0"; do set -- $s
  nohup python3 run_alcf.py --cluster $1 --model $2 --name $3 --out out/$3.rep.jsonl --workers $WORKERS >> out/alcf-$3.log 2>&1 < /dev/null &
done
