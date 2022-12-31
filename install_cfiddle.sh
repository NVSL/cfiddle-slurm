#!/usr/bin/env bash
set -ex

git clone http://github.com/NVSL/cfiddle
pip install cfiddle
(cd cfiddle; ./install_prereqs.sh)


