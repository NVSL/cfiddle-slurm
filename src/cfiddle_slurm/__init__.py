from contextlib import contextmanager
from cfiddle import *

from  .SlurmRunnerDelegate import SlurmRunnerDelegate, TestingSlurmRunnerDelegate

all=["SlurmRunnerDelegate",
     "slurm_execution",
     "TestingSlurmRunnerDelegate"]

@contextmanager
def slurm_execution():
    try:
        with cfiddle_config(RunnerDelegate_type=SlurmRunnerDelegate):
            yield
    finally:
        pass


