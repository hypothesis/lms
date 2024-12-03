#!/usr/bin/env python3
# mypy: disable-error-code="attr-defined"
"""
Initialize the DB.

Usage:

    python3 -m lms.scripts.init_db --help

"""

import argparse
import logging
from os import environ

import alembic.command
import alembic.config
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import ProgrammingError

from lms import models  # noqa: F401
from lms.db import Base, create_engine

log = logging.getLogger(__name__)


def is_stamped(engine: Engine) -> bool:
    """Return True if the DB is stamped with an Alembic revision ID."""

    with engine.connect() as connection:
        try:
            if connection.execute(text("select * from alembic_version")).first():
                return True
        except ProgrammingError:
            pass

    return False


def delete(engine: Engine) -> None:
    """Delete any existing DB tables."""

    try:
        from lms.db import pre_delete  # noqa: PLC0415
    except ImportError:
        pass
    else:
        pre_delete(engine)

    with engine.connect() as connection:
        # Delete the DB "public" schema directly.
        # We do this instead of using SQLAlchemy's drop_all because we want to delete all tables in the current DB.
        # For example, this will delete tables created by migrations in other branches, not only the ones SQLAlchemy know about in the current code base.
        connection.execute(text("DROP SCHEMA PUBLIC CASCADE;"))
        connection.execute(text("CREATE SCHEMA PUBLIC;"))
        connection.execute(text("COMMIT;"))

    try:
        from lms.db import post_delete  # noqa: PLC0415
    except ImportError:
        pass
    else:
        post_delete(engine)


def create(engine: Engine) -> None:
    """Create new DB tables from the app's models."""

    try:
        from lms.db import pre_create  # noqa: PLC0415
    except ImportError:
        pass
    else:
        pre_create(engine)

    Base.metadata.create_all(engine)

    try:
        from lms.db import post_create  # noqa: PLC0415
    except ImportError:
        pass
    else:
        post_create(engine)


def main():
    parser = argparse.ArgumentParser(description="Initialize the DB.")

    parser.add_argument(
        "--delete",
        action="store_true",
        help="delete any existing DB tables",
    )
    parser.add_argument(
        "--create",
        action="store_true",
        help="create new DB tables from the models",
    )
    parser.add_argument(
        "--stamp",
        action="store_true",
        help="stamp the DB with the latest Alembic version",
    )

    args = parser.parse_args()

    engine = create_engine(environ["DATABASE_URL"])

    if args.delete:
        delete(engine)

    if args.create or args.stamp:
        stamped = is_stamped(engine)

    if args.create:
        if stamped:
            log.warning("Not creating tables because the DB is stamped by Alembic")
        else:
            create(engine)

    if args.stamp:
        if stamped:
            log.warning("Not stamping DB because it's already stamped")
        else:
            alembic.command.stamp(alembic.config.Config("conf/alembic.ini"), "head")


if __name__ == "__main__":
    main()
