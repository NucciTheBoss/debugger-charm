# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
#
# editors/os/exports.py


import re

from ..lib.base import (EOF, ParsingError,
    remove_child_nodes,
    CommaJoinNode, ContainerNode, RecordNode, StringNode,
    ParentOfMatcher, TypeValueMatcher)
from ..lib.line import (LineEditor,
    LineParser,
    BlankLineNode, CommentLineNode, LinesNode)


CLIENTOPTIONS_RE = r"""(?P<client>[^(]+)(\((?P<options>[a-zA-Z0-9_,"]+)\))?"""


# simple class definitions
ClientNode = type("ClientNode", (StringNode,), {})
ClientsOptionsNode = type("ClientsOptionsNode", (RecordNode,), {"separator": ","})
ExportsRecordNode = type("ExportsRecordNode", (RecordNode,), {})
OptionNode = type("OptionNode", (StringNode,), {})
OptionsNode = type("OptionsNode", (RecordNode,), {"separator": ","})
PathNode = type("PathNode", (StringNode,), {})
RootNode = type("RootNode", (LinesNode,), {})


class ClientOptionsNode(ContainerNode):

    def render(self):
        clientnode = self.children[0]
        optionsnode = self.children[1]
        return f"{clientnode.render()}({optionsnode.render()})"


class RecordPathMatcher(ParentOfMatcher):

    def __init__(self, path, **kwargs):
        matcher = TypeValueMatcher(PathNode, path)
        super().__init__(matcher=matcher, **kwargs)


class ExportsFileParser(LineParser):
    """Exports file parser.

    See exports(5).

    Root(Lines):        (CommentLine | Blankline | ExportsRecord)*
    ExportsRecord:      Path ClientsOptions
    Path(String):       <value>
    ClientsOptions:     ClientOptions*
    ClientOptions:      Client "(" Options ")"
    Client(String):     <value>
    Options:            Option "," ...
    Option(String):     <value>
    """

    def parse_exportsrecord(self):
        try:
            path, clientsoptions = self.line.split(None, 1)
            self.next()
        except:
            raise ParsingError("missing fields")

        clientsoptionsnode = ClientsOptionsNode()

        for clientoptions in clientsoptions.split():
            if "(" in clientoptions and clientoptions.endswith(")"):
                client, rest = clientoptions.split("(", 1)
                opts = rest[:-1].split(",")
            else:
                client = clientoptions
                opts = []
            optionsnode = OptionsNode()
            optionsnode.addn([OptionNode(opt) for opt in opts])

            clientsoptionsnode.add(ClientOptionsNode([ClientNode(client), optionsnode]))

        return ExportsRecordNode([PathNode(path), clientsoptionsnode])

    def parse(self):
        root = RootNode()

        while self.line != EOF:
            if self.line.startswith("#"):
                root.add(self.parse_commentline())
            elif self.line == "":
                root.add(self.parse_blankline())
            else:
                root.add(self.parse_exportsrecord())

        return root


class ExportsFileEditor(LineEditor):
    """Exports file editor.
    """

    DEFAULT_PARSER_CLASS = ExportsFileParser
    DEFAULT_PATH = "/etc/exports"

    def add_record_by_text(self, line):
        """Convenience: Add record by text format.
        """
        p = self.get_parser(line)
        p.nextstripline()
        self.root.add(p.parse_exportsrecord())

    def remove_by_path(self, path):
        """Convenience: Remove record by path.
        """
        parentchilds = self.root.find(
                RecordPathMatcher(path, rettype="parentchild"))
        remove_child_nodes(parentchilds)
