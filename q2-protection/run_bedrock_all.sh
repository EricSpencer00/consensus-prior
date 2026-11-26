#!/bin/zsh
# Q2 full runs on Bedrock; resumes from existing out/*.full.jsonl.
cd "${0:A:h}"
P=~/.pyenv/versions/3.11.14/bin/python3
for x in zai.glm-5:glm-5 deepseek.v3.2:deepseek-v3.2 moonshot.kimi-k2-thinking:kimi-k2-thinking; do
  $P run_bedrock.py --model ${x%%:*} --name ${x##*:} --workers 16 --out out/${x##*:}.full.jsonl &
done
wait
