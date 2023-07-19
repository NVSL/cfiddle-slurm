from contextlib import contextmanager
from cfiddle import *

from  .SelfContainedExecutionMethod import SelfContainedExecutionMethod

all=["SelfContainedDelegate"]

@contextmanager
def slurm_execution():
    try:
        with cfiddle_config(RunnerDelegate_type=SelfContainedExecutionMethod):
            yield
    finally:
        pass


