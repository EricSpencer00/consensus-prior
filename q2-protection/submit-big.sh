#!/bin/bash
# Wait for each model download to finish, then submit its multi-node replication job.
cd $WORK/consensus/q2-protection
L=../dl-rep-models.log
sub() { # repo name nodes hours extra
  until grep -q "done $1\|FAIL $1" $L; do sleep 60; done
  grep -q "FAIL $1" $L && { echo "skip $2: download failed"; return; }
  qsub -l select=$3 -l walltime=$4:00:00 -N q2rep-$2 -v "MODEL=$1,NAME=$2,PP=$3,TAG=rep,PROMPTS=prompts_rep.jsonl,EXTRA=$5" job-mn.pbs
}
sub mistralai/Mistral-Medium-3.5-128B mistral-medium-3.5 2 10 "--max-tokens 32000 --max-len 36864"
sub Qwen/Qwen3.8-Flash-Next qwen3.8-flash-next 2 10 "--max-tokens 32000 --max-len 36864 --temperature 0.6"
sub moonshotai/Kimi-K2.6 kimi-k2.6 3 12 "--max-tokens 32000 --max-len 36864"
