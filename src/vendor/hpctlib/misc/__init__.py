# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
#
# hpctlib/misc/__init__.py


"""Collection of miscellaneous objects.
"""


import functools
import inspect
import logging
import secrets
import time


_app_logger = logging.getLogger(__name__)


def get_methodname(self):
    """Return method name of caller.
    """

    fname = inspect.stack()[1].function
    return f"{self.__class__.__name__}.{fname}"


def get_nonce():
    """Return a nonce.
    """

    return secrets.token_urlsafe()


def get_timestamp():
    """Return a timestamp (string).
    """

    return time.strftime("%Y%m%d-%H%M%S", time.gmtime())


def log_enter_exit(msg=None, logfn=None):
    """Decorator factory to report enter and exit messages via log
    function.

    Args:
        msg: Message to show in log entry.
        logfn: Alternate function to log message. Default is to
            logger.debug of the application logger.
    """

    def decorator(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                qualname = getattr(func, "__qualname__", "na")
                _msg = msg or f"[{qualname}]"
                _logfn = logfn or _app_logger.debug

                try:
                    _logfn(f"{_msg} enter")
                except:
                    pass

                return func(*args, **kwargs)
            finally:
                try:
                    _logfn(f"{_msg} exit")
                except:
                    pass

        return wrapper

    return decorator
