# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
#
# hpctlib/interface/codec.py


"""Codecs perform the work of encoding and decoding according to an
encoding strategy. Validation of a codec involves the test of
```value == decode(encode(value))```.
"""


import base64
import cryptography
import ipaddress
import json
import logging
from types import NoneType
from typing import Any, Union
import zlib


logger = logging.getLogger(__name__)


class EncodingError(Exception):
    pass


class ParameterError(Exception):
    pass


class ValueError(Exception):
    pass


class Codec:
    """Base class for codecs.

    This class is set up so that minimal overrides are necessary for
    subclasses. Instead, class/object settings suffice.

    The class attribute encoding is determines the encoding/decoding
    strategy. The encoded form is/must be a string. encoding of "asis"
    is a noop for encoding/decoding.

    The codec_types class attribute is used to validate values before
    and after encoding and decoding, respectively.
    """

    codec_types = None
    encoding = "asis"

    def __init__(self, encoding=None):
        """Initialize codec with optional override.

        Args:
            encoding: Encoding/decoding strategy.
        """

        if encoding:
            self.encoding = encoding
        self.params = {}

    def __repr__(self):
        return f"<{self.__module__}.{self.__class__.__name__} encoding ({self.encoding})>"

    def _decode(self, s: str, encoding: str) -> Any:
        """Low-level decode (from string) without checks.

        This method should be overridden for special cases.
        """

        if s == None:
            return None

        if encoding == "asis":
            return s

        if encoding == "string":
            pass
        elif encoding == "base64":
            s = base64.b64decode(s.encode()).decode()
        elif encoding == "base85":
            s = base64.b85decode(s.encode()).decode()
        elif encoding == "zlib":
            s = zlib.decompress(base64.b85decode(s.encode()))
        else:
            raise EncodingError(f"unsupported encoding ({encoding})")

        return json.loads(s)

    def _encode(self, value: Any, encoding: str) -> str:
        """Low-level encode (to string) without checks.

        This method should be overridden for special cases.
        """

        if encoding == "asis":
            return value

        # stringify
        s = json.dumps(value)

        # further encode as/if necessary
        if encoding == "string":
            pass
        elif encoding == "base64":
            s = base64.b64encode(s.encode()).decode()
        elif encoding == "base85":
            s = base64.b85encode(s.encode()).decode()
        elif encoding == "zlib":
            s = base64.b85encode(zlib.compress(s.encode())).decode()
        else:
            raise EncodingError(f"unsupported encoding ({encoding})")

        return s

    def check_type(self, value, types, e=None):
        """Check value type against list of types.

        Args:
            value: Value to check.
            types: List of types to check value against.

        Raises:
            ValueError on error.
        """

        if types == None:
            return
        elif type(value) not in types:
            if not e:
                e = ValueError(f'value type not one of "{types}"')
            raise e

    def decode(self, value: str) -> Any:
        """Decode string value to typed result.

        Subclasses should override this method with proper type
        annotations, then call super().decode().

        Args:
            value: Encoded string to decode.
        Returns:
            Decoded (original) form of value.
        """

        self.check_type(value, [str])
        value = self._decode(value, self.encoding)
        self.check_type(value, self.codec_types)
        return value

    def encode(self, value) -> str:
        """Encode typed value to a string.

        Subclasses should override this method with proper type
        annotations, then call super().encode().

        Args:
            value: Value to encode.
        Returns:
            Encoded form of value.
        """

        self.check_type(value, self.codec_types)
        value = self._encode(value, self.encoding)
        self.check_type(value, [str])
        return value

    def get_doc(self) -> dict:
        """Generate and return a dictionary describing the codec.
        """

        doc = (self.__doc__ or "").strip()
        d = {
            "type": self.__class__.__name__,
            "module": self.__module__,
            "description": doc,
            "encoding": self.encoding,
        }
        return d


class Blob(Codec):
    """Blob (arbitrary encodable object).
    """

    codec_types = None
    encoding = "zlib"

    def decode(self, value: str) -> Any:
        return super().decode(value)

    def encode(self, value: Any) -> str:
        return super().encode(value)


class Boolean(Codec):
    """Boolean: True, False.
    """

    codec_types = [bool]
    encoding = "string"

    def decode(self, value: str) -> bool:
        return super().decode(value)

    def encode(self, value: bool) -> str:
        return super().encode(value)


class Dict(Codec):
    """Dictionary.
    """

    codec_types = [dict]
    encoding = "string"

    def decode(self, value: str) -> dict:
        return super().decode(value)

    def encode(self, value: dict) -> str:
        return super().encode(value)


class Fernet(Blob):
    """Blob with Fernet encryption.

    Note: quiet about errors and values.
    """

    codec_types = [bytes, None]
    encoding = "string"

    def __init__(self, keyfile):
        self.keyfile = keyfile

    def _decode(self, value: str) -> bytes:
        f = cryptography.Fernet(open(self.keyfile, "rt").read())
        value = f.decrypt(value.decode("utf-8"))
        return value

    def _encode(self, value: bytes) -> str:
        f = cryptography.Fernet(open(self.keyfile, "rt").read())
        value = f.encrypt(value).encode("utf-8")
        return value

    def decode(self, value: str) -> bytes:
        return super().decode(value)

    def encode(self, value: bytes) -> str:
        return super().encode(value)


class Float(Codec):
    """Float.

    Note: Be careful with expectations of precision.
    """

    codec_types = [float]
    encoding = "string"

    def decode(self, value: str) -> float:
        return super().decode(value)

    def encode(self, value: float) -> str:
        return super().encode(value)


class Integer(Codec):
    """Integer.
    """

    codec_types = [int]
    encoding = "string"

    def decode(self, value: str) -> int:
        return super().decode(value)

    def encode(self, value: int) -> str:
        return super().encode(value)


class IPAddress(Codec):
    """IP address: IPv4Address, IPv6Address.
    """

    codec_types = [ipaddress.IPv4Address, ipaddress.IPv6Address]
    encoding = "string"

    def _decode(self, value: str) -> Any:
        return ipaddress.ip_address(value)

    def decode(self, value: str) -> Union[ipaddress.IPv4Address, ipaddress.IPv6Address]:
        return super().decode(value)

    def encode(self, value: Union[ipaddress.IPv4Address, ipaddress.IPv6Address]) -> str:
        return super().encode(value)


class IPNetwork(Codec):
    """IP network: IPv4Network, IPv6Network.
    """

    codec_types = [ipaddress.IPv4Network, ipaddress.IPv6Network]
    encoding = "string"

    def _decode(self, value: str) -> Any:
        return ipaddress.ip_network(value)

    def decode(self, value: str) -> Union[ipaddress.IPv4Network, ipaddress.IPv6Network]:
        return super().decode(value)

    def encode(self, value: Union[ipaddress.IPv4Network, ipaddress.IPv6Network]) -> str:
        return super().encode(value)


class Noop(Codec):
    """Noop / no change.
    """

    encoding = "asis"

    def decode(self, value: str) -> Any:
        return value

    def encode(self, value: Any) -> str:
        return value


class String(Codec):
    """String codec (noop).
    """

    encoding = "asis"

    def decode(self, value: str) -> str:
        return value

    def encode(self, value: str) -> str:
        return value


class Ready(Boolean):
    """Convert ready status: True, False.
    """
    pass
