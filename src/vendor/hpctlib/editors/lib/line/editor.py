# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
#
# editors/base/line/editor.py


from ..base import Editor
from .parser import LineParser


class LineEditor(Editor):
    """Base for a line-oriented editor.
    """

    DEFAULT_PARSER_CLASS = LineParser
