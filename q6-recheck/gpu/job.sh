#!/bin/bash
#PBS -A <project>
#PBS -l walltime=01:00:00
#PBS -l filesystems=home:grand
#PBS -N q6-determinism
#PBS -j oe
W=$WORK/consensus/q6-recheck
export HF_HOME=$WORK/hf-cache HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 CUDA_VISIBLE_DEVICES=0
export VLLM_CACHE_ROOT=$W/vllm-cache-$(hostname) TORCHINDUCTOR_CACHE_DIR=$W/inductor-cache-$(hostname)
PY=$W/env/bin/python
export CC=/usr/bin/gcc CXX=/usr/bin/g++  # Polaris defaults to nvc++, which inductor cannot drive
OUT=$W/out/${OUTNAME:-$(hostname | cut -d. -f1)-$PBS_JOBID}
mkdir -p $OUT; cd $W
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv > $OUT/gpu.txt
for mode in ${MODES:-hf vllm vllm-bi}; do for r in 1 2; do
  RUN=$r timeout 1200 $PY $W/gen.py $mode $OUT > $OUT/log_${mode}_$r.txt 2>&1; echo "$mode $r rc=$?"
done; done
