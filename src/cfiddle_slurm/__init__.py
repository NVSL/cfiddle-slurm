from contextlib import contextmanager
from cfiddle import *

from  .SlurmRunnerDelegate import SelfContainedDelegate

all=["SelfContainedDelegate", #SlurmRunnerDelegate",
 #    "slurm_execution",
     #"SlurmRunnerDelegateUnshared",
 #    "DifferentDirectoryDelegate",
  #   "TemporaryDirectoryDelegate",
#     "ShellDelegate",
#     "SudoDelegate"
    ]

@contextmanager
def slurm_execution():
    try:
        with cfiddle_config(RunnerDelegate_type=SlurmRunnerDelegate):
            yield
    finally:
        pass


