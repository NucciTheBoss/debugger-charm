# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
#
# hpctlib/interface/registry.py


"""Provides InterfaceRegistry.
"""


import logging
from typing import Union

from .base import Interface, SuperInterface


logger = logging.getLogger(__name__)


class InterfaceRegistry:
    """Registry of interfaces by name.

    Supports Interface and SuperInterface.
    """

    def __init__(self):
        self.classes = {}

    def get(self, name: str):
        """Get the interface class by name.
        """

        return self.classes.get(name)

    def load(self, name: str, *args, **kwargs):
        """Get the interfaces class and set it up with the args.
        """

        cls = self.get(name)
        if cls:
            return cls(*args, **kwargs)
        else:
            return None

    def items(self):
        """Get interface (key, value) items of registered entries.
        """

        return self.classes.items()

    def keys(self):
        """Get interface keys of registered entries.
        """

        return self.classes.keys()

    def register(self, name: str, cls: Union[Interface, SuperInterface]):
        """Register interface class by name.
        """

        if not issubclass(cls, (Interface, SuperInterface)):
            raise Exception(f"cls ({cls}) not an Interface")

        self.classes[name] = cls

    def values(self):
        """Get interface classes of registered entries.
        """

        return self.classes.values()
