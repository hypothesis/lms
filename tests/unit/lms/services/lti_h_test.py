from unittest.mock import create_autospec, sentinel

import pytest
from h_api.bulk_api import CommandBuilder

from lms.models import Grouping
from lms.services import HAPIError
from lms.services.lti_h import LTIHService
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

    @pytest.fixture
    def lti_h_svc(self, pyramid_request):
        return LTIHService(None, pyramid_request)

    @pytest.fixture
    def h_user(self, pyramid_request):
        return pyramid_request.lti_user.h_user

    @pytest.fixture
    def grouping(self):
        return create_autospec(Grouping, instance=True, spec_set=True)
