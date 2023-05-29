#!/usr/bin/env bash

xterm -xrm '*hold: true' -geometry 132x8+0-1 -e "cd /home/widmapp/wb_controller/bin; python3 wb_controller_ultra.py" &
