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

def toPercentage(stringInput):
    numberValue = int(stringInput)
    if not 0 <= numberValue <= 100:
        raise ValueError()
    return numberValue

def toOnOffString(stringInput):
    if not stringInput in ['on', 'off']:
        raise ValueError()
    return stringInput


class ShutterStickWrapper:

    writeablePropertyValidators = {
        'sunMode':              toOnOffString,
        'position':             toPercentage,
        'sunPosition':          toPercentage,
        'ventilatingPosition':  toPercentage,
        'dawnAutomatic':        toOnOffString,
        'duskAutomatic':        toOnOffString,
        'manualMode':           toOnOffString,
        'sunAutomatic':         toOnOffString,
        'timeAutomatic':        toOnOffString,
        'ventilatingMode':      toOnOffString,
    }

    def __init__(self, duofernstick):
        self.duofernstick = duofernstick

    def deviceExists(self, deviceCode):
        return deviceCode in self.devices

    def deviceHasProperty(self, deviceCode, deviceProperty):
        return self.deviceExists(deviceCode) \
            and deviceProperty in self.devices[deviceCode]

    def getPropertyAsBytes(self, deviceCode, deviceProperty):
        return bytes(str(self.devices[deviceCode][deviceProperty]), 'utf-8')

    @property
    def devices(self):
        return self.duofernstick.duofern_parser.modules['by_code']

    @staticmethod
    def isWritable(property):
        return property in ShutterStickWrapper.writeablePropertyValidators

    @staticmethod
    def sanitizeInput(property, value):
        if not ShutterStickWrapper.isWritable(property):
            raise ValueError()
        return ShutterStickWrapper.writeablePropertyValidators[property](value)


class DuofernFs(fuse.Fuse):
    def __init__(self, duofernstick, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stick = duofernstick

    def getattr(self, path):
        st = MyStat()

        fsPath = DuofernFsPath(path)

        if fsPath.depth == 1:
            if fsPath.isRoot or self.stick.deviceExists(fsPath.deviceCode):
                st.st_mode = stat.S_IFDIR | 0o755
                st.st_nlink = 2
                return st

            return -errno.ENOENT

        if fsPath.depth == 2:
            if not self.stick.deviceExists(fsPath.deviceCode):
                return -errno.ENOENT

            if not self.stick.deviceHasProperty(fsPath.deviceCode, fsPath.deviceProperty):
                return -errno.ENOENT

            st.st_mode = stat.S_IFREG | 0o444
            if ShutterStickWrapper.isWritable(fsPath.deviceProperty):
                st.st_mode = st.st_mode | 0o222
            st.st_size = len(self.stick.getPropertyAsBytes(fsPath.deviceCode, fsPath.deviceProperty))
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
            for deviceCode in self.stick.devices.keys():
                yield fuse.Direntry(deviceCode)
            return

        if fsPath.deviceCode in self.stick.devices:
            for deviceProperty in self.stick.devices[fsPath.deviceCode].keys():
                yield fuse.Direntry(deviceProperty)

    def open(self, path, flags):
        fsPath = DuofernFsPath(path)

        if fsPath.depth != 2:
            return -errno.ENOENT

        if not self.stick.deviceHasProperty(fsPath.deviceCode, fsPath.deviceProperty):
            return -errno.ENOENT

        if not ShutterStickWrapper.isWritable(fsPath.deviceProperty):
            readWriteMask = os.O_RDONLY | os.O_WRONLY | os.O_RDWR
            if (flags & readWriteMask) != os.O_RDONLY:
                return -errno.EACCES

    def write(self, path, buf, offset):
        fsPath = DuofernFsPath(path)

        if fsPath.depth != 2:
            return -errno.ENOENT

        if not self.stick.deviceHasProperty(fsPath.deviceCode, fsPath.deviceProperty):
            return -errno.ENOENT

        if not ShutterStickWrapper.isWritable(fsPath.deviceProperty):
            return -errno.EACCES

        try:
            value = ShutterStickWrapper.sanitizeInput(fsPath.deviceProperty, buf.decode())
        except:
            return -errno.EINVAL

        self.stick.duofernstick.command(fsPath.deviceCode, fsPath.deviceProperty, value)

        return len(buf)


    def read(self, path, size, offset):
        fsPath = DuofernFsPath(path)

        if fsPath.depth != 2:
            return -errno.ENOENT

        if not self.stick.deviceHasProperty(fsPath.deviceCode, fsPath.deviceProperty):
            return -errno.ENOENT

        return self.stick.getPropertyAsBytes(fsPath.deviceCode, fsPath.deviceProperty)


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