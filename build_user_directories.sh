#!/usr/bin/bash -ex

rm -rf /home/test_fiddler
mkdir /home/test_fiddler
cp -a test_fiddler_home/.ssh /home/test_fiddler/.ssh
chown -R test_fiddler /home/test_fiddler

rm -rf /home/cfiddle
mkdir /home/cfiddle
chown -R cfiddle /home/cfiddle
