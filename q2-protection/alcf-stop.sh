#!/bin/bash
# Stop all run_alcf.py processes of this user.
pids=$(ps -u $USER -o pid=,args= | awk '$2=="python3" && $3=="run_alcf.py" {print $1}')
[ -n "$pids" ] && kill $pids
