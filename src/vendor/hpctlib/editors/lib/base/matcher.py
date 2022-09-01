# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
#
# editors/base/matcher.py

class Matcher:
    """Encapsulate match function, match parameters, and match criteria.

    Match parameters:
        rootnode - Node at which to perform match. Defaults to None.
        maxcount - Maximum number of matches to get. Defaults to -1 (no
            limit).
        rettype - Type of node information to return: "node" is the node
            reference, "path" is the list of nodes from rootnode to the
            matched node.

    Match criteria/arguments passed at creation via kwargs are used to
    set object members as: _<key>=<value>.

    To subclass:
    1) set __init__() signature to take named (and optionally typed)
        arguments
    2) set match() to match as needed
    """

    def __init__(self, **kwargs):
        self.maxcount = -1
        self.maxdepth = 6
        self.rettype = "node"
        self.rootnode = None

        for k in ["maxcount", "rettype", "rootnode"]:
            if k in kwargs:
                setattr(self, k, kwargs.pop(k))

        for k in kwargs:
            setattr(self, f"_{k}", kwargs.get(k))

    def match(self, node, nodepath):
        return False


class DescendantOfMatcher(Matcher):
    """Matches against node having an ancestor at a negative depth
    (e.g., -1 for parent, -2 for grandparent) having a submatcher
    match.
    """

    def __init__(self, matcher, depth=1, **kwargs):
        super().__init__(matcher=matcher, depth=depth, **kwargs)

    def match(self, node, nodepath):
        if len(nodepath) > self._depth:
            return self._matcher.match(nodepath[-(self._depth+1)])


class ChildOfMatcher(DescendantOfMatcher):
    """Matches against node with its parent having a submatcher match.

    Note: Special case of DescendantMatcher.
    """

    def __init__(self, matcher, **kwargs):
        super().__init__(matcher=matcher, depth=1, **kwargs)


class NodeMatcher(Matcher):
    """Matches against node.
    """

    def __init__(self, node, **kwargs):
        super().__init__(node=node, **kwargs)

    def match(self, node, nodepath):
        return node == self._node


class ParentOfMatcher(Matcher):
    """Matches against node having *at least one* child with
    submatcher match.

    Note: Mostly useful when submatcher can only match once.
    """

    def __init__(self, matcher, **kwargs):
        super().__init__(matcher=matcher, **kwargs)

    def match(self, node, nodepath):
        #print(f"node ({node})")
        if hasattr(node, "children"):
            for _node in node.children:
                #print(f"testing child ({node})")
                if self._matcher.match(_node, nodepath+[_node]):
                    return True


class TypeMatcher(Matcher):
    """Matches against node type.
    """

    def __init__(self, nodetype, **kwargs):
        super().__init__(nodetype=nodetype, **kwargs)

    def match(self, node, nodepath):
        """Convenience: Find node by type.
        """
        return type(node) == self._nodetype


class TypeValueMatcher(Matcher):
    """Matches against node type and node value.
    """

    def __init__(self, nodetype, value, **kwargs):
        super().__init__(nodetype=nodetype, value=value, **kwargs)

    def match(self, node, nodepath):
        return type(node) == self._nodetype and node.value == self._value


class ValueMatcher(Matcher):
    """Matches against node value.
    """

    def __init__(self, value, **kwargs):
        super().__init__(value=value, **kwargs)

    def match(self, node, nodepath):
        return node.value == self._value
