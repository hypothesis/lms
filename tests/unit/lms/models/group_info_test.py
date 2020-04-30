import pytest
from sqlalchemy.exc import IntegrityError

from lms.models import ApplicationInstance, GroupInfo
from tests import factories


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

    def test_instructors_defaults_to_an_empty_list(self):
        assert GroupInfo().instructors == []

    def test_upsert_instructor_when_no_existing_instructors(self):
        group_info = GroupInfo()
        instructor = factories.HUser()._asdict()

        group_info.upsert_instructor(instructor)

        assert group_info.instructors == [instructor]

    def test_upsert_instructor_when_existing_instructors(self):
        group_info = GroupInfo()
        existing_instructors = group_info.instructors = [
            factories.HUser()._asdict(),
            factories.HUser()._asdict(),
            factories.HUser()._asdict(),
        ]
        new_instructor = factories.HUser(username="new_instructor")._asdict()

        group_info.upsert_instructor(new_instructor)

        assert group_info.instructors == existing_instructors + [new_instructor]

    def test_upsert_instructor_when_existing_matching_instructor(self):
        group_info = GroupInfo()
        updated_instructor = factories.HUser()._asdict()
        existing_instructors = group_info.instructors = [
            factories.HUser()._asdict(),
            factories.HUser(username=updated_instructor["username"])._asdict(),
            factories.HUser()._asdict(),
        ]

        group_info.upsert_instructor(updated_instructor)

        assert group_info.instructors == [
            existing_instructors[0],
            updated_instructor,
            existing_instructors[2],
        ]

    def test_upsert_instructor_when_existing_equal_instructor(self):
        group_info = GroupInfo()
        existing_instructors = group_info.instructors = [
            factories.HUser()._asdict(),
            factories.HUser()._asdict(),
            factories.HUser()._asdict(),
        ]

        group_info.upsert_instructor(existing_instructors[1])

        assert group_info.instructors == existing_instructors

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
