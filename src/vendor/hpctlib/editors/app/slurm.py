# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
#
# editors/app/slurm.py


from ..lib.base import (EOF, ParsingError,
    Matcher,
    RecordNode, StringNode)
from ..lib.line import (LineParser,
    LineEditor,
    LinesNode)


# simple class definitions
CommentNode = type("CommentNode", (StringNode,), {})
IncludePathNode = type("IncludePathNode", (StringNode,), {})
ItemNode = type("ItemNode", (RecordNode,), {"separator": "="})
ItemNameNode = type("ItemNameNode", (StringNode,), {})
ItemValueNode = type("ItemValueNode", (StringNode,), {})
ParamsNode = type("ParamsNode", (RecordNode,), {"separator": None})
ParamNode = type("ParamNode", (RecordNode,), {"separator": "="})
ParamNameNode = type("ParamNameNode", (StringNode,), {})
ParamValueNode = type("ParamValueNode", (StringNode,), {})
RootNode = type("RootNode", (LinesNode,), {})
SlurmRecordNode = type("SlurmRecordNode", (RecordNode,), {})

class IncludeNode(StringNode):

    def render(self):
        pathnode = self.children[0]
        return f"Include {pathnode.render()}"
        # TODO: trailing comment?

class RecordMatcher(Matcher):
    """Matches against: name, value (optional).
    """

    args = ["name", "value"]

    def match(self, node, nodepath):
        if node["type"] == "slurm-record":
            value = node["value"]
            if self._name in value:
                if self._value != None:
                    return value[self._name] == self._value
                return True


class SlurmConfFileParser(LineParser):
    """SlurmConfFileParser.

    See https://slurm.schedmd.com/slurm.conf.html.

    Root(Lines):        (CommentLine | BlankLine | Include | SlurmRecord)*
    Include:            "include" IncludePath Comment?
    IncludePath(String):<value>
    SlurmRecord(Record):Item Params* Comment?
    Item(Record):       Name "=" Value
    Name(String):       <value>
    Value(String):      <value>
    Params(Record):     ParamItem ("," ParamItem)*
    ParamItem(Record):  ParamName "=" ParamValue
    Comment(String):    <"#" value>

    TODO: How best to handle Comment node?
    """

    def parse_include(self):
        try:
            _, filename = self.line.split(None, 1)
            self.next()

            if "#" in filename:
                filename, comment = filename.split("#", 1)
            else:
                comment = None
        except:
            raise ParsingError("missing filename")

        return IncludeNode([IncludePathNode(filename)])

    def parse_item(self):
        try:
            name, value = self.line.split("=", 1)
            l = value.split(None, 1)
            if len(l) == 1:
                # no params
                l.append("")
            value, self.line = l
        except Exception as e:
            raise ParsingError("missing value")

        return ItemNode([ItemNameNode(name), ItemValueNode(value)])

    def parse_params(self):
        try:
            if "#" in self.line:
                i = self.line.index("#")
                line = self.line[:i]
                self.line = self.line[i:]
            else:
                line, self.line = self.line, ""

            params = line.split(None)
        except Exception as e:
            raise ParsingError("missing paramater(s)")

        paramsnode = ParamsNode()
        try:
            for param in params:
                name, value = param.split("=", 1)
                paramsnode.add(ParamNode([ParamNameNode(name), ParamValueNode(value)]))
        except Exception as e:
            raise ParsingError("bad parameter")

        return paramsnode

    def parse_slurmrecord(self):
        slurmrecordnode = SlurmRecordNode([self.parse_item()])

        if not self.is_comment_line(self.line):
            paramsnode = self.parse_params()
            if paramsnode:
                slurmrecordnode.add(paramsnode)

        if self.is_comment_line(self.line):
            slurmrecordnode.add(CommentNode(self.line))
        elif self.line != "":
            raise ParsingError("bad record")

        self.next()

        return slurmrecordnode

    def parse(self):
        root = RootNode()

        while self.line != EOF:
            if self.is_comment_line(self.line):
                root.add(self.parse_commentline())
            elif self.line == "":
                root.add(self.parse_blankline())
            else:
                l = self.line.split(None, 1)
                if l[0].lower() == "include":
                    root.add(self.parse_include())
                else:
                    root.add(self.parse_slurmrecord())
        return root


class SlurmConfFileEditor(LineEditor):
    """Slurm configuration file editor.
    """

    DEFAULT_PARSER_CLASS = SlurmConfFileParser
    DEFAULT_PATH = "/etc/slurm/slurm.conf"

    def add_line(self, line):
        """Convenience: Add line.
        """
        p = self.get_parser(line)
        self.root.add(p.parse_slurmrecord())
