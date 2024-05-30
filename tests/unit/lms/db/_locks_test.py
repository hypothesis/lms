import pytest

from lms.db import CouldNotAcquireLock, LockType, try_advisory_transaction_lock


class TestTryAdvisoryTransactionLock:
    def test_it_succeeds_if_lock_available(self, db_session):
        try_advisory_transaction_lock(db_session, LockType.OAUTH2_TOKEN_REFRESH, 123)

    def test_it_fails_if_lock_not_available(self, db_session, other_db_session):
        try_advisory_transaction_lock(db_session, LockType.OAUTH2_TOKEN_REFRESH, 123)

        lock_type = LockType.OAUTH2_TOKEN_REFRESH
        with pytest.raises(CouldNotAcquireLock) as exc_info:
            try_advisory_transaction_lock(other_db_session, lock_type, 123)
        assert exc_info.value.args == (lock_type, 123)

    def test_it_succeeds_if_lock_with_different_id_held(
        self, db_session, other_db_session
    ):
        try_advisory_transaction_lock(db_session, LockType.OAUTH2_TOKEN_REFRESH, 123)
        try_advisory_transaction_lock(
            other_db_session, LockType.OAUTH2_TOKEN_REFRESH, 456
        )

    def test_it_releases_lock_when_transaction_ends(self, db_session, other_db_session):
        try_advisory_transaction_lock(db_session, LockType.OAUTH2_TOKEN_REFRESH, 123)
        db_session.rollback()
        try_advisory_transaction_lock(
            other_db_session, LockType.OAUTH2_TOKEN_REFRESH, 123
        )

    @pytest.fixture
    def other_db_session(self, db_engine, db_sessionfactory):
        connection = db_engine.connect()
        return db_sessionfactory(bind=connection)
