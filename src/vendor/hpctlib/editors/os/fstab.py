# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
#
# editors/os/fstab.py


from ..lib.base import (EOF, ParsingError,
    remove_child_nodes,
    ParentOfMatcher, TypeValueMatcher,
    RecordNode, StringNode)
from ..lib.line import (LineEditor,
    LineParser,
    BlankLineNode, CommentLineNode, LinesNode)


# simple class definitions
FileNode = type("FileNode", (StringNode,), {})
FreqNode = type("FreqNode", (StringNode,), {})
FstabRecordNode = type("FstabRecordNode", (RecordNode,), {"separator": None})
MntopNode = type("MntopNode", (StringNode,), {})
MntopsNode = type("MntopsNode", (RecordNode,), {"separator": ","})
PassnoNode = type("PassnoNode", (StringNode,), {})
RootNode = type("RootNode", (LinesNode,), {})
SpecNode = type("SpecNode", (StringNode,), {})
VfstypeNode = type("VfstypeNode", (StringNode,), {})


class RecordFileMatcher(ParentOfMatcher):

    def __init__(self, path, **kwargs):
        matcher = TypeValueMatcher(nodetype=FileNode, value=path)
        super().__init__(matcher=matcher, **kwargs)


class RecordSpecMatcher(ParentOfMatcher):

    def __init__(self, spec, **kwargs):
        matcher = TypeValueMatcher(nodetype=SpecNode, value=spec)
        super().__init__(matcher=matcher, **kwargs)


class FstabFileParser(LineParser):
    """Fstab file parser.

    See fstab(5).

    Root(Lines):        (CommentLine | BlankLine | FstabRecord)*
    FstabRecord:        Spec File Vfstype Mntops Freq Passno
    Spec(String):       <value>
    File(String):       <value
    Vfstype(String):    <value>
    Mntops:             Mntop ("," Mntop)*
    Mntop(String):      <value>
    Freq(String):       <value>
    Passno(String):     <value>
    """

    def _parse_fstabrecord(self, line):
        try:
            l = line.split(None, 6)
        except:
            raise ParsingError("missing fields")

        mntops = l[3].split(",")
        fstabrecordnode = FstabRecordNode(
                children=[
                    SpecNode(l[0]),
                    FileNode(l[1]),
                    VfstypeNode(l[2]),
                    MntopsNode(children=[MntopNode(mntop) for mntop in mntops]),
                    FreqNode(l[4]),
                    PassnoNode(l[5]),
                ])

        return fstabrecordnode

    def parse(self):
        root = RootNode()

        while True:
            line = self.feed.popline()
            if line == EOF:
                break
            line = line.strip()

            if line.startswith("#"):
                root.add(CommentLineNode(line))
            elif line == "":
                root.add(BlankLineNode(line))
            else:
                root.add(self._parse_fstabrecord(line))
        return root


class FstabFileEditor(LineEditor):
    """Fstab file editor.
    """

    DEFAULT_PARSER_CLASS = FstabFileParser
    DEFAULT_PATH = "/etc/fstab"

    def add_record_by_text(self, line):
        """Convenience: Add record by text format.
        """
        self.root.add(self._parse_fstabrecord(line))

    def remove_by_file(self, path):
        """Convenience: Remove record by file.
        """
        parentchilds = self.root.find(
                RecordFileMatcher(path, rettype="parentchild"))
        remove_child_nodes(parentchilds)

    def remove_by_spec(self, spec):
        """Convenience: Remove record by spec.
        """
        parentchilds = self.root.find(
                RecordSpecMatcher(spec, rettype="parentchild"))
        remove_child_nodes(parentchilds)
