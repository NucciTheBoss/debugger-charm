# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
#
# hpctlib/interface/__init__.py


"""Support for working with operator interfaces.

The ```interface_registry``` provides a central point to obtain an
Interface/SuperInterface by name. The name normally corresponds to
what is specified as the interface in the relation section of the
operator ```metadata.yaml``` file.
"""


import logging

from .registry import InterfaceRegistry


logger = logging.getLogger(__name__)

interface_registry = InterfaceRegistry()
