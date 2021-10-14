from unittest.mock import create_autospec, sentinel

import pytest
from h_api.bulk_api import CommandBuilder

from lms.models import Grouping
from lms.services import ApplicationInstanceNotFound, HAPIError
from lms.services.lti_h import LTIHService
from tests import factories

pytestmark = pytest.mark.usefixtures(
    "application_instance_service", "h_api", "group_info_service"
)


class TestSync:
    def test_sync_does_nothing_if_provisioning_is_disabled(
        self, application_instance_service, lti_h_svc, h_api, grouping
    ):
        application_instance_service.get_current.return_value.provisioning = False

        lti_h_svc.sync([grouping], sentinel.params)

        h_api.execute_bulk.assert_not_called()

    def test_sync_catches_HAPIErrors(
        self, h_api, lti_h_svc, grouping, group_info_service
    ):
        h_api.execute_bulk.side_effect = HAPIError

        with pytest.raises(HAPIError):
            lti_h_svc.sync([grouping], sentinel.params)

        group_info_service.assert_not_called()

    def test_sync_calls_bulk_action_correctly(self, h_api, h_user, lti_h_svc):
        groups = factories.Grouping.create_batch(2)

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
            CommandBuilder.group_membership.create("user_0", "group_0").raw,
            CommandBuilder.group_membership.create("user_0", "group_1").raw,
        ]

    def test_sync_raises_if_theres_no_ApplicationInstance(
        self, application_instance_service, grouping, lti_h_svc
    ):
        application_instance_service.get_current.side_effect = (
            ApplicationInstanceNotFound
        )

        with pytest.raises(ApplicationInstanceNotFound):
            lti_h_svc.sync([grouping], sentinel.params)


class TestGroupInfoUpdating:
    def test_sync_upserts_the_GroupInfo_into_the_db(
        self, group_info_service, lti_h_svc, pyramid_request, grouping
    ):
        lti_h_svc.sync([grouping], sentinel.params)

        group_info_service.upsert.assert_called_once_with(
            h_group=grouping,
            consumer_key=pyramid_request.lti_user.oauth_consumer_key,
            params=sentinel.params,
        )

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        return pyramid_request


@pytest.fixture
def lti_h_svc(pyramid_request):
    return LTIHService(None, pyramid_request)


@pytest.fixture
def h_user(pyramid_request):
    return pyramid_request.lti_user.h_user


@pytest.fixture
def grouping():
    return create_autospec(Grouping, instance=True, spec_set=True)
