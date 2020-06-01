import pytest

from lms.models import ApplicationInstance, Course


class TestInsertIfNotExists:
    def test_it_inserts_a_new_row_if_no_matching_row_exists(self, db_session):
        Course.insert_if_not_exists(
            db_session,
            "test_authority_provided_id",
            "test_consumer_key",
            {"foo": "bar"},
        )

        assert Course.get(
            db_session, "test_authority_provided_id", "test_consumer_key"
        ).settings.data == {"foo": "bar"}

    def test_it_does_nothing_if_a_matching_row_already_exists(self, db_session):
        Course.insert_if_not_exists(
            db_session,
            "test_authority_provided_id",
            "test_consumer_key",
            {"original": "settings"},
        )

        Course.insert_if_not_exists(
            db_session,
            "test_authority_provided_id",
            "test_consumer_key",
            {"new": "settings"},
        )

        assert Course.get(
            db_session, "test_authority_provided_id", "test_consumer_key"
        ).settings.data == {"original": "settings"}


class TestGet:
    def test_get_returns_None_if_no_matching_row_exists(self, db_session):
        assert (
            Course.get(db_session, "test_authority_provided_id", "test_consumer_key")
            is None
        )


@pytest.fixture(autouse=True)
def application_instance(db_session):
    application_instance = ApplicationInstance(
        consumer_key="test_consumer_key",
        shared_secret="test_shared_secret",
        lms_url="test_lms_url",
        requesters_email="test_requesters_email",
    )
    db_session.add(application_instance)
    return application_instance
