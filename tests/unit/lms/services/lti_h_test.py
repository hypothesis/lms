from unittest.mock import create_autospec, sentinel

import pytest
from h_api.bulk_api import CommandBuilder

from lms.models import Grouping
from lms.services import HAPIError
from lms.services.lti_h import LTIHService, checkpoint_sync_data
from tests import factories


@pytest.mark.usefixtures("application_instance_service", "h_api", "group_info_service")
class TestSync:
    def test_sync_catches_HAPIErrors(
        self, h_api, lti_h_svc, grouping, group_info_service
    ):
        h_api.execute_bulk.side_effect = HAPIError

        with pytest.raises(HAPIError):
            lti_h_svc.sync([grouping], sentinel.params)

        group_info_service.assert_not_called()

    def test_sync_calls_bulk_action_correctly(self, h_api, h_user, lti_h_svc):
        courses = factories.Course.create_batch(2)

        lti_h_svc.sync(courses, sentinel.params)

        _, kwargs = h_api.execute_bulk.call_args

        assert "commands" in kwargs

        assert [command.raw for command in kwargs["commands"]] == [
            CommandBuilder.user.upsert(
                {
                    "authority": lti_h_svc._authority,  # noqa: SLF001
                    "username": h_user.username,
                    "display_name": h_user.display_name,
                    "identities": [
                        {
                            "provider": h_user.provider,
                            "provider_unique_id": h_user.provider_unique_id,
                        }
                    ],
                },
                "user_0",
            ).raw
        ] + [
            CommandBuilder.group.upsert(
                {
                    "authority": lti_h_svc._authority,  # noqa: SLF001
                    "name": group.name,
                    "authority_provided_id": group.authority_provided_id,
                },
                f"group_{i}",
            ).raw
            for i, group in enumerate(courses)
        ] + [
            CommandBuilder.group_membership.create("user_0", "group_0").raw,
            CommandBuilder.group_membership.create("user_0", "group_1").raw,
        ]

    def test_sync_upserts_the_GroupInfo_into_the_db(
        self, group_info_service, lti_h_svc, grouping
    ):
        lti_h_svc.sync([grouping], sentinel.params)

        group_info_service.upsert_group_info.assert_called_once_with(
            grouping=grouping, params=sentinel.params
        )

    def test_sync_syncs_checkpoints(self, h_api, lti_h_svc):
        groupings = factories.Course.create_batch(2)
        checkpoint_data = {
            "document_uri": "https://example.com/doc",
            "user": {"username": "teacher", "role": "instructor"},
        }

        lti_h_svc.sync(groupings, sentinel.params, checkpoint_data=checkpoint_data)

        h_api.sync_checkpoints.assert_called_once_with(
            checkpoints=[
                {
                    "group_authority_provided_id": grouping.authority_provided_id,
                    "document_uri": "https://example.com/doc",
                }
                for grouping in groupings
            ],
            user={"username": "teacher", "role": "instructor"},
        )

    @pytest.fixture
    def lti_h_svc(self, pyramid_request):
        return LTIHService(None, pyramid_request)

    @pytest.fixture
    def h_user(self, pyramid_request):
        return pyramid_request.lti_user.h_user

    @pytest.fixture
    def grouping(self):
        return create_autospec(Grouping, instance=True, spec_set=True)


class TestCheckpointSyncData:
    def test_it(self, lti_user):
        assignment = factories.Assignment(
            checkpoint_enabled=True, document_uri="https://example.com/doc"
        )

        assert checkpoint_sync_data(assignment, lti_user) == {
            "document_uri": "https://example.com/doc",
            "user": {
                "username": lti_user.h_user.username,
                "role": "student",
            },
        }

    @pytest.mark.usefixtures("user_is_instructor")
    def test_it_with_instructor(self, lti_user):
        assignment = factories.Assignment(
            checkpoint_enabled=True, document_uri="https://example.com/doc"
        )

        assert checkpoint_sync_data(assignment, lti_user)["user"]["role"] == (
            "instructor"
        )

    def test_it_returns_None_without_an_assignment(self, lti_user):
        assert checkpoint_sync_data(None, lti_user) is None

    def test_it_returns_None_when_checkpoint_is_not_enabled(self, lti_user):
        assignment = factories.Assignment(
            checkpoint_enabled=False, document_uri="https://example.com/doc"
        )

        assert checkpoint_sync_data(assignment, lti_user) is None

    def test_it_returns_None_when_the_document_uri_is_not_known(self, lti_user):
        # E.g. a file assignment whose PDF fingerprint hasn't been computed
        # yet: syncing our internal document_url instead would create an h
        # document no annotation ever matches.
        assignment = factories.Assignment(checkpoint_enabled=True, document_uri=None)

        assert checkpoint_sync_data(assignment, lti_user) is None
