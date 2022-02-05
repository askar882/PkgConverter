#!/usr/bin/env python

import os
import types
import struct
import argparse
import zipfile
from dataclasses import dataclass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', metavar='INPUT', help='.pkg file to convert.')
    parser.add_argument('-o', '--output', help='Output file path.')
    args = parser.parse_args()
    if not os.path.exists(args.input):
        raise FileNotFoundError('%s not found.' % args.input)
    pkg_converter = PkgConverter(args.input)
    output = args.output
    if not output:
        output = args.input + '.zip'
    if os.path.exists(output):
        print("Output file '%s' exists, overwrite?[y/N] " % output, end='')
        prompt = input()
        if not prompt.lower().startswith('y'):
            return
    pkg_converter.convert_to_zip(output)
    print('Succeed.')


class PkgConverter():
    SUPPORTED_VERSIONS = [
        'PKGV0001',
        'PKGV0002',
        'PKGM0014'
    ]

    @dataclass
    class FileInfo():
        path: str
        offset: int
        length: int

    def __init__(self, infile: str):
        self._input = infile
        self.files = []
        if os.path.getsize(infile) <= 4:
            raise ValueError('File too short.')
        with open(infile, 'rb') as f:
            f.read_int = types.MethodType(
                lambda s: struct.unpack('i', s.read(4))[0],
                f)
            signature_length = f.read_int()
            signature = f.read(signature_length).decode()
            if not signature.startswith('PKG'):
                raise ValueError('Not a PKG file.')
            if signature not in self.SUPPORTED_VERSIONS:
                raise NotImplementedError(
                    '%s is not supported.' % signature)
            self.signature = signature
            self.files_count = f.read_int()
            for i in range(self.files_count):
                path_length = f.read_int()
                path = f.read(path_length).decode()
                offset = f.read_int()
                length = f.read_int()
                self.files.append(PkgConverter.FileInfo(path, offset, length))
            self.offset = f.tell()

    def convert_to_zip(self, output):
        with (zipfile.ZipFile(output, mode='w') as z,
              open(self._input, 'rb') as fin):
            z.comment = self.signature.encode()
            for f in self.files:
                fin.seek(self.offset + f.offset)
                data = fin.read(f.length)
                z.writestr(f.path, data)

    def __repr__(self):
        return '''PkgConverter(\
signature='{0}', files_count={1}, files={2}, offset={3})\
'''.format(self.signature,
             self.files_count,
             self.files,
             self.offset)


if __name__ == '__main__':
    main()
