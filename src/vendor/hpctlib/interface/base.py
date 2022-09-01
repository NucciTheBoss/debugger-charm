# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
#
# hpctlib/interface/base.py


"""Base implementation of Interface, Value, SuperInterface.
"""


import logging
from typing import Any


logger = logging.getLogger(__name__)


class NoValue:

    def __str__(self):
        return "no value"

    def __repr__(self):
        return "no value"

NoValue = NoValue()

class Value:
    """Base descriptor for use with interfaces. The interface provides
    storage via its get() and set().
    """

    def __init__(self, codec, default=NoValue, checker=None):
        self.codec = codec
        self.default = default
        self.checker = checker

    def __get__(self, owner, objtype=None):
        """Return value (from owner).
        """
        if owner == None:
            return self

        value = owner._get(self.name, NoValue)
        if value == NoValue:
            value = self.default
        else:
            value = self.codec.decode(value)

        if self.checker:
            self.checker.check(value)

        return value

    def __set__(self, owner, value):
        """Set value (in owner).
        """

        if self.checker:
            self.checker.check(value)

        value = self.codec.encode(value)
        owner._set(self.name, value)

    def __set_name__(self, owner, name):
        """Set name (mangle to put in owner).

        TODO: is this needed?
        """
        #self.name = f"_{owner.__class__.__name__}_store_{name}"
        #self.name = f"_{owner.__name__}_store_{name}"
        self.name = name


class ReadOnlyValue(Value):
    """When target is read-only.
    """

    def __set__(self, owner, value):
        raise AttributeError("this setting is read only")


class Interface:
    """Base interface class providing standard functionality.

    A minimum number of methods, with specific names, are provided to
    avoid polluting the namespace. This allows clean integration with
    descriptors (from Value).
    """

    _basecls = Value

    def __init__(self, *args, **kwargs):
        self._store = {}

    def __repr__(self):
        return f"<{self.__module__}.{self.__class__.__name__} keys ({self.get_keys()})>"

    def __contains__(self, key):
        o = getattr(self.__class__, key)
        return issubclass(o, self._basecls)

    def _get(self, key, default=None):
        """Accessor for the interface store.
        """

        return self._store.get(key, default)

    def _set(self, key, value):
        """Accessor for the interface store.
        """

        self._store[key] = value

    def get_doc(self, show_values=False):
        """Return json object about interface.
        """
        try:
            values = {}
            doc = (self.__class__.__doc__ or "").strip()
            j = {
                "interface": self.__class__.__name__,
                "module": self.__module__,
                "description": doc.strip(),
                "values": values,
            }

            for k in self.get_keys():
                # TODO: call Value.get_doc()
                v = getattr(self.__class__, k)
                doc = (v.__doc__ or "").strip()
                values[k] = {
                    "type": v.__class__.__name__,
                    "module": v.__module__,
                    "codec": v.codec.get_doc(),
                    "checker": v.checker and v.checker.get_doc(),
                    "description": doc.strip(),
                }
                if 0:
                    d = {
                        "type": v.codec.__class__.__name__,
                        "module": v.codec.__module__,
                        "description": doc,
                        "params": self.params
                    }

                if show_values:
                    values[k]["value"] = getattr(self, k)

        except Exception as e:
            raise

        return j

    def get_keys(self):
        """Get keys of all descriptors.
        """

        # TODO: _bucketkey does not show up
        basecls = self._basecls
        return [k for k in dir(self)
                if hasattr(self.__class__, k) and isinstance(getattr(self.__class__, k), basecls)]

    def get_items(self):
        """Get descriptor items.
        """

        basecls = self._basecls
        return [(k, getattr(self, k)) for k in self.get_keys()]

    def is_ready(self):
        """Return if the interface is ready.
        """
        return False

    def set_item(self, key, value):
        """Update a single item by key.
        """

        setattr(self, key, value)

    def update(self, d):
        """Update multiple items from a dict.
        """

        for k, v in d:
            self.set_item(k, v)

class SuperInterface:
    """Base class to manage multiple interfaces.
    """

    def __init__(self):
        pass


def test(interface: Interface, name: str, value: Any):
    """Generic inteface test function.

    Prints out test info. On error, any exceptions are caught and
    reported as messages. This function does not fail.

    Args:
        interface: Interface object.
        name: Identifier for value.
        value: Value to test interface.
    """

    try:
        print(f"interface ({interface})")
        print(f"codec ({getattr(interface.__class__, name).codec})")
        print(f"checker ({getattr(interface.__class__, name).checker})")
        print(f"name ({name})")

        # assign (would normally be <interface>.<name> = <value>)
        print(f"value ({value})")
        setattr(interface, name, value)

        # interface store
        encoded = interface._get(name)
        print(f"encoded type ({type(encoded)}) value ({encoded})")

        decoded = getattr(interface, name)
        print(f"decoded type ({type(decoded)}) value ({decoded})")

        print(f"match? ({decoded == value})")
    except Exception as e:
        print(f"exception e ({e})")

    print("-----")
