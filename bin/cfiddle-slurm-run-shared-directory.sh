#!/usr/bin/bash

srun cfiddle-slurm-runner-delegate-run --slurm-state $1 --cwd $2 --log-level $3

