# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
#
# editors/base/line/parser.py


from .node import BlankLineNode, CommentLineNode, LineNode, LinesNode
from ..base import EOF, Parser


class LineParser(Parser):
    """Base for a line-parser.

    Note:
    1) self.line is available to all methods and need not be passed.
    2) All parse_* methods should refer to self.line for the latest
        line read from input.
    3) When self.line is consumed, call nextline() or nextstripline()
        to prime self.line.

    Default handling is provided for #-style comments and blank lines
    which are both retained.

    Root:               Lines
    Lines:              (CommentLine | BlankLine | Line) ...
    Line(String):       <value>
    """

    def __init__(self, *args, **kwargs):
        self.line = None
        super().__init__(*args, **kwargs)

    def is_comment_line(self, line):
        return line.startswith("#")

    def next(self):
        return self.nextstripline()

    def nextline(self):
        """Load next line into self.line. And, return self.line.
        """
        self.line = self.feed.popline()
        return self.line

    def nextstripline(self):
        """Load next line into self.line. Strip it of leading
        and trailing whitespace (which gets rid of newline).
        """
        if self.nextline() != EOF:
            self.line = self.line.strip()
        return self.line

    def parse(self):
        root = LinesNode()

        while self.line != EOF:
            if self.is_comment_line(self.line):
                root.add(self.parse_commentline())
            elif self.line == "":
                root.add(self.parse_blankline())
            else:
                root.add(LineNode(self.line))
                self.next()

        return root

    def parse_blankline(self):
        line = self.line
        self.next()
        return BlankLineNode(line)

    def parse_commentline(self):
        line = self.line
        self.next()
        return CommentLineNode(line)

