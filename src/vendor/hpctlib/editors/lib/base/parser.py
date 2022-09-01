# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
#
# editors/lib/base/parser.py


"""A Parser.
"""


import io
import os
import os.path
import subprocess

from .node import Node


class EOFType:
    pass

EOF = EOFType()


class Feed:

    def __init__(self, f):
        self.buf = None
        if type(f) == str:
            self.f = io.StringIO(f)
        else:
            self.f = f

    def peekchar(self):
        """Read, but do not remove, next character from input.
        """
        self.preload()
        if self.buf:
            ch = self.buf[0]
        else:
            ch = self.f.read(1)
            self.buf = ch
        return ch

    def peeknchars(self, count):
        """Read, but do not remove, next n characters from input.
        """
        self.preload()
        pass

    def popchar(self):
        """Read next character from input.
        """
        self.preload()
        buf = self.buf
        try:
            ch = buf[0]
            self.buf = buf[1:]
        except:
            return EOF
        return ch

    def popline(self):
        """Read next line (upto newline) from input.
        """
        self.preload()
        try:
            buf = self.buf

            i = buf.index("\n")
            line = buf[:i+1]
            self.buf = buf[i+1:]
        except:
            line = buf
            self.buf = ""
        if line == "":
            return EOF
        return line

    def preload(self):
        """Preload buffer. Ensure that there is at least a full line
        in the buffer.
        """
        #print(f"PRE: preload buf {self.buf}")
        if not self.buf:
            self.buf = self.f.readline()
        #print(f"POST: preload buf {self.buf}")


class Parser:
    """Base parser class.
    """

    def __init__(self, f, prime=True):
        self.root = None
        self.feed = Feed(f)
        if prime:
            self.next()

    def next(self):
        """Load buffer with next "chunk" of data. This is parser-specific.
        """
        pass

    def parse(self):
        """Parse input and return results.
        """

        return Node()


class ParsingError(Exception):
    pass
