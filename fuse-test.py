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

class DuofernFsPath:
    def __init__(self, path):
        self.path = path
        self.pathElements = path[1:].split('/')

    @property
    def isRoot(self):
        return self.path == '/'

    @property
    def depth(self):
        return len(self.pathElements)

    @property
    def deviceCode(self):
        return self.pathElements[0]

    @property
    def deviceProperty(self):
        return self.pathElements[1]


class DuofernFs(fuse.Fuse):
    def __init__(self, duofernstick, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.duofernstick = duofernstick

    def getattr(self, path):
        st = MyStat()

        fsPath = DuofernFsPath(path)

        if fsPath.depth == 1:
            if fsPath.isRoot or self.deviceExists(fsPath.deviceCode):
                st.st_mode = stat.S_IFDIR | 0o755
                st.st_nlink = 2
                return st

            return -errno.ENOENT

        if fsPath.depth == 2:
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

            if not self.deviceExists(fsPath.deviceCode):
                return -errno.ENOENT

            if not self.deviceHasProperty(fsPath.deviceCode, fsPath.deviceProperty):
                return -errno.ENOENT

            st.st_mode = stat.S_IFREG | 0o444
            if fsPath.deviceProperty in writeableProperties:
                st.st_mode = st.st_mode | 0o222
            st.st_size = len(self.getPropertyAsBytes(fsPath.deviceCode, fsPath.deviceProperty))
            st.st_nlink = 2
            return st

        return -errno.EIO


    def readdir(self, path, offset):
        yield fuse.Direntry('.')
        yield fuse.Direntry('..')

        fsPath = DuofernFsPath(path)

        if not fsPath.depth == 1:
            return

        if fsPath.isRoot:
            for deviceCode in self._devices.keys():
                yield fuse.Direntry(deviceCode)
            return

        if fsPath.deviceCode in self._devices:
            for deviceProperty in self._devices[fsPath.deviceCode].keys():
                yield fuse.Direntry(deviceProperty)

    def open(self, path, flags):
        fsPath = DuofernFsPath(path)

        if fsPath.depth != 2:
            return -errno.ENOENT

        if not self.deviceHasProperty(fsPath.deviceCode, fsPath.deviceProperty):
            return -errno.ENOENT

        accmode = os.O_RDONLY | os.O_WRONLY | os.O_RDWR
        if (flags & accmode) != os.O_RDONLY:
            return -errno.EACCES

    def read(self, path, size, offset):
        fsPath = DuofernFsPath(path)

        if fsPath.depth != 2:
            return -errno.ENOENT

        if not self.deviceHasProperty(fsPath.deviceCode, fsPath.deviceProperty):
            return -errno.ENOENT

        return self.getPropertyAsBytes(fsPath.deviceCode, fsPath.deviceProperty)

    def deviceExists(self, deviceCode):
        return deviceCode in self._devices

    def deviceHasProperty(self, deviceCode, deviceProperty):
        return self.deviceExists(deviceCode) \
            and deviceProperty in self._devices[deviceCode]

    def getPropertyAsBytes(self, deviceCode, deviceProperty):
        return bytes(str(self._devices[deviceCode][deviceProperty]), 'utf-8')

    @property
    def _devices(self):
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