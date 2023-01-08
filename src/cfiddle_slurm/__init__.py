from contextlib import contextmanager
from cfiddle import *

from  .SlurmRunnerDelegate import SlurmRunnerDelegate, TestingSlurmRunnerDelegate, SlurmRunnerDelegateUnshared

all=["SlurmRunnerDelegate",
     "slurm_execution",
     "TestingSlurmRunnerDelegate",
     "SlurmRunnerDelegateUnshared"]

@contextmanager
def slurm_execution():
    try:
        with cfiddle_config(RunnerDelegate_type=SlurmRunnerDelegate):
            yield
    finally:
        pass


