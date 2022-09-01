# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
#
# editors/lib/base/editor.py


"""An Editor provides a way to interact with (configuration) files.
Loading, dumping, and editing are standard. Convenience methods may
also be provided on a case-by-case basis.
"""


from .node import Node
from .parser import Feed, Parser


class Editor:
    """Base editor class.
    """

    DEFAULT_PARSER_CLASS = Parser
    DEFAULT_PATH = None

    def __init__(self, parsercls=None):
        self.parsercls = parsercls or self.DEFAULT_PARSER_CLASS
        self.root = None

    def add_json(self, j):
        """Add from json representation.
        """
        pass

    def dump(self, path=None):
        """Write rendered results to a file.
        """

        path = path or self.DEFAULT_PATH
        with open(path, "wt") as f:
            f.write(self.root.render())

    def get_parser(self, *args, **kwargs):
        """Return a parser instance of the parser registered with the
        editor.
        """
        return self.parsercls(*args, **kwargs)

    def load(self, path=None):
        """Load file and parse, saving result internally.
        """

        path = path or self.DEFAULT_PATH
        with open(path, "rt") as f:
            root = self.parse(f)
            self.root = root

    def parse(self, f):
        """Parse input and return results.
        """
        return self.get_parser(f).parse()

    def raw(self):

        return self.root

    def render(self):
        """Reconstitute original.
        """

        return self.root.render()

    def render_json(self):
        """Render nodes as json.
        """

        return self.root.render_json()
