# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
#
# editors/os/freedesktop.py


from ..lib.base import (EOF, ParsingError,
    remove_child_nodes,
    Matcher, ParentOfMatcher, TypeMatcher, TypeValueMatcher,
    RecordNode, StringNode, TemplateStringNode)
from ..lib.line import (LineEditor,
    LineParser,
    BlankLineNode, CommentLineNode, LinesNode)


# simple class definitions
EntriesNode = type("EntriesNode", (RecordNode,), {"separator": "\n"})
EntryNode = type("EntryNode", (RecordNode,), {"separator": "="})
GroupNode = type("GroupNode", (RecordNode,), {})
HeaderNode = type("HeaderNode", (TemplateStringNode,), {"template": "[{value}]"})
KeyNode = type("KeyNode", (StringNode,), {})
RootNode = type("RootNode", (LinesNode,), {})
ValueNode = type("ValueNode", (StringNode,), {})


class EntryMatcher(Matcher):
    """Matches against node value: groupname, key, value (optional).
    """

    def __init__(self, groupname, key, value=None, **kwargs):
        super().__init__(groupname=groupname, key=key, value=value, **kwargs)

    def match(self, node, nodepath):
        if type(node) == GroupNode and node.value == self._groupname:

            value = node.value
            return value["key"] == self._key and value["value"] == self._value


class HeaderMatcher(TypeValueMatcher):
    """Matches against node value: groupname.
    """

    def __init__(self, groupname, **kwargs):
        super().__init__(nodetype=HeaderNode, value=groupname, **kwargs)


class FreeDesktopConfFileParser(LineParser):
    """Free desktop conf file parser.

    See https://specifications.freedesktop.org/desktop-entry-spec/latest/ar01s03.html .

    Root(Lines):        (CommentLine | BlankLine | Group)*
    Group(Record)       Header Entries
    Header(String):     "[" <value> "]"
    Entries(Record):    (CommentLine | BlankLine | Entry)*
    Entry:              Key "=" Value
    Key(String):        <value>
    Value(String):      <value>
    """

    def parse_group(self):
        name = self.line[1:-1].strip()
        self.next()
        return GroupNode([HeaderNode(name), self.parse_entries()])

    def parse_entries(self):
        entriesnode = EntriesNode()

        while self.line != EOF:
            if self.is_comment_line(self.line):
                entriesnode.add(self.parse_commentline())
            elif self.line == "":
                entriesnode.add(self.parse_blankline())
            elif not self.line.startswith("["):
                entriesnode.add(self.parse_entry())
            else:
                break

        return entriesnode

    def parse_entry(self):
        try:
            key, value = self.line.split("=", 1)
            self.next()
        except:
            raise ParsingError("missing key and value")

        return EntryNode([KeyNode(key), ValueNode(value)])

    def parse(self):
        root = RootNode()

        self.next()
        while self.line != EOF:
            if self.is_comment_line(self.line):
                root.add(self.parse_commentline())
            elif self.line == "":
                root.add(self.parse_blankline())
            elif self.line.startswith("["):
                root.add(self.parse_group())
            else:
                raise ParsingError("missing section")
        return root


class FreeDesktopConfFileEditor(LineEditor):
    """A non-lossy editor for freedesktop.org configuation files.
    """

    DEFAULT_PARSER_CLASS = FreeDesktopConfFileParser

    def add_entry(self, groupname, key, value):
        groupnode = self.find_first(ParentOfMatcher(matcher=HeaderMatcher(groupname)))
        if not groupnode:
            self.add_group(groupname)
            groupnode = self.find_first(ParentOfMatcher(matcher=HeaderMatcher(groupname)))

        entriesnode = groupnode.find_first(TypeMatcher(EntriesNode))
        if entriesnode:
            entriesnode.add(EntryNode([KeyNode(key), ValueNode(value)]))

    def add_group(self, groupname):
        node = self.find_first(HeaderMatcher(groupname))
        if not node:
            self.root.add(GroupNode([HeaderNode(groupname), EntriesNode()]))

    def get_groups(self):
        nodes = self.root.find(TypeMatcher(HeaderNode))
        return [f"{node.value}" for node in nodes]

    def remove_entry(self, groupname, key):
        parentchild = self.root.find_first(EntryMatcher(groupname, key, rettype="parentchild"))
        if parentchild:
            remove_child_nodes([parentchild])

    def remove_group(self, groupname):
        parentchild = self.root.find_first(
                ParentOfMatcher(HeaderMatcher(groupname), rettype="parentchild"))
        if parentchild:
            remove_child_nodes([parentchild])
