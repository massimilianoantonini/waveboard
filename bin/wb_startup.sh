#!/usr/bin/env bash

xterm -xrm '*hold: true' -geometry 132x8+0-1 -e "cd /home/widmapp/waveboard/bin; python3 wb_controller_ultra.py -m -p 2-sonde.json" &
