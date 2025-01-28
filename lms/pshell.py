# type: ignore  # noqa: PGH003
import os
import sys
from contextlib import suppress

from transaction.interfaces import NoTransaction

from lms import models, services, tasks


def setup(env):
    from h_testkit import (
        set_factoryboy_sqlalchemy_session,  # type: ignore  # noqa: PGH003
    )

    sys.path = ["."] + sys.path  # noqa: RUF005

    from tests import factories

    sys.path = sys.path[1:]

    request = env["request"]

    # Make Pyramid things like route_url() and static_url() use the right
    # hostname and port when called from pshell.
    request.environ["HTTP_HOST"] = os.environ["HTTP_HOST"]

    request.tm.begin()

    env["tm"] = request.tm
    env["tm"].__doc__ = "Active transaction manager (a transaction is already begun)."

    env["db"] = env["session"] = request.db
    env["db"].__doc__ = "Active DB session."

    env["m"] = env["models"] = models
    env["m"].__doc__ = "The lms.models package."

    env["f"] = env["factories"] = factories
    env["f"].__doc__ = "The test factories for quickly creating objects."
    set_factoryboy_sqlalchemy_session(request.db)

    env["t"] = env["tasks"] = tasks
    env["tasks"].__doc__ = "The lms.tasks package."

    env["s"] = env["services"] = services
    env["s"].__doc__ = "The lms.services package."

    try:
        yield
    finally:
        with suppress(NoTransaction):
            request.tm.abort()
