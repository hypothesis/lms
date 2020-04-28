import pytest
from sqlalchemy.exc import IntegrityError

from lms.models import ApplicationInstance, GroupInfo


class TestGroupInfo:
    def test_persist_and_retrieve(self, db_session, group_info):
        db_session.add(group_info)

        retrieved_group_info = db_session.query(GroupInfo).one()

        assert retrieved_group_info.id
        assert (
            retrieved_group_info.authority_provided_id == "test_authority_provided_id"
        )
        assert retrieved_group_info.consumer_key == "test_consumer_key"

    def test_application_instance_relation(
        self, application_instance, db_session, group_info
    ):
        db_session.add(group_info)

        retrieved_group_info = db_session.query(GroupInfo).one()

        assert retrieved_group_info.application_instance == application_instance

    def test_authority_provided_id_cant_be_None(self, db_session, group_info):
        group_info.authority_provided_id = None
        db_session.add(group_info)

        with pytest.raises(
            IntegrityError, match='"authority_provided_id" violates not-null constrain'
        ):
            db_session.flush()

    def test_application_instance_cant_be_None(self, db_session, group_info):
        group_info.application_instance = None
        db_session.add(group_info)

        with pytest.raises(
            IntegrityError, match='"consumer_key" violates not-null constrain'
        ):
            db_session.flush()

    @pytest.fixture(autouse=True)
    def application_instance(self):
        """Return the ApplicationInstance that the test GroupInfo belongs to."""
        return ApplicationInstance(
            consumer_key="test_consumer_key",
            shared_secret="test_shared_secret",
            lms_url="test_lms_url",
            requesters_email="test_requesters_email",
        )

    @pytest.fixture
    def group_info(self, application_instance):
        """Return the GroupInfo object that's being tested."""
        return GroupInfo(
            authority_provided_id="test_authority_provided_id",
            application_instance=application_instance,
        )
