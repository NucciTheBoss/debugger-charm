# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
#
# editors/os/systemd.py


from ..lib.base import (EOF, ParsingError,
    remove_child_nodes,
    ParentOfMatcher, TypeMatcher, TypeValueMatcher,
    RecordNode, StringNode, TemplateStringNode)
from ..lib.line import (LineEditor,
    LineParser,
    BlankLineNode, CommentLineNode, LinesNode)


HeaderNode = type("HeaderNode", (TemplateStringNode,), {"template": "[{value}]"})
NameNode = type("NameNode", (StringNode,), {})
RootNode = type("RootNode", (LinesNode,), {})
SectionNode = type("SectionNode", (RecordNode,), {"separator": "\n"})
SettingsNode = type("SettingsNode", (RecordNode,), {"separator": "\n"})
SettingNode = type("SettingNode", (RecordNode,), {"separator": "="})
ValueNode = type("ValueNode", (StringNode,), {})


class SystemdConfFileParser(LineParser):
    """Systemd conf file parser.

    Note: Comments between continuation lines are relocated above the
    first line with a continuation character. Containuation lines are
    concatenated.

    See https://www.freedesktop.org/software/systemd/man/systemd.syntax.html .

    Root(Lines):        (CommentLine | BlankLine | Section)*
    Section(Record):    Header Settings*
    Header(String):     "[" <value> "]"
    Settings(Record):   (CommentLine | BlankLine | Setting)
    Setting(Record):    Name "=" Value CommentNode?
    Name(String):       <value>
    Value(String):      <value>
    """

    def is_comment_line(self, line):
        return line.startswith("#") or line.startswith(";")

    def parse_section(self):
        secname = self.line[1:-1].strip()
        secnode = SectionNode(children=[HeaderNode(secname)])
        self.next()

        settingsnode = SettingsNode()

        while self.line != EOF:
            if self.is_comment_line(self.line):
                settingsnode.add(self.parse_commentline())
            elif self.line == "":
                settingsnode.add(self.parse_blankline())
            elif not self.line.startswith("["):
                settingsnode.add(self.parse_setting())
            else:
                break

        if settingsnode.children:
            secnode.add(settingsnode)

        return secnode

    def parse_setting(self):
        try:
            name, value = self.line.split("=", 1)
            self.next()
            return SettingNode(children=[NameNode(name), ValueNode(value)])
        except:
            raise ParsingError("missing name and value")

    def parse(self):
        root = RootNode()

        self.next()
        while self.line != EOF:
            if self.is_comment_line(self.line):
                root.add(self.parse_commentline())
            elif self.line == "":
                root.add(self.parse_blankline())
            else:
                if self.line.startswith("[") and self.line.endswith("]"):
                    root.add(self.parse_section())
                else:
                    raise ParsingError("missing section")
        return root


class SystemdConfFileEditor(LineEditor):
    """A non-lossy editor for systemd configuration files.
    """

    DEFAULT_PARSER_CLASS = SystemdConfFileParser

    def get_section_names(self):
        nodes = self.root.find(TypeMatcher(nodetype=HeaderNode))
        return [node.value for node in nodes]

    def get_settings(self, secname):
        matcher = TypeValueMatcher(nodetype=HeaderNode, value=secname)
        secnode = self.root.find_first(ParentOfMatcher(matcher=matcher, rettype="node"))
        if secnode:
            settings = []
            for node in secnode.find(TypeMatcher(nodetype=SettingNode)):
                namenode, valuenode = node.children
                settings.append((namenode.value, valuenode.value))
            return settings
        else:
            return None
