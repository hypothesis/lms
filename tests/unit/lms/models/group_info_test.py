import factory
import pytest
from sqlalchemy.exc import IntegrityError

from lms.models import GroupInfo
from tests import factories


class TestGroupInfo:
    def test_application_instance_relation(
        self, application_instance, db_session, group_info
    ):
        db_session.add(group_info)

        retrieved_group_info = db_session.query(GroupInfo).one()

        assert retrieved_group_info.application_instance == application_instance

    def test_application_instance_cant_be_None(self, db_session, group_info):
        group_info.application_instance = None
        db_session.add(group_info)

        with pytest.raises(
            IntegrityError,
            match='"application_instance_id" violates not-null constrain',
        ):
            db_session.flush()

    def test_upsert_instructor_when_no_existing_instructors(self, group_info):
        instructor = factories.HUser()._asdict()

        group_info.upsert_instructor(instructor)

        assert group_info.instructors == [instructor]

    def test_upsert_instructor_when_existing_instructors(
        self, group_info, existing_instructors
    ):
        new_instructor = factories.HUser(username="new_instructor")._asdict()

        group_info.upsert_instructor(new_instructor)

        assert group_info.instructors == existing_instructors + [new_instructor]

    def test_upsert_instructor_when_existing_matching_instructor(
        self, group_info, existing_instructors
    ):
        updated_instructor = factories.HUser(
            username=group_info.instructors[1]["username"], display_name="updated"
        )._asdict()

        group_info.upsert_instructor(updated_instructor)

        assert group_info.instructors == [
            existing_instructors[0],
            updated_instructor,
            existing_instructors[2],
        ]

    def test_upsert_instructor_when_existing_equal_instructor(
        self, group_info, existing_instructors
    ):
        group_info.upsert_instructor(existing_instructors[1])

        assert group_info.instructors == existing_instructors

    def test_set_and_get_type(self):
        group_info = GroupInfo()

        group_info.type = "test_type"

        assert group_info.type == "test_type"

    @pytest.mark.parametrize("blank_info", (True, False))
    def test_info_defaults_ok(self, blank_info):
        group_info = GroupInfo()
        if blank_info:
            group_info.info = None

        assert group_info.type is None
        assert not group_info.instructors

    @pytest.fixture
    def existing_instructors(self, group_info):
        group_info.instructors = factory.build_batch(
            dict, 3, FACTORY_CLASS=factories.HUser
        )
        return group_info.instructors

    @pytest.fixture(autouse=True)
    def application_instance(self):
        """Return the ApplicationInstance that the test GroupInfo belongs to."""
        return factories.ApplicationInstance()

    @pytest.fixture
    def group_info(self, application_instance):
        """Return the GroupInfo object that's being tested."""
        return GroupInfo(
            authority_provided_id="test_authority_provided_id",
            application_instance=application_instance,
        )
