import tempfile
import glob
import os
from contextlib import contextmanager

from cfiddle import *
from cfiddle_slurm.SelfContainedExecutionMethod import TestSelfContainedDelegate
import pytest

@contextmanager
def working_directory(path):
    here = os.getcwd()
    try:
        os.chdir(path)
        yield path
    finally:
        os.chdir(here)


def _pristine_dir():
    with tempfile.TemporaryDirectory(dir=".") as cfiddle_dir:
        with cfiddle_config(CFIDDLE_BUILD_ROOT=cfiddle_dir):
            yield cfiddle_dir


@pytest.fixture(scope="module",
                params=[
                        TestSelfContainedDelegate,
                        ])
def setup(request):
    with cfiddle_config(RunnerDelegate_type=request.param):
        enable_debug()
        yield from _pristine_dir()

def test_file_list(setup):
    exe = build(code('extern "C" int foo() {return 4;}'))
    r = run(exe, "foo", extra_input_files=["empty_file"])
    assert len(r[0].invocation.compute_input_files()) == 2
    

def test_file_zip():

    from cfiddle_slurm.SelfContainedExecutionMethod import zip_files, unzip_files, collect_file_metadata
    
    with tempfile.TemporaryDirectory() as dst:
        files_to_zip = [x[:-1] if x[-1] == "/" else x for x in glob.glob("test_dir/**", recursive=True)]
        
        zip_files(files_to_zip, os.path.join(dst, "test.zip"))
        unzip_files(os.path.join(dst, "test.zip"), directory=dst)
        with working_directory(dst):
            unziped_files = glob.glob(f"**", recursive=True)
        assert set(unziped_files) == set(files_to_zip + ["test.zip"])

        for f in files_to_zip:
            original_metadata = collect_file_metadata(f)
            del original_metadata["st_atime"]
            restored_metadata = collect_file_metadata(os.path.join(dst, f))
            del restored_metadata["st_atime"]
            assert original_metadata == restored_metadata


def test_input_transfer(setup):
    exe = build(code(r"""
#include <iostream>
#include <fstream>
extern "C" int foo() {
    std::ifstream myfile;
    myfile.open ("number_file.in", std::ios::in);
    int k;
    myfile >> k;
    return k;
}

"""))
    r = run(exe, "foo", extra_input_files=["number_file.in"])
    assert r[0].return_value == 43

def test_output_transfer(setup):
    exe = build(code(r"""
#include <iostream>
#include <fstream>
extern "C" void foo() {
    std::ofstream myfile;
    myfile.open ("number_file.out");
    myfile << 42;

}

"""))
    r = run(exe, "foo", extra_output_files=["number_file.out"])
    with open("number_file.out") as f:
        assert int(f.read()) == 42;
    

def _test_slurm_execution(capfd):
    with slurm_execution():
        run(build(code(r"""
#include <unistd.h>
#include<iostream>  
  
extern "C" void go2()
{
        char hostbuffer[256];
        gethostname(hostbuffer, sizeof(hostbuffer));
        std::cerr << hostbuffer;
}
""")), "go2", arg_map())

        
