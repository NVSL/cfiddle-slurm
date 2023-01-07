
import subprocess
import os
import pytest

@pytest.mark.skipif(os.geteuid() != 0,
                    reason="You aren't root")
def test_sudo():
    # this is tightly coupled to the dockerfile we use for testing.
    out = subprocess.check_output(['su', 'test_fiddler', '-c', 'sudo -u cfiddle /cse142L/cfiddle-slurm/bin/cfiddle-slurm-run.sh'])
    assert "7000" in out.decode()
    assert "(cfiddle)" in out.decode()
