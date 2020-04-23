from unittest.mock import create_autospec

import pytest
from h_api.bulk_api import CommandBuilder
from pyramid.httpexceptions import HTTPInternalServerError

from lms.models import GroupInfo, HGroup
from lms.services import HAPIError
from lms.services.lti_h import LTIHService
from tests import factories


class TestSync:
    def test_sync_does_nothing_if_provisioning_is_disabled(
        self, ai_getter, lti_h_svc, h_api, h_group
    ):
        ai_getter.provisioning_enabled.return_value = False

        lti_h_svc.sync(h_groups=[h_group])

        h_api.execute_bulk.assert_not_called()

    def test_sync_catches_HAPIErrors(
        self, h_api, lti_h_svc, h_group, group_info_service
    ):
        h_api.execute_bulk.side_effect = HAPIError

        with pytest.raises(HTTPInternalServerError):
            lti_h_svc.sync(h_groups=[h_group])

        group_info_service.assert_not_called()

    def test_sync_calls_bulk_action_correctly(self, h_api, h_user, lti_h_svc):
        groups = factories.HGroup.create_batch(2)

        lti_h_svc.sync(h_groups=groups)

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
        self, params, group_info_service, lti_h_svc, pyramid_request, h_group
    ):
        lti_h_svc.sync([h_group])

        group_info_service.upsert.assert_called_once_with(
            authority_provided_id=h_group.authority_provided_id,
            consumer_key=pyramid_request.lti_user.oauth_consumer_key,
            params=params,
        )

    @pytest.fixture
    def params(self):
        return {
            field.key: f"TEST_{field.key.upper()}" for field in GroupInfo.iter_columns()
        }

    @pytest.fixture
    def pyramid_request(self, params, pyramid_request):
        pyramid_request.params = params
        return pyramid_request


@pytest.mark.usefixtures("use_serial_api")
class TestGroupUpdating:
    def test_it_upserts_the_group(self, h_api, lti_h_svc, h_group):
        lti_h_svc.sync([h_group])

        h_api.upsert_group.assert_called_once_with(h_group)

    def test_it_raises_if_upserting_the_group_fails(self, h_api, lti_h_svc, h_group):
        h_api.upsert_group.side_effect = HAPIError("Oops")

        with pytest.raises(HTTPInternalServerError, match="Oops"):
            lti_h_svc.sync([h_group])


@pytest.mark.usefixtures("use_serial_api")
class TestUserUpserting:
    def test_it_calls_h_api_for_user_update(self, h_api, lti_h_svc, h_user, h_group):
        lti_h_svc.sync([h_group])

        h_api.upsert_user.assert_called_once_with(h_user=h_user)

    def test_it_raises_if_upsert_user_raises_unexpected_error(
        self, h_api, lti_h_svc, h_group
    ):
        h_api.upsert_user.side_effect = HAPIError("whatever")

        with pytest.raises(HTTPInternalServerError, match="whatever"):
            lti_h_svc.sync([h_group])

    def test_it_doesnt_use_the_h_api_if_feature_not_enabled(
        self, ai_getter, h_api, lti_h_svc, h_group
    ):
        ai_getter.provisioning_enabled.return_value = False

        lti_h_svc.sync([h_group])

        h_api.upsert_user.assert_not_called()


@pytest.mark.usefixtures("use_serial_api")
class TestAddingUserToGroups:
    def test_it_adds_the_user_to_the_group(self, h_api, lti_h_svc, h_user, h_group):
        lti_h_svc.sync([h_group])

        h_api.add_user_to_group.assert_called_once_with(h_user, h_group)

    def test_it_raises_if_post_raises(self, h_api, lti_h_svc, h_group):
        h_api.add_user_to_group.side_effect = HAPIError("Oops")

        with pytest.raises(HTTPInternalServerError, match="Oops"):
            lti_h_svc.sync([h_group])


pytestmark = pytest.mark.usefixtures("ai_getter", "h_api", "group_info_service")


@pytest.fixture
def lti_h_svc(pyramid_request):
    return LTIHService(None, pyramid_request)


@pytest.fixture
def h_user(pyramid_request):
    return pyramid_request.lti_user.h_user


@pytest.fixture
def use_serial_api(pyramid_request):
    pyramid_request.feature = lambda item: item == "use_serial_api"


@pytest.fixture
def h_group():
    return create_autospec(HGroup, instance=True, spec_set=True)
