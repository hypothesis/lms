from unittest import mock

import pytest

from lms.models import ApplicationInstance, GroupInfo
from lms.services.group_info_upsert import GroupInfoUpsert


class TestGroupInfoUpsert:
    def test_it_adds_a_new_GroupInfo_if_none_exists(
        self, attrs, db_session, group_info_upsert
    ):
        group_info_upsert(**attrs)

        group_info = (
            db_session.query(GroupInfo)
            .filter_by(authority_provided_id=attrs["authority_provided_id"])
            .one()
        )
        assert group_info.consumer_key == attrs["consumer_key"]
        assert group_info.context_title == attrs["context_title"]
        assert group_info.context_label == attrs["context_label"]

    def test_it_updates_an_existing_GroupInfo_if_one_already_exists(
        self, attrs, db_session, group_info_upsert
    ):
        db_session.add(GroupInfo(**attrs))

        group_info_upsert(**dict(attrs, context_title="NEW_TITLE"))

        group_info = (
            db_session.query(GroupInfo)
            .filter_by(authority_provided_id=attrs["authority_provided_id"])
            .one()
        )
        assert group_info.consumer_key == attrs["consumer_key"]
        assert group_info.context_label == attrs["context_label"]
        assert (
            group_info.tool_consumer_instance_name
            == attrs["tool_consumer_instance_name"]
        )
        assert group_info.context_title == "NEW_TITLE"

    @pytest.fixture
    def group_info_upsert(self, pyramid_config, pyramid_request):
        """The group_info_upsert service that is being tested."""
        return GroupInfoUpsert(mock.sentinel.context, pyramid_request)

    @pytest.fixture
    def attrs(self):
        return {
            "authority_provided_id": "TEST_AUTHORITY_PROVIDED_ID",
            "consumer_key": "TEST_CONSUMER_KEY",
            "context_title": "TEST_CONTEXT_TITLE",
            "context_label": "TEST_CONTEXT_LABEL",
            "tool_consumer_instance_name": "TEST_TOOL_CONSUMER_INSTANCE_NAME",
        }

    @pytest.fixture
    def application_instance(self, pyramid_request):
        """The application instance that the test group infos belong to."""
        application_instance = ApplicationInstance(
            consumer_key="TEST_CONSUMER_KEY",
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
