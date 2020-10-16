#!/usr/bin/env python

import fuse
from pyduofern.duofern_stick import DuofernStickThreaded

from lib.duofernstick_wrapper import ShutterStickWrapper
from lib.duofern_fs import DuofernFs


def main():
    usage="""
Userspace hello example

""" + fuse.Fuse.fusage

    
    stick = DuofernStickThreaded(serial_port="/dev/duofernstick", config_file_json="./pyduofern-config.json")
    stick._initialize()
    stick.start()

    server = DuofernFs(
        ShutterStickWrapper(stick), 
        version="%prog " + fuse.__version__,
        usage=usage,
        dash_s_do='setsingle'
    )

    server.parse(errex=1)
    server.main()

if __name__ == '__main__':
    main()