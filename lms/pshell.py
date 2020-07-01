import sys
from contextlib import suppress

from transaction.interfaces import NoTransaction

from lms import models


def setup(env):
    sys.path = ["."] + sys.path

    from tests import factories  # pylint:disable=import-outside-toplevel

    sys.path = sys.path[1:]

    request = env["request"]

    request.tm.begin()

    env["tm"] = request.tm
    env["tm"].__doc__ = "Active transaction manager (a transaction is already begun)."

    env["db"] = env["session"] = request.db
    env["db"].__doc__ = "Active DB session."

    env["m"] = env["models"] = models
    env["m"].__doc__ = "The lms.models package."

    env["f"] = env["factories"] = factories
    env["f"].__doc__ = "The test factories for quickly creating objects."
    factories.set_sqlalchemy_session(request.db)

    try:
        yield
    finally:
        with suppress(NoTransaction):
            request.tm.abort()
