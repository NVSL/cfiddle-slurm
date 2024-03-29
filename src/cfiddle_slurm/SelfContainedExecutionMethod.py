import io
import json
import platform
import zipfile
import os
import glob
import logging as log

from cfiddle.Runner import SubprocessExecutionMethod

class SelfContainedExecutionMethod(SubprocessExecutionMethod):
    """
    This delegate encapsulates all the data need to invoke and return the results of a cfiddle function, 
    including the input and output files.  This means that if the input or outputs are large, you may run into trouble, 
    since they are all stored in memory.

    This allows for very flexible delegation of execution (E.g., to another machine via ssh).  
    The delegation mechanism are provided by the :code:`delegate_function` package.  And the delegate should be passed to the constructor.
    """
    def __init__(self, function_delegator, *argc, **kwargs):
        super().__init__(*argc, **kwargs)
        self._function_delegator = function_delegator

    def execute(self, command, runner):        
        self._command = command
        self._runner = runner
        self._pre_execute()
        self._function_delegator.invoke(self, "_do_execution")
        self._post_execute()

    def _pre_execute(self):
        self._inputs_file = io.BytesIO()
        self._collect_inputs()
        self._create_inputs_file()

    def _do_execution(self):
        self._unzip_inputs_file()
        super().execute(self._command, self._runner)
        self._collect_outputs()
        self._outputs_file = io.BytesIO()
        self._create_outputs_file()                     

    def _post_execute(self):
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


from delegate_function import SSHDelegate, SubprocessDelegate, TemporaryDirectoryDelegate

def TestSelfContainedDelegate():
    return SelfContainedExecutionMethod(TemporaryDirectoryDelegate(subdelegate=SubprocessDelegate()))
