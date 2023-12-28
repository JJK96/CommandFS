#!/usr/bin/env python
import logging

import os
from os.path import realpath
from threading import RLock
from cachetools import TLRUCache, cachedmethod
from fuse import FUSE, FuseOSError, Operations, LoggingMixIn
from datetime import timedelta, datetime
from stat import S_IFDIR
from time import time
import subprocess 


class CachedRead:
    def __init__(self, root, command, cache_timeout):
        self.root = root
        self.command = command.split(' ')
        self.cache_timeout = cache_timeout
        self.cache = TLRUCache(ttu=self.my_ttu, timer=datetime.now, maxsize=100)

    def my_ttu(self, _key, value, now):
        return now + timedelta(seconds=self.cache_timeout)

    @cachedmethod(lambda self: self.cache)
    def read(self, path):
        print("Reading: ", path)
        with open(path, 'rb') as f:
            print("Running ", self.command)
            try:
                p = subprocess.run(self.command, stdin=f, capture_output=True)
            except Exception as e:
                print(e)
                return "Error"
            return p.stdout


class CommandFS(Operations):

    def __init__(self, root, command, cache_timeout):
        self.root = realpath(root)
        print(self.root)
        self.reader = CachedRead(self.root, command, cache_timeout)

    def __call__(self, op, path, *args):
        return super().__call__(op, self.root + path, *args)

    def getattr(self, path, fh=None):
        st = os.lstat(path)
        result = {key: getattr(st, key) for key in (
            'st_atime', 'st_ctime', 'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_uid', 'st_size'
        )}
        if not (result['st_mode'] & S_IFDIR):
            result['st_size'] = len(self.reader.read(path))
        return result

    def open(self, path, flags):
        fh = os.open(path, flags) << 1
        return fh

    def read(self, path, size, offset, fh):
        data = self.reader.read(path)
        val = data[offset:offset + size]
        return val

    def readdir(self, path, fh):
        print("Listing dir: ", path)
        return ['.', '..'] + os.listdir(path)

    def release(self, path, fh):
        return os.close(fh >> 1)

    def statfs(self, path):
        stv = os.statvfs(path)
        return dict((key, getattr(stv, key)) for key in (
            'f_bavail', 'f_bfree', 'f_blocks', 'f_bsize', 'f_favail',
            'f_ffree', 'f_files', 'f_flag', 'f_frsize', 'f_namemax'
        ))

    getxattr = None

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("src")
    parser.add_argument("dst")
    parser.add_argument("command")
    parser.add_argument("--cache-timeout", default=10, help="Timeout for the cache in seconds")
    args = parser.parse_args()

    # logging.basicConfig(level=logging.ERROR)
    dradisfs = CommandFS(args.src, args.command, args.cache_timeout)
    fuse = FUSE(dradisfs, args.dst, foreground=True, allow_other=True)

if __name__ == '__main__':
    main()
