# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
#
# editors/lib/line/node.py


"""Nodes for LineEditor.
"""


from ..base import BlankNode, NewlineJoinNode, StringNode


class BlankLineNode(BlankNode):
    """Blank line node."""
    pass


class CommentLineNode(StringNode):
    """Comment line node."""
    pass


class LineNode(StringNode):
    """Generic line node."""
    pass


class LinesNode(NewlineJoinNode):
    """Multiline node."""
    pass
