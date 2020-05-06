from unittest import mock

import pytest

from lms.models import ApplicationInstance, GroupInfo
from lms.services.group_info import GroupInfoService


class TestGroupInfoUpsert:
    AUTHORITY = "TEST_AUTHORITY_PROVIDED_ID"
    CONSUMER_KEY = "TEST_CONSUMER_KEY"

    def test_it_adds_a_new_GroupInfo_if_none_exists(
        self, db_session, group_info_svc, params
    ):
        group_info_svc.upsert(
            authority_provided_id=self.AUTHORITY,
            consumer_key=self.CONSUMER_KEY,
            params=params,
            type_="course_group",
        )

        group_info = self.get_inserted_group_info(db_session)

        assert group_info.consumer_key == self.CONSUMER_KEY
        assert group_info.context_title == params["context_title"]
        assert group_info.context_label == params["context_label"]
        assert group_info.type == "course_group"

    def test_it_updates_an_existing_GroupInfo_if_one_already_exists(
        self, db_session, group_info_svc, params
    ):
        db_session.add(
            GroupInfo(
                **dict(
                    params,
                    id=None,
                    authority_provided_id=self.AUTHORITY,
                    consumer_key=self.CONSUMER_KEY,
                )
            )
        )

        group_info_svc.upsert(
            authority_provided_id=self.AUTHORITY,
            consumer_key=self.CONSUMER_KEY,
            params=dict(params, context_title="NEW_TITLE"),
            type_="course_group",
        )

        group_info = self.get_inserted_group_info(db_session)

        assert group_info.consumer_key == self.CONSUMER_KEY
        assert group_info.context_label == params["context_label"]
        assert group_info.context_title == "NEW_TITLE"
        assert group_info.type == "course_group"

    def test_it_ignores_non_metadata_params(self, db_session, group_info_svc, params):
        group_info_svc.upsert(
            authority_provided_id=self.AUTHORITY,
            consumer_key=self.CONSUMER_KEY,
            params=dict(
                params,
                id="IGNORE ME 1",
                authority_provided_id="IGNORE ME 2",
                something_unrelated="IGNORED ME 3",
            ),
            type_="course_group",
        )

        group_info = self.get_inserted_group_info(db_session)

        assert group_info.authority_provided_id == self.AUTHORITY
        assert group_info.id != "IGNORE ME 1"

    @pytest.mark.usefixtures("user_is_instructor")
    def test_it_records_instructors_with_group_info(
        self, db_session, group_info_svc, pyramid_request
    ):
        group_info_svc.upsert(
            authority_provided_id=self.AUTHORITY,
            consumer_key=self.CONSUMER_KEY,
            params={},
            type_="course_group",
        )

        group_info = self.get_inserted_group_info(db_session)

        assert len(group_info.instructors) == 1
        assert (
            group_info.instructors[0]["username"]
            == pyramid_request.lti_user.h_user.username
        )
        assert group_info.instructors[0]["email"] == "test_email"

    @pytest.mark.usefixtures("user_is_learner")
    def test_it_doesnt_record_learners_with_group_info(
        self, db_session, group_info_svc
    ):
        group_info_svc.upsert(
            authority_provided_id=self.AUTHORITY,
            consumer_key=self.CONSUMER_KEY,
            params={},
            type_="course_group",
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
    def group_info_svc(self, pyramid_request):
        """Return the group_info_svc service that is being tested."""
        return GroupInfoService(mock.sentinel.context, pyramid_request)

    @pytest.fixture
    def params(self):
        return {
            column: f"TEST_{column.upper()}"
            for column in GroupInfo.columns()
            if column != "info"
        }

    @pytest.fixture
    def application_instance(self, pyramid_request):
        """Return the application instance that the test group infos belong to."""
        application_instance = ApplicationInstance(
            consumer_key=self.CONSUMER_KEY,
            developer_key="TEST_DEVELOPER_KEY",
            lms_url="TEST_LMS_URL",
            shared_secret="TEST_SHARED_SECRET",
            requesters_email="TEST_EMAIL",
        )
        pyramid_request.db.add(application_instance)
        return application_instance

    @pytest.fixture(autouse=True)
    def group_infos(self, application_instance, pyramid_request):
        """Add some "noise" group infos."""
        # Add some "noise" group infos to the DB for every test, to make the
        # tests more realistic.
        group_infos = [
            GroupInfo(
                authority_provided_id="NOISE_ID_1",
                consumer_key="NOISE_CONSUMER_KEY_1",
                application_instance=application_instance,
            ),
            GroupInfo(
                authority_provided_id="NOISE_ID_2",
                consumer_key="NOISE_CONSUMER_KEY_2",
                application_instance=application_instance,
            ),
            GroupInfo(
                authority_provided_id="NOISE_ID_3",
                consumer_key="NOISE_CONSUMER_KEY_3",
                application_instance=application_instance,
            ),
        ]
        pyramid_request.db.add_all(group_infos)
        return group_infos

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.lti_user = pyramid_request.lti_user._replace(email="test_email")
        return pyramid_request
