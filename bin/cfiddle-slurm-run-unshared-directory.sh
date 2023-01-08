#!/usr/bin/bash

set -xe

slurm_state=$1
shift
inputs_file=$1
shift
#cwd=$1
#shift
log_level=$1
shift

echo slurm_state=$slurm_state
echo inputs_file=$inputs_file
echo log_level=$log_level

srun rm -rf /tmp/foo
srun mkdir -p /tmp/foo
sbcast $slurm_state /tmp/foo/${slurm_state##*/}
sbcast $inputs_file /tmp/foo/${inputs_file##*/}
srun cfiddle-slurm-runner-delegate-run --slurm-state $slurm_state --cwd /tmp/foo --log-level $log_level

