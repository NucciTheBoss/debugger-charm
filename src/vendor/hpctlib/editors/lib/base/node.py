# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
#
# editors/lib/base/node.py


"""Base nodes for Editor.
"""


class Node:
    """Base node.
    """

    def render(self):
        """Return a reconstituted form of the node value.
        """
        pass

    def render_json(self):
        """Render a json (compatible) object.
        """
        pass


class LeafNode(Node):
    """Node with a value, but no children.

    This ensures that double-minded nodes do not exist.
    """

    def __init__(self, value):
        self.value = value

    def render_json(self):
        """Render a json (compatible) object.
        """

        d = {
            "type": self.__class__.__name__,
            "value": f"{self.value}",
        }
        return d

    def walk(self, maxdepth=1, topdown=True):
        """No children.
        """

        yield self

    def walkpath(self, nodepath=None, maxdepth=1, topdown=True):
        """No children.
        """

        nodepath = (nodepath or [])+[self]
        yield nodepath[:]


class ContainerNode(Node):
    """Base node with children but no value.

    This ensures that double-minded nodes do not exist.
    """

    def __init__(self, children=None):
        self.children = children if children != None else []

    def add(self, node):
        """Add node to children.
        """

        self.children.append(node)

    def addn(self, nodes):
        """Add node to children.
        """

        self.children.extend(nodes)

    def has(self, node):
        """Return True if node is a child.
        """

        return node in self.children

    def find(self, matcher, maxcount=None, maxdepth=None, rettype=None):
        """Find all nodes/nodepaths/parentchild which the matcher
        matches.
        """

        rettype = rettype or matcher.rettype
        maxcount = maxcount or matcher.maxcount
        maxdepth = maxdepth or matcher.maxdepth

        l = []
        for nodepath in self.walkpath(maxdepth=maxdepth):
            node = nodepath[-1]
            if matcher.match(node, nodepath):
                if rettype == "node":
                    l.append(node)
                elif rettype == "path":
                    l.append(nodepath)
                elif rettype == "parentchild":
                    if len(nodepath) > 1:
                        l.append(nodepath[-2:])
                    else:
                        l.append([None, nodepath[-1]])
                if len(l) == matcher.maxcount:
                    break
        return l

    def find_first(self, matcher, maxdepth=None, rettype=None):
        """Find first match and return it, else None.
        """
        results = self.find(matcher, maxcount=1, maxdepth=maxdepth, rettype=rettype)
        if results:
            return results[0]
        else:
            return None

    def index(self, node):
        """Return position of node in children.
        """

        try:
            return self.children.index(node)
        except:
            return -1

    def insert_before(self, node, relnode, append=False):
        """Insert node before relnode. Optionally append.
        """

        try:
            i = self.children.index(relnode)
            self.children.insert(i, node)
        except:
            if append:
                self.children.append(node)

    def insert_after(self, node, relnode, append=False):
        """Insert node after relnode. Optionally append.
        """
        try:
            i = self.children.index(relnode)
            self.children.insert(i+1, node)
        except:
            if append:
                self.children.append(node)

    def remove(self, node):
        """Remove child node (if found) from the list of children.
        """

        try:
            self.children.remove(node)
        except:
            pass

    def render(self):
        """Return a reconstituted form of the node value.
        """
        pass

    def render_json(self):
        """Render a json (compatible) object.
        """

        d = {
            "type": self.__class__.__name__,
            "children": [node.render_json() for node in self.children],
        }

        return d

    def upsert(self, node, newnode):
        """Upsert node with newnode in the list of children.
        """

        try:
            i = self.children.index(node)
            self.children[i] = newnode
        except:
            self.children.append(newnode)

    def walk(self, maxdepth=1, topdown=True):
        """Descend the node tree (via children) and return all nodes
        encountered.
        """

        if topdown:
            yield self
        for node in self.children:
            yield from node.walk(maxdepth-1, topdown)
        if not topdown:
            yield self

    def walkpath(self, nodepath=None, maxdepth=1, topdown=True):
        """Descend the node tree (via children) and return all nodepaths
        encountered.
        """

        nodepath = (nodepath or [])+[self]
        if topdown:
            yield nodepath[:]
        if maxdepth > 0:
            for node in self.children:
                yield from node.walkpath(nodepath, maxdepth-1, topdown)
        if not topdown:
            yield nodepath[:]


class BlankNode(LeafNode):
    """Blank.
    """

    def render(self):
        return ""


class JoinNode(ContainerNode):
    """Joins rendered children with separator.
    """

    # whitespace
    separator = None

    def render(self):
        separator = self.separator if self.separator != None else " "
        return separator.join([node.render() for node in self.children])

    def render_json(self):
        d = super().render_json()
        d["separator"] = self.separator
        return d

class CommaJoinNode(JoinNode):
    """Joins rendered children with ",".
    """

    separator = ","


class NewlineJoinNode(JoinNode):
    """Joins rendered children with newline.
    """

    separator = "\n"


class RecordNode(JoinNode):
    """Holds items rendered by joining with whitespace separator.
    """

    separator = None


class StringNode(LeafNode):
    """Renders value as a string.
    """

    def render(self):
        return f"{self.value}"


class TemplateStringNode(StringNode):
    """Renders value within a template string.
    """

    template = "{value}\n"

    def render(self):
        return self.template.format(value=self.value)



def remove_child_nodes(parentchilds):
    """Convenience: Remove child node from parent, multiple times.
    """
    for parentnode, childnode in parentchilds:
        parentnode.remove(childnode)
