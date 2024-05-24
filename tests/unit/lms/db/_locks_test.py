import pytest

from lms.db import LockType, TryLockError, try_advisory_transaction_lock


class TestTryAdvisoryTransactionLock:
    def test_it(self, db_session, other_db_session):
        # Initial lock attempt should succeed.
        try_advisory_transaction_lock(db_session, LockType.OAUTH2_TOKEN_REFRESH, 123)

        # Another session attempting a conflicting lock should fail
        with pytest.raises(TryLockError):
            try_advisory_transaction_lock(
                other_db_session, LockType.OAUTH2_TOKEN_REFRESH, 123
            )

        # Another session attempting a non-conflicting lock should succeed
        try_advisory_transaction_lock(
            other_db_session, LockType.OAUTH2_TOKEN_REFRESH, 456
        )

        # After the transaction ends, the lock should be released and other
        # sessions should be able to acquire it.
        db_session.rollback()
        try_advisory_transaction_lock(
            other_db_session, LockType.OAUTH2_TOKEN_REFRESH, 123
        )

    @pytest.fixture
    def other_db_session(self, db_engine, db_sessionfactory):
        connection = db_engine.connect()
        return db_sessionfactory(bind=connection)
