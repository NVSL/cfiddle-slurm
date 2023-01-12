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

        
class SlurmRunnerDelegate(SubprocessDelegate):

    def execute(self, command, runner):
        self._command = command
        self._runner = runner
        log.debug(f"{self._command=}")
        log.debug(f"{os.getcwd()=}")
        self.run_in_slurm()

    def run_in_slurm(self):
        with tempfile.NamedTemporaryFile(mode="wb", dir=".") as f:
            self.slurm_state = f.name
            pickle.dump(self, f)
            f.flush()
            self._invoke_slurm()

    def _invoke_slurm(self):
        self._invoke_shell(["salloc", "cfiddle-slurm-run-shared-directory.sh", self.slurm_state, ".", str(log.root.level)])
            
    def run(self):
        super().execute(self._command, self._runner)

    def _invoke_shell(self, cmd):
        try:
            log.debug(f"Executing in {' '.join(cmd)=}")
            r = subprocess.run(cmd, check=True, capture_output=True)
            log.debug(f"{r.stdout.decode()}")
            log.debug(f"{r.stderr.decode()}")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Slurm execution failed: {e} {e.stdout.decode()} {e.stderr.decode()}")
        
class _SlurmRunnerDelegate(SubprocessDelegate):

    def __init__(self, *argc,**kwargs):
        super(SubprocessDelegate, self).__init__(*argc, **kwargs)
    
    def execute(self, command, runner):

        self._command = command
        self._runner = runner
        self._files_to_take = self._collect_input_filenames(runner)
    
        log.debug(f"{self._command=}")
        log.debug(f"{self._files_to_take=}")

        with tempfile.NamedTemporaryFile(dir=".", suffix=".zip") as inputs_file:
            with tempfile.NamedTemporaryFile(dir=".", suffix=".zip") as outputs_file:
                #self._inputs_file = inputs_file.name
                #self._outputs_file = outputs_file.name
                log.debug(f"{os.getcwd()=}")
                #log.debug(f"{self._inputs_file=}")
                #log.debug(f"{self._outputs_file=}")
                #self._create_inputs_file()
                self.run_in_slurm()
                #self._unzip_outputs_file()

    def run_in_slurm(self):
        with tempfile.TemporaryDirectory(dir=".") as d:
            self.slurm_state = os.path.join(d, "delegate.pickle")
            with open(self.slurm_state, "wb") as out:
                pickle.dump(self, out)
            self._invoke_slurm()

    def _invoke_slurm(self):
        self._invoke_shell(["salloc", "cfiddle-slurm-run-shared-directory.sh", self.slurm_state, ".", str(log.root.level)])
            
    def run(self):
        #self._execution_directory = os.getcwd() #execution_directory
        #log.debug(f"{self._execution_directory=}")
        #self._unzip_inputs_file()
        self._do_execution()
        #self._collect_outputs()
        #self._create_outputs_file()

    def _create_inputs_file(self):
        log.debug(f"Copying input files")
        zip_files(self._files_to_take, self._inputs_file)
        
    # def _copy_inputs_file(self):
    #     dst_path = os.path.join(self._execution_directory, "inputs.zip")
    #     log.debug(f"Copying inputs file {self._inputs_file} to {dst_path}.")
    #     shutil.copyfile(self._inputs_file, dst_path)

    # def _unzip_inputs_file(self):
    #     unzip_files(self._inputs_file, directory=self._execution_directory)

    def _do_execution(self):
        super().execute(self._command, self._runner)

    # def _collect_outputs(self):
    #     output_files = self._collect_output_filenames(self._runner)
    #     output_files = sum([glob.glob(f, recursive=True) for f in output_files], [])

    #     self._output_files = list(set(output_files))
    #     log.debug(f"{self._output_files=}")
        
    # def _create_outputs_file(self):
    #     zip_files(self._output_files, self._outputs_file)

    # def _copy_back_outputs_file(self):
    #     src_path = os.path.join(self._execution_directory, "outputs.zip")
    #     log.debug(f"Copying inputs file  {src_path} to {self._outputs_file}.")
    #     shutil.copyfile(src_path, self._outputs_file)

    # def _unzip_outputs_file(self):
    #     unzip_files(self._outputs_file, ".")

    def _collect_input_filenames(self, runner):
        files = set(runner.compute_input_files())
        
        for invocation in runner.get_invocations():
            files = files.union(invocation.compute_input_files())

        return list(files)

    def _collect_output_filenames(self, runner):
        files = set(runner.compute_output_files())

        for invocation in runner.get_invocations():
            files = files.union(invocation.compute_output_files())

        return list(files)


    def _invoke_shell(self, cmd):
        try:
            log.debug(f"Executing in {' '.join(cmd)=}")
            r = subprocess.run(cmd, check=True, capture_output=True)
            log.debug(f"{r.stdout.decode()}")
            log.debug(f"{r.stderr.decode()}")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Slurm execution failed: {e} {e.stdout.decode()} {e.stderr.decode()}")
        
class TestingSlurmRunnerDelegate(SlurmRunnerDelegate):

    def __init__(self, *argc,**kwargs):
        super(SlurmRunnerDelegate, self).__init__(*argc, **kwargs)
        self._run_in_slurm = False

    def run_in_slurm(self):
        super().run()

class SlurmRunnerDelegateUnshared(SlurmRunnerDelegate):

    def _invoke_slurm(self):
        state_file = os.path.abspath(self.slurm_state)
        inputs_file = os.path.abspath(self._inputs_file)
        with tempfile.TemporaryDirectory() as hideout:
            with working_directory(hideout):
                self._invoke_shell(["salloc", "cfiddle-slurm-run-unshared-directory.sh", state_file, inputs_file, str(log.root.level)])

        
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
        slurm_delegate.run()
    except: #CFiddleException as e:
        raise
        
