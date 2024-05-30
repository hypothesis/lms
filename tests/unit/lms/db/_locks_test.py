import pytest

from lms.db import CouldNotAcquireLock, LockType, try_advisory_transaction_lock

# Two very random IDs which shouldn't conflict with any tests that happen to
# be running in parallel with this module.
LOCK_ID = 1_000_001
OTHER_LOCK_ID = 1_000_002


# Make sure locks acquired in different tests don't conflict.
@pytest.mark.xdist_group("TryAdvisoryTransactionLock")
class TestTryAdvisoryTransactionLock:
    def test_it_succeeds_if_lock_available(self, db_session):
        try_advisory_transaction_lock(
            db_session, LockType.OAUTH2_TOKEN_REFRESH, LOCK_ID
        )

    def test_it_fails_if_lock_not_available(self, db_session, other_db_session):
        try_advisory_transaction_lock(
            db_session, LockType.OAUTH2_TOKEN_REFRESH, LOCK_ID
        )

        lock_type = LockType.OAUTH2_TOKEN_REFRESH
        with pytest.raises(CouldNotAcquireLock) as exc_info:
            try_advisory_transaction_lock(other_db_session, lock_type, LOCK_ID)
        assert exc_info.value.args == (lock_type, LOCK_ID)

    def test_it_succeeds_if_lock_with_different_id_held(
        self, db_session, other_db_session
    ):
        try_advisory_transaction_lock(
            db_session, LockType.OAUTH2_TOKEN_REFRESH, LOCK_ID
        )
        try_advisory_transaction_lock(
            other_db_session, LockType.OAUTH2_TOKEN_REFRESH, OTHER_LOCK_ID
        )

    def test_it_releases_lock_when_transaction_ends(self, db_session, other_db_session):
        try_advisory_transaction_lock(
            db_session, LockType.OAUTH2_TOKEN_REFRESH, LOCK_ID
        )
        db_session.rollback()
        try_advisory_transaction_lock(
            other_db_session, LockType.OAUTH2_TOKEN_REFRESH, LOCK_ID
        )

    @pytest.fixture
    def other_db_session(self, db_engine, db_sessionfactory):
        connection = db_engine.connect()
        return db_sessionfactory(bind=connection)
