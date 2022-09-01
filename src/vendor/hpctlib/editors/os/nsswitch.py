# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
#
# editors/os/nsswitch.py


from ..lib.base import (EOF, ParsingError,
    ContainerNode, RecordNode, StringNode, TemplateStringNode,
    ParentOfMatcher, TypeMatcher, TypeValueMatcher)
from ..lib.line import (LineEditor,
    LineParser,
    BlankLineNode, CommentLineNode, LinesNode)


# simple class definitions
ActionNode = type("ActionNode", (TemplateStringNode,), {"template": "[{value}]"})
DbnameNode = type("DbnameNode", (StringNode,), {})
RootNode = type("RootNode", (LinesNode,), {})
SourceNode = type("SourceNode", (StringNode,), {})
SourcesActionsNode = type("SourcesActionsNode", (RecordNode,), {"separator": None})


class NsswitchRecordNode(ContainerNode):

    def render(self):
        dbnamenode = self.children[0]
        sourcesactionsnode = self.children[1]
        return f"{dbnamenode.render()}: {sourcesactionsnode.render()}"


class RecordDbnameMatcher(ParentOfMatcher):

    def __init__(self, dbname, **kwargs):
        matcher = TypeValueMatcher(DbnameNode, dbname)
        super().__init__(matcher=matcher, **kwargs)


class NSSwitchConfFileParser(LineParser):
    """Parser for nsswitch.conf file.

    See nsswitch.conf(5).

    Root(Lines):        (CommentLine | BlankLine | NsswitchRecord)*
    NsswithRecord:      Dbname SourcesActions
    Dbname(String):     <value>
    SourcesActions:     (Source | Action)+
    Source(String):     <value>
    Action(String):     "[" <value> "]"
    """

    def parse_nsswitchrecord(self):
        try:
            dbname, sourcesactions = self.line.split(":", 1)
            self.next()
            sourcesactions = sourcesactions.split(None)
        except:
            raise ParsingError("missing dbname or sources and actions")

        sourcesactionsnode = SourcesActionsNode()
        for sourceaction in sourcesactions:
            if sourceaction.startswith("[") and sourceaction.endswith("]"):
                sourcesactionsnode.add(ActionNode(sourceaction[1:-1]))
            else:
                sourcesactionsnode.add(SourceNode(sourceaction))

        nsswitchrecordnode = NsswitchRecordNode(
                [
                    DbnameNode(dbname),
                    sourcesactionsnode,
                ])

        return nsswitchrecordnode

    def parse(self):
        root = RootNode()

        self.next()
        while self.line != EOF:
            if self.is_comment_line(self.line):
                root.add(self.parse_commentline())
            elif self.line == "":
                root.add(self.parse_blankline())
            else:
                root.add(self.parse_nsswitchrecord())
        return root


class NSSwitchConfFileEditor(LineEditor):
    """Editor for nsswitch.conf file.
    """

    DEFAULT_PARSER_CLASS = NSSwitchConfFileParser
    DEFAULT_PATH = "/etc/nsswitch.conf"

    def get_sourcesactions(self, dbname):
        """Return list of sources and actions for dbname.
        """
        parentchild = self.root.find_first(
                RecordDbnameMatcher(dbname, rettype="parentchild"))

        sourcesactions = []
        if parentchild:
            _, childnode = parentchild
            for node in childnode.children[1].children:
                sourcesactions.append(f"{node.render()}")

        return sourcesactions

    def remove_db(self, dbname):
        """Convenience: Remove nsswitch record.
        """
        parentchild = self.root.find_first(
                RecordDbnameMatcher(dbname, rettype="parentchild"))
        if parentchild:
            parentnode, childnode = parentchild
            parentnode.remove(childnode)

    def upsert_record_by_text(self, line):
        """Upsert record by text.
        """
        p = self.get_parser(line)
        p.nextstripline()

        recordnode = p.parse_nsswitchrecord()
        dbnamenode = recordnode.find_first(TypeMatcher(DbnameNode))
        dbname = dbnamenode.value

        parentchild = self.root.find_first(
                RecordDbnameMatcher(dbname, rettype="parentchild"))
        if parentchild:
            parentnode, childnode = parentchild
            parentnode.upsert(childnode, recordnode)
        else:
            self.root.add(recordnode)
