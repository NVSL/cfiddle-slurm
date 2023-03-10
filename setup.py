from setuptools import setup, find_packages
import subprocess
import os, sys
import platform

with open("VERSION") as f:
    version = f.read()
    
setup(
    name="cfiddle_slurm",
    version=version.strip(),
    package_data={
        'cfiddle_slurm': ['VERSION'],
    },
    install_requires = ["cfiddle"],
    description="Support for running CFiddle functions via Slurm",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',      # Define that your audience are developers
        'Intended Audience :: Education',
        'License :: OSI Approved :: MIT License',   # Again, pick a license
        'Programming Language :: Python :: 3', 
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    url="https://github.com/NVSL/cfiddle-slurm",
    author="Steven Swanson",
    author_email="swanson@cs.ucsd.edu",
    packages=find_packages('src'),
    package_dir={'': 'src'},
    entry_points={
        'console_scripts' :[
            'cfiddle-slurm-runner-delegate-run=cfiddle_slurm.SlurmRunnerDelegate:slurm_runner_delegate_run'
        ]
    },
    scripts=['bin/cfiddle-slurm-run-shared-directory.sh',
             'bin/cfiddle-slurm-run-unshared-directory.sh'
             ]
)


