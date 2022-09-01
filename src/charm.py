#!/usr/bin/env python3
# Copyright 2022 nucci
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Charm the service."""

import logging
import sys

import ops.charm
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus
sys.path.insert(1, sys.path[0]+"/vendor")
from hpctlib.ops.charm.debugger import DebuggerCharm as CharmBase

logger = logging.getLogger(__name__)


class DebuggerCharm(CharmBase):
    """Charm the service."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.start, self._on_start)
        self._stored.set_default(things=[])

    def _on_start(self, _):
        self.unit.status = ActiveStatus()

    def _on_config_changed(self, _):
        """Just an example to show how to deal with changed configuration.

        TEMPLATE-TODO: change this example to suit your needs.
        If you don't need to handle config, you can remove this method,
        the hook created in __init__.py for it, the corresponding test,
        and the config.py file.

        Learn more about config at https://juju.is/docs/sdk/config
        """
        pass


if __name__ == "__main__":
    main(DebuggerCharm)
