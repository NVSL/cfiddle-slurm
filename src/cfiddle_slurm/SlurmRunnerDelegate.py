import sys
import json
import zipfile
import os
import tempfile
import glob
import logging as log
import subprocess
import click
import pickle

from contextlib import contextmanager
import shutil

from cfiddle.Runner import SubprocessDelegate

# Slurm Tasks
# 3. Execute command in remote execution directory.
# 4. Execute command in local directory

# SSH tasks w/shared home directory
# 3. Execute command in remote execution directory.
# 4. Execute command in local directory

# SSH tasks w/o shared home directory
# 1. Build inputs zip file
# 2. Create remote temp directory
# 3. scp inputs file
# 4. Execute command in remote execution directory.
# 5. Execute command in local directory (in this process, in a separate process, in a docker container, with sudo in a docker container)
# 6. Build outputs zip file
# 7. scp outputs file back
# 8. Copy back outputs zip file and unpack locally

# native tasks
# 4. Execute command in local directory
#   1. in this process
#   2. in a separate process
#   3. in a docker container
#   4. with sudo in a docker container


class SlurmRunnerDelegate(SubprocessDelegate):

    def execute(self, command, runner):
        self._command = command
        self._runner = runner
        log.debug(f"{self._command=}")
        log.debug(f"{os.getcwd()=}")

        with tempfile.NamedTemporaryFile(mode="wb", dir=".") as slurm_state:
            pickle.dump(self, slurm_state)
            slurm_state.flush()
            self._invoke_slurm(slurm_state.name)

    def _invoke_slurm(self, slurm_state):
        self._invoke_shell(["salloc", "cfiddle-slurm-run-shared-directory.sh", slurm_state, ".", str(log.root.level)])
            
    def subprocess_run(self):
        super().execute(self._command, self._runner)

    def _invoke_shell(self, cmd):
        try:
            log.debug(f"Executing in {' '.join(cmd)=}")
            r = subprocess.run(cmd, check=True, capture_output=True)
            log.debug(f"{r.stdout.decode()}")
            log.debug(f"{r.stderr.decode()}")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Shell execution failed: {e} {e.stdout.decode()} {e.stderr.decode()}")
    
class ShellDelegate(SubprocessDelegate):

    def __init__(self, shell_command=None, single_string=True, *argc, **kwargs):
        super().__init__()
        if shell_command is None:
            shell_command = ["bash", "-c"]
        self._shell_command = shell_command
        self._single_string = single_string

    def execute(self, command, runner):
        if  False and self._single_string:
            super().execute(self._shell_command + [" ".join(command)], runner)
        else:
            super().execute(self._shell_command + command, runner)


class SudoDelegate(ShellDelegate):

    def __init__(self, user, *argc, **kwargs):
        super().__init__(["sudo", "--preserve-env=PATH", "--preserve-env=LD_LIBRARY_PATH", "-u", user], single_string=False, *argc, **kwargs)

def SudoSelfDelegate():
    return SudoDelegate(user=pwd.getpwuid(os.getuid()).pw_name)

class DifferentDirectoryDelegate(SubprocessDelegate):

    def __init__(self, execution_directory=None, *argc,**kwargs):
        super().__init__(*argc, **kwargs)
        self._execution_directory = execution_directory
        
    def execute(self, command, runner):

        self._runner = runner
        log.debug(f"{command=}")

        with tempfile.NamedTemporaryFile(suffix=".zip") as inputs_file:
            with tempfile.NamedTemporaryFile(suffix=".zip") as outputs_file:
                self._inputs_file = inputs_file.name
                self._outputs_file = outputs_file.name
                log.debug(f"{os.getcwd()=}")
                log.debug(f"{self._inputs_file=}")
                log.debug(f"{self._outputs_file=}")
                self._collect_inputs()
                self._create_inputs_file()
                log.debug(f"{self._execution_directory=}")
                with tempfile.TemporaryDirectory() if self._execution_directory is None else nullcontext(self._execution_directory) as d:
                    with working_directory(d):
                        self._unzip_inputs_file()
                        super().execute(command, self._runner)
                        self._collect_outputs()
                        self._create_outputs_file()                        
                self._unzip_outputs_file()

    def _collect_inputs(self):
        files = set(self._runner.compute_input_files())
        
        for invocation in self._runner.get_invocations():
            files = files.union(invocation.compute_input_files())

        self._input_files = list(files)
        log.debug(f"{self._input_files=}")

    def _create_inputs_file(self):
        log.debug(f"Copying input files")
        zip_files(self._input_files, self._inputs_file)
        
    def _unzip_inputs_file(self):
        unzip_files(self._inputs_file, directory=".")

    def _collect_outputs(self):
        output_files = self._collect_output_filenames()
        output_files = sum([glob.glob(f, recursive=True) for f in output_files], [])

        self._output_files = list(set(output_files))
        log.debug(f"{self._output_files=}")
      
    def _collect_output_filenames(self):
        files = set(self._runner.compute_output_files())

        for invocation in self._runner.get_invocations():
            files = files.union(invocation.compute_output_files())

        return list(files)

    def _create_outputs_file(self):
        zip_files(self._output_files, self._outputs_file)

    def _unzip_outputs_file(self):
        unzip_files(self._outputs_file, ".")

class GenericSelfContainedDelegate(SubprocessDelegate):

    def __init__(self, function_delegator, *argc, **kwargs):
        super().__init__(*argc, **kwargs)
        self._function_delegator = function_delegator

    def execute(self, command, runner):        
        self._command = command
        self._runner = runner
        self.pre_execute()
        self._function_delegator.invoke(self, "do_execution")
        self.post_execute()

    def pre_execute(self):
        self._inputs_file = io.BytesIO()
        self._collect_inputs()
        self._create_inputs_file()

    def do_execution(self):
        self._unzip_inputs_file()
        super().execute(self._command, self._runner)
        self._collect_outputs()
        self._outputs_file = io.BytesIO()
        self._create_outputs_file()                     

    def post_execute(self):
        self._unzip_outputs_file()

    def _collect_inputs(self):
        files = set(self._runner.compute_input_files())
        
        for invocation in self._runner.get_invocations():
            files = files.union(invocation.compute_input_files())

        self._input_files = list(files)
        log.debug(f"{self._input_files=}")

    def _create_inputs_file(self):
        log.debug(f"Copying input files")
        zip_files(self._input_files, self._inputs_file)
        
    def _unzip_inputs_file(self):
        unzip_files(self._inputs_file, directory=".")

    def _collect_outputs(self):
        output_files = self._collect_output_filenames()
        output_files = sum([glob.glob(f, recursive=True) for f in output_files], [])

        self._output_files = list(set(output_files))
        log.debug(f"{self._output_files=}")
      
    def _collect_output_filenames(self):
        files = set(self._runner.compute_output_files())

        for invocation in self._runner.get_invocations():
            files = files.union(invocation.compute_output_files())

        return list(files)

    def _create_outputs_file(self):
        zip_files(self._output_files, self._outputs_file)

    def _unzip_outputs_file(self):
        unzip_files(self._outputs_file, ".")


from delegate_function import BaseDelegate, TemporaryDirectoryDelegate as Foo
def TestGenericSelfContainedDelegate():
    return GenericSelfContainedDelegate(Foo(subdelegate=BaseDelegate()))


class DockerRunnerDelegate(SubprocessDelegate):

    def execute(self, command, runne):
        self._command = command
        self._runner = runner
        log.debug(f"{self._command=}")
        log.debug(f"{os.getcwd()=}")

        with tempfile.TemporaryDirectory() as d:
            with tempfile.NamedTemporaryFile(mode="wb", dir = d) as f:
                pickle.dump(self, f)
                f.flush()
                self._invoke_docker(working_directory=d, state_file=f.name)


    def _invoke_docker(self, working_directory, state_file):
        self._invoke_shell(["docker", "run",
                            "-w", working_directory,
                            "--mount type=bind,source=/tmp,dst=/tmp",
                            image,
                            "cfiddle-slurm-run-shared-directory.sh", slurm_state, ".", str(log.root.level)])
            

    def subprocess_run(self):
        super().execute(self._command, self._runner)

class TemporaryDirectoryDelegate(DifferentDirectoryDelegate):
    def __init__(self, *argc,**kwargs):
        self._temp_directory = tempfile.TemporaryDirectory()
        super().__init__(self._temp_directory.name, *argc, **kwargs)


#class SlurmRunnerDelegateUnshared(SlurmRunnerDelegate):
#
#    def _invoke_slurm(self):
#        state_file = os.path.abspath(self.slurm_state)
#        inputs_file = os.path.abspath(self._inputs_file)
#        with tempfile.TemporaryDirectory() as hideout:
#            with working_directory(hideout):
#                self._invoke_shell(["salloc", "cfiddle-slurm-run-unshared-directory.sh", state_file, inputs_file, str(log.root.level)])

        
def zip_files(file_list, output):
    zipf = zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED)
    manifest = {}
    for f in file_list:
        manifest[f] = collect_file_metadata(f)
        log.debug(f"Added {f} to {output}")
        zipf.write(f,f)
    manifest_string = json.dumps(manifest, sort_keys=True, indent=4)
    zipf.writestr(".__manifest__", manifest_string)
    zipf.close()

    
def unzip_files(zf, directory, delete_manifest=True):
    paths =[]
    with zipfile.ZipFile(zf) as zipf:
        zipf.extractall(directory)
        with open(os.path.join(directory, ".__manifest__"), "r") as m:
            manifest = json.load(m)
            for f, d in manifest.items():
                log.debug(f"Extracted {f} from {zf} to {directory}")
                path = os.path.join(directory, f)
                if os.path.exists(path):
                    os.utime(path, times=(d['st_atime'], d['st_mtime']))
                    os.chmod(path, d['st_mode'])
        if delete_manifest:
            os.unlink(os.path.join(directory, ".__manifest__"))


def collect_file_metadata(path):
    r = os.stat(path)
    return dict(st_mode=r.st_mode,
                st_mtime=r.st_mtime,
                st_atime=r.st_atime)


@contextmanager
def working_directory(path):
    here = os.getcwd()
    try:
        os.chdir(path)
        yield path
    finally:
        os.chdir(here)

@click.command()
@click.option('--slurm-state', required=True, type=click.File("rb"), help="File with a pickled slurm state in it.")
@click.option('--log-level', default=None, type=int, help="Verbosity level for logging.")
@click.option("--cwd", default=".", help="Directory to run in")
#@click.option('--results', "results", required=True, type=click.File("wb"), help="File to deposit the results in.")
def slurm_runner_delegate_run(slurm_state, log_level, cwd):
    import platform
    if log_level is not None:
        log.root.setLevel(log_level)
    log.debug(f"Executing in delegate process on {platform.node()}")
    with working_directory(cwd):
        do_slurm_runner_delegate_run(slurm_state)
    
def do_slurm_runner_delegate_run(slurm_state):
    slurm_delegate = pickle.load(slurm_state)
    try:
        slurm_delegate.subprocess_run()
    except: #CFiddleException as e:
        raise
        
