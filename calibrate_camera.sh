#!/bin/bash

# Open lxterminal and execute commands
lxterminal --command="/bin/bash -c '
cd /home/raspelbeere1991/projects/Dice/rasperry_run/
source myenv/bin/activate
python state_calibration.py
exec /bin/bash -i'"