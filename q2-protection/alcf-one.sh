#!/bin/bash
# Launch one ALCF endpoint run. Usage: alcf-one.sh CLUSTER MODEL NAME [WORKERS]
cd $WORK/consensus/q2-protection
nohup python3 run_alcf.py --cluster $1 --model $2 --name $3 --out out/$3.rep.jsonl --workers ${4:-24} >> out/alcf-$3.log 2>&1 < /dev/null &
