from unittest import mock

import pytest

from lms.models import GroupInfo
from lms.services.group_info import GroupInfoService
from tests import factories


class TestGroupInfoService:
    AUTHORITY = "TEST_AUTHORITY_PROVIDED_ID"

    def test_upsert_group_info_adds_a_new_if_none_exists(self, db_session, svc, params):
        course = factories.Course(authority_provided_id=self.AUTHORITY)

        svc.upsert_group_info(course, params=params)

        group_info = self.get_inserted_group_info(db_session)

        assert group_info.application_instance == course.application_instance
        assert group_info.context_title == params["context_title"]
        assert group_info.context_label == params["context_label"]
        assert group_info.type == "course_group"

    def test_upsert_group_info_updates_an_existing_if_one_already_exists(
        self, db_session, svc, params, pre_existing_group
    ):
        db_session.add(pre_existing_group)

        svc.upsert_group_info(
            factories.Course(authority_provided_id=self.AUTHORITY),
            params=dict(params, context_title="NEW_TITLE"),
        )

        group_info = self.get_inserted_group_info(db_session)

        assert (
            group_info.application_instance == pre_existing_group.application_instance
        )
        assert group_info.context_label == params["context_label"]
        assert group_info.context_title == "NEW_TITLE"
        assert group_info.type == "course_group"

    def test_upsert_group_info_ignores_non_metadata_params(
        self, db_session, svc, params
    ):
        svc.upsert_group_info(
            factories.Course(authority_provided_id=self.AUTHORITY),
            params=dict(
                params,
                id="IGNORE ME 1",
                authority_provided_id="IGNORE ME 2",
                something_unrelated="IGNORED ME 3",
            ),
        )

        group_info = self.get_inserted_group_info(db_session)

        assert group_info.authority_provided_id == self.AUTHORITY
        assert group_info.id != "IGNORE ME 1"

    @pytest.mark.usefixtures("user_is_instructor")
    def test_upsert_group_info_records_instructors_with_group_info(
        self, db_session, svc, pyramid_request
    ):
        svc.upsert_group_info(
            factories.Course(authority_provided_id=self.AUTHORITY), params={}
        )

        group_info = self.get_inserted_group_info(db_session)

        assert len(group_info.instructors) == 1
        assert (
            group_info.instructors[0]["username"]
            == pyramid_request.lti_user.h_user.username
        )
        assert group_info.instructors[0]["email"] == "test_email"

    @pytest.mark.usefixtures("user_is_learner")
    def test_upsert_group_info_doesnt_record_learners_with_group_info(
        self, db_session, svc
    ):
        svc.upsert_group_info(
            factories.Course(authority_provided_id=self.AUTHORITY), params={}
        )

        group_info = self.get_inserted_group_info(db_session)

        assert group_info.instructors == []

    def get_inserted_group_info(self, db_session):
        return (
            db_session.query(GroupInfo)
            .filter_by(authority_provided_id=self.AUTHORITY)
            .one()
        )

    @pytest.fixture
    def svc(self, pyramid_request):
        return GroupInfoService(mock.sentinel.context, pyramid_request)

    @pytest.fixture
    def params(self):
        return {
            column: f"TEST_{column.upper()}"
            for column in GroupInfo.columns()
            if column not in ("consumer_key", "_info", "application_instance_id")
        }

    @pytest.fixture(
        params=(True, False), ids=["GroupInfo w/o info", "GroupInfo w/info"]
    )
    def pre_existing_group(self, application_instance, request, params):
        pre_existing_group = GroupInfo(
            **dict(
                params,
                id=None,
                authority_provided_id=self.AUTHORITY,
                application_instance_id=application_instance.id,
            )
        )

        if request.param:
            pre_existing_group.info = None

        return pre_existing_group

    @pytest.fixture(autouse=True)
    def with_existing_group_infos(self):
        # Add some "noise" GroupInfo to make the tests more realistic
        factories.GroupInfo.build_batch(3)

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.lti_user = pyramid_request.lti_user._replace(email="test_email")
        return pyramid_request
