#!/usr/bin/env python

from pyduofern.duofern_stick import DuofernStickThreaded

import os, stat, errno
# pull in some spaghetti to make this stuff work without fuse-py being installed
try:
    import _find_fuse_parts
except ImportError:
    pass
import fuse


if not hasattr(fuse, '__version__'):
    raise RuntimeError("your fuse-py doesn't know of fuse.__version__, probably it's too old.")

fuse.fuse_python_api = (0, 2)

hello_path = '/hello'
hello_str = b'Hello World!\n'

class MyStat(fuse.Stat):
    def __init__(self):
        self.st_mode = 0
        self.st_ino = 0
        self.st_dev = 0
        self.st_nlink = 0
        self.st_uid = 0
        self.st_gid = 0
        self.st_size = 0
        self.st_atime = 0
        self.st_mtime = 0
        self.st_ctime = 0

class DuofernFs(fuse.Fuse):
    def __init__(self, duofernstick, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.duofernstick = duofernstick

    def getattr(self, path):
        st = MyStat()

        pathElements = path[1:].split('/')

        if len(pathElements) == 1:
            [stickCode] = pathElements

            if path == '/' or self.stickExists(stickCode):
                st.st_mode = stat.S_IFDIR | 0o755
                st.st_nlink = 2
                return st

            return -errno.ENOENT

        if len(pathElements) == 2:
            writeableProperties = [
                "sunMode",
                "position",
                "sunPosition",
                "ventilatingPosition",
                "dawnAutomatic",
                "duskAutomatic",
                "manualMode",
                "sunAutomatic",
                "timeAutomatic",
                "ventilatingMode"
            ]
            [stickCode, stickProperty] = pathElements

            if not self.stickExists(stickCode):
                return -errno.ENOENT

            if not self.stickHasProperty(stickCode, stickProperty):
                return -errno.ENOENT

            st.st_mode = stat.S_IFREG | 0o444
            if stickProperty in writeableProperties:
                st.st_mode = st.st_mode | 0o222
            st.st_nlink = 2
            return st

        return -errno.EIO


    def readdir(self, path, offset):
        yield fuse.Direntry('.')
        yield fuse.Direntry('..')

        pathElements = path[1:].split('/')

        if len(pathElements) == 1:
            [stickCode] = pathElements

            if stickCode == '':
                for stickCode in self._sticks.keys():
                    yield fuse.Direntry(stickCode)

            elif stickCode in self._sticks:
                for stickProperty in self._sticks[stickCode].keys():
                    yield fuse.Direntry(stickProperty)

    def open(self, path, flags):
        if path != hello_path:
            return -errno.ENOENT

        accmode = os.O_RDONLY | os.O_WRONLY | os.O_RDWR
        if (flags & accmode) != os.O_RDONLY:
            return -errno.EACCES

    def read(self, path, size, offset):
        if path != hello_path:
            return -errno.ENOENT

        slen = len(hello_str)
        if offset < slen:
            if offset + size > slen:
                size = slen - offset
            buf = hello_str[offset:offset+size]
        else:
            buf = b''
        return buf

    def stickExists(self, stickCode):
        return stickCode in self._sticks

    def stickHasProperty(self, stickCode, stickProperty):
        return self.stickExists(stickCode) \
            and stickProperty in self._sticks[stickCode]

    @property
    def _sticks(self):
        return self.duofernstick.duofern_parser.modules['by_code']


def main():
    usage="""
Userspace hello example

""" + fuse.Fuse.fusage

    
    stick = DuofernStickThreaded(serial_port="/dev/duofernstick", config_file_json="./pyduofern-config.json")
    stick._initialize()
    stick.start()

    server = DuofernFs(
        stick, 
        version="%prog " + fuse.__version__,
        usage=usage,
        dash_s_do='setsingle'
    )

    server.parse(errex=1)
    server.main()

if __name__ == '__main__':
    main()