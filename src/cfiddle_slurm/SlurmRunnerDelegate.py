import json
import zipfile
import os
import tempfile
import glob
import logging as log

from contextlib import contextmanager
import shutil

from cfiddle.Runner import SubprocessDelegate

        
class SlurmRunnerDelegate(SubprocessDelegate):
    def execute(self, command, runner):


        self._command = command
        self._runner = runner
        self._files_to_take = self._collect_input_filenames(runner)
    
        log.debug(f"{self._command=}")
        log.debug(f"{self._files_to_take=}")

        with tempfile.NamedTemporaryFile(suffix=".zip") as inputs_file:
            with tempfile.NamedTemporaryFile(suffix=".zip") as outputs_file:
                with tempfile.TemporaryDirectory() as execution_directory:
                    self._execution_directory = execution_directory
                    self._inputs_file = inputs_file.name
                    self._outputs_file = outputs_file.name
                    log.debug(f"{os.getcwd()=}")
                    log.debug(f"{self._execution_directory=}")
                    log.debug(f"{self._inputs_file=}")
                    log.debug(f"{self._outputs_file=}")

                    self._create_inputs_file()
                    self._copy_inputs_file()
                    with working_directory(self._execution_directory):
                        self._unzip_inputs_file()
                        self._do_execution()
                        self._collect_outputs()
                        self._create_outputs_file()
                    self._copy_back_outputs_file()
                    self._unzip_outputs_file()

    def _create_inputs_file(self):
        zip_files(self._files_to_take, self._inputs_file)
        
    def _copy_inputs_file(self):
        shutil.copyfile(self._inputs_file, os.path.join(self._execution_directory, "inputs.zip"))

    def _unzip_inputs_file(self):
        unzip_files(self._inputs_file, directory=self._execution_directory)

    def _do_execution(self):
        super().execute(self._command, self._runner)

    def _collect_outputs(self):
        output_files = self._collect_output_filenames(self._runner)
        output_files = sum([glob.glob(f, recursive=True) for f in output_files], [])

        self._output_files = list(set(output_files))
        log.debug(f"{self._output_files=}")
        
    def _create_outputs_file(self):
        zip_files(self._output_files, "outputs.zip")

    def _copy_back_outputs_file(self):
        shutil.copyfile(os.path.join(self._execution_directory, "outputs.zip"), self._outputs_file)

    def _unzip_outputs_file(self):
        unzip_files(self._outputs_file, ".")

    def _collect_input_filenames(self, runner):
        files = set(runner.compute_required_files())
        
        for invocation in runner.get_invocations():
            files = files.union(invocation.compute_required_files())

        return list(files)

    def _collect_output_filenames(self, runner):
        files = set(runner.compute_output_files())

        for invocation in runner.get_invocations():
            files = files.union(invocation.compute_output_files())

        return list(files)


        
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

