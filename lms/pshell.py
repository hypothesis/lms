from contextlib import suppress

from transaction.interfaces import NoTransaction

from lms import models


def setup(env):
    request = env["request"]

    request.tm.begin()

    env["tm"] = request.tm
    env["tm"].__doc__ = "Active transaction manager (a transaction is already begun)."

    env["db"] = env["session"] = request.db
    env["db"].__doc__ = "Active DB session."

    env["m"] = env["models"] = models
    env["m"].__doc__ = "The lms.models package."

    try:
        yield
    finally:
        with suppress(NoTransaction):
            request.tm.abort()
