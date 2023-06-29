from contextlib import contextmanager
from cfiddle import *

from  .SlurmRunnerDelegate import SlurmRunnerDelegate, DifferentDirectoryDelegate, TemporaryDirectoryDelegate, ShellDelegate, SudoDelegate

all=["SlurmRunnerDelegate",
     "slurm_execution",
     #"SlurmRunnerDelegateUnshared",
     "DifferentDirectoryDelegate",
     "TemporaryDirectoryDelegate",
     "ShellDelegate",
     "SudoDelegate"
    ]

@contextmanager
def slurm_execution():
    try:
        with cfiddle_config(RunnerDelegate_type=SlurmRunnerDelegate):
            yield
    finally:
        pass


