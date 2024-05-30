from enum import IntEnum

import sqlalchemy as sa
from sqlalchemy.orm import Session


class CouldNotAcquireLock(Exception):
    """Exception raised if a lock cannot be immediately acquired."""


class LockType(IntEnum):
    """
    Identifies a type of resource for an advisory lock.

    Advisory locks are identified by a `(type, object_id)` tuple, where both
    are 32-bit integers. This enum provides values for `type`. The meaning of
    `object_id` depends on the type.
    """

    OAUTH2_TOKEN_REFRESH = 1
    """
    Lock for an OAuth 2 token update.

    The object ID is the `OAuth2Token.id` value for the token being updated.
    """


def try_advisory_transaction_lock(db: Session, lock_type: LockType, id_: int):
    """
    Attempt to acquire an advisory lock, scoped to the current transaction.

    The lock is released when the transaction is closed.

    :param db: database session
    :param lock_type: the type of entity for the lock
    :param id_: a type-specific ID for the entity being locked
    :raise CouldNotAcquireLock: if the lock cannot be acquired immediately
    """
    query = sa.text("SELECT pg_try_advisory_xact_lock(:key1, :key2)")
    if not db.execute(query, {"key1": lock_type, "key2": id_}).scalar():
        raise CouldNotAcquireLock(lock_type, id_)
