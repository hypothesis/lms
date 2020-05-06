from unittest.mock import create_autospec, sentinel

import pytest
from h_api.bulk_api import CommandBuilder
from pyramid.httpexceptions import HTTPInternalServerError

from lms.models import HGroup
from lms.services import HAPIError
from lms.services.lti_h import LTIHService
from tests import factories


class TestSync:
    def test_sync_does_nothing_if_provisioning_is_disabled(
        self, ai_getter, lti_h_svc, h_api, h_group
    ):
        ai_getter.provisioning_enabled.return_value = False

        lti_h_svc.sync([h_group], sentinel.params)

        h_api.execute_bulk.assert_not_called()

    def test_sync_catches_HAPIErrors(
        self, h_api, lti_h_svc, h_group, group_info_service
    ):
        h_api.execute_bulk.side_effect = HAPIError

        with pytest.raises(HTTPInternalServerError):
            lti_h_svc.sync([h_group], sentinel.params)

        group_info_service.assert_not_called()

    def test_sync_calls_bulk_action_correctly(self, h_api, h_user, lti_h_svc):
        groups = factories.HGroup.create_batch(2)

        lti_h_svc.sync(groups, sentinel.params)

        _, kwargs = h_api.execute_bulk.call_args

        assert "commands" in kwargs

        # pylint: disable=protected-access
        assert [command.raw for command in kwargs["commands"]] == [
            CommandBuilder.user.upsert(
                {
                    "authority": lti_h_svc._authority,
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
                    "authority": lti_h_svc._authority,
                    "name": group.name,
                    "authority_provided_id": group.authority_provided_id,
                },
                f"group_{i}",
            ).raw
            for i, group in enumerate(groups)
        ] + [
            CommandBuilder.group_membership.create("user_0", f"group_0").raw,
            CommandBuilder.group_membership.create("user_0", f"group_1").raw,
        ]


class TestGroupInfoUpdating:
    def test_sync_upserts_the_GroupInfo_into_the_db(
        self, group_info_service, lti_h_svc, pyramid_request, h_group
    ):
        lti_h_svc.sync([h_group], sentinel.params)

        group_info_service.upsert.assert_called_once_with(
            h_group=h_group,
            consumer_key=pyramid_request.lti_user.oauth_consumer_key,
            params=sentinel.params,
        )

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        return pyramid_request


pytestmark = pytest.mark.usefixtures("ai_getter", "h_api", "group_info_service")


@pytest.fixture
def lti_h_svc(pyramid_request):
    return LTIHService(None, pyramid_request)


@pytest.fixture
def h_user(pyramid_request):
    return pyramid_request.lti_user.h_user


@pytest.fixture
def h_group():
    return create_autospec(HGroup, instance=True, spec_set=True)
