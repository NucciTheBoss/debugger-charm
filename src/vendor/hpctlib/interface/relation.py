# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
#
# hpctlib/interface/relation.py


"""Base collection of operator relation-oriented interfaces.
"""


import logging
from typing import Any

from . import codec
from . import interface_registry
from .base import (Value, Interface, NoValue, ReadOnlyValue,
    SuperInterface)


logger = logging.getLogger(__name__)

OTHER_ROLE = {
    "peer": "peer",
    "provider": "requirer",
    "requirer": "provider",
}


#
# base classes
#

class MockRelation:

    def __init__(self):
        self.data = {
            "app": {},
            "unit": {},
        }


class BucketInterface(Interface):
    """Interface for relation bucket storage.
    """

    _basecls = Value

    def __init__(self, charm, relname: str, bucketkey: str):
        self._charm = charm
        self._relname = relname
        self._bucketkey = bucketkey
        self._mock = False

    def _get(self, key: str, default=None):
        """Accessor (for raw data) to the relation store.
        """

        key = key.replace("_", "-")

        bucketkey = self._bucketkey
        relation = self.get_relation()

        if relation:
            value = relation.data[bucketkey].get(key, NoValue)
            if value == NoValue:
                value = default
            return value

    def _set(self, key: str, value: Any):
        """Accessor (for raw data) to the relation store.
        """

        key = key.replace("_", "-")

        bucketkey = self._bucketkey

        for relation in self.get_leader_relations():
            print(f"relation ({relation})")
            relation.data[bucketkey].update({key: value})

    def get_relation(self):
        """Return relation associated with registered relation name.
        """

        if self._mock:
            return self._mock_relation
        else:
            return self._charm.model.get_relation(self._relname)

    def get_leader_relations(self):
        """Return relations associated with registered relation name,
        only if leader.
        """

        if self._mock:
            relations = [self._mock_relation]
        else:
            if self._charm.unit.is_leader():
                relations = self._charm.model.relations.get(self._relname, [])
            else:
                relations = []
        return relations

    def is_ready(self):
        """Return if the interface is ready.
        """

        return False

    def set_mock(self):
        self._mock = True
        self._mock_relation = MockRelation()


class AppBucketInterface(BucketInterface):
    """Base app relation bucket interface.

    Note All app relation bucket interfaces should subclass this!
    """
    pass


class AppConfigBucketInterface(AppBucketInterface):
    """
    """

    config = Value(codec.Blob(), None)


class AppSecureConfigBucketInterface(AppBucketInterface):
    """
    """

    config = Value(codec.Blob(), None)


class UnitBucketInterface(BucketInterface):
    """Base unit relation bucket interface.

    The egress_subnets, ingress_address, private_address are available
    for all unit relation data buckets.

    Note: All unit relation bucket interfaces should subclass this!
    """

    egress_subnets = ReadOnlyValue(codec.IPNetwork(), None)
    ingress_address = ReadOnlyValue(codec.IPAddress(), None)
    private_address = ReadOnlyValue(codec.IPAddress(), None)


#
# other subclasses
#

class ReadyBucketInterface(AppBucketInterface):

    status = Value(codec.Ready(), False)


class RelationSuperInterface(SuperInterface):
    """Super interface for working with relation interfaces/data.

    Usage:
    ```
        slurm_ready = AppReadySuperInterface(self, "slurm-ready")
        slurm_ready.provider_app_interface.status = False
        slurm_ready.select(event.app).status = False
    ```
    """

    def __init__(self, charm, relname: str, role=None):
        self.charm = charm
        self.relname = relname
        self.role = role

        self.interface_classes = {
            ("provider", "app"): None,
            ("provider", "unit"): UnitBucketInterface,
            ("requirer", "app"): None,
            ("requirer", "unit"): UnitBucketInterface,
            ("peer", "app"): None,
            ("peer", "unit"): None,
        }

    def get_doc(self, show_values=False):
        """Return json doc about super interface.
        """

        doc = (self.__doc__ or "").strip()
        j = {
            "type": self.__class__.__name__,
            "module": self.__module__,
            "description": doc,
        }
        jj = j["interfaces"] = {}

        for role in ["provider", "requirer", "peer"]:
            for buckettype in ["app", "unit"]:
                jjj = jj[role] = {}
                interface_cls = self.get_interface_class(role, buckettype)
                if interface_cls == None:
                    jjj[buckettype] = None
                else:
                    interface = interface_cls(self.charm, self.relname, None)
                    jjj[buckettype] = interface.get_doc(show_values)

        return j

    def get_interface_class(self, role, buckettype):
        """Return interface class for role and buckettype (one of "app",
        "unit").
        """
        return self.interface_classes.get((role, buckettype))

    def get_role(self):
        """Determine "role" (provider, requirer, peer).
        """

        if self.role:
            return self.role

        meta = self.charm.framework.meta
        if self.relname in meta.provides:
            return "provider"
        elif self.relname in meta.requires:
            return "requirer"
        else:
            return "peer"

    def select(self, bucketkey):
        """Select and return interface to use.

        When determining the interface to use, the role and bucketkey
        are necessary. In particular, when the bucket key is event.app
        or event.unit, then the interface is that of the "other" side.
        E.g., when the provider wants access to the event.app, this means
        the requirer app bucket.

        When working with the bucket directly (e.g.,
        relation.data[event.app]), the "select" is done mentally in
        order to deal with the bucket data suitably.
        """

        role = self.get_role()

        if bucketkey in ["app", "unit"]:
            # special handling for explicit interface selection
            buckettype = bucketkey
            rolekey = role
        else:
            from ops.model import Application

            isapp = isinstance(bucketkey, Application)
            if isapp:
                isselfapp = bucketkey == self.charm.app
            else:
                isselfapp = bucketkey.app == self.charm.app

            buckettype = isapp and "app" or "unit"

            if role != "peer":
                rolekey = isselfapp and role or OTHER_ROLE[role]
            else:
                rolekey = "peer"

        interface_cls = self.get_interface_class(rolekey, buckettype)

        return interface_cls(self.charm, self.relname, bucketkey)


class AppConfigRelationSuperInterface(RelationSuperInterface):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.interface_classes[("provider", "app")] = AppConfigBucketInterface


class AppSecureConfigRelationSuperInterface(RelationSuperInterface):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.interface_classes[("provider", "app")] = AppSecureConfigBucketInterface


class AppReadyRelationSuperInterface(RelationSuperInterface):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.interface_classes[("provider", "app")] = ReadyBucketInterface


# register interfaces

interface_registry.register("relation-app-config", AppConfigRelationSuperInterface)
interface_registry.register("relation-app-secure-config", AppSecureConfigRelationSuperInterface)
interface_registry.register("relation-app-ready", AppReadyRelationSuperInterface)
