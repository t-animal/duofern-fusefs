#!/bin/bash

from pyduofern.duofern_stick import DuofernStickThreaded
import time

stick = DuofernStickThreaded(serial_port="/dev/duofernstick", config_file_json="./pyduofern-config.json") # by default looks for /dev/duofernstick
stick._initialize() # do some initialization sequence with the stick
stick.start() # start the stick in a thread so it keeps communicating with your blinds

time.sleep(10) # let it settle to be able to talk to your blinds.
# your code here
# this uses internal variables of the duofern parser module and likely I will wrap it in
# the future.

blindCode = "61e238"

print(stick.duofern_parser.modules['by_code'][blindCode]['position'])

# stick.command(blindCode, "up") # down the blind with code 1ff1d3

#stick.command(blindCode, "stop") # stop the blind with code 1ff1d3

#stick.command(blindCode, "position", 30) # set position of the blind with code 1ff1d3 to 30%
