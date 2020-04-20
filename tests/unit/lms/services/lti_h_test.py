from unittest.mock import create_autospec

import pytest
from h_api.bulk_api import CommandBuilder
from pyramid.httpexceptions import HTTPInternalServerError

from lms.models import GroupInfo
from lms.services import HAPIError
from lms.services.lti_h import HGroup, LTIHService
from tests import factories


class TestSync:
    def test_single_group_sync_calls_sync(self, lti_h_svc, h_group):
        lti_h_svc.sync = create_autospec(lti_h_svc.sync)

        lti_h_svc.single_group_sync()

        lti_h_svc.sync.assert_called_once_with(h_groups=[h_group])

    def test_sync_does_nothing_if_provisioning_is_disabled(
        self, ai_getter, lti_h_svc, h_api, h_group
    ):
        ai_getter.provisioning_enabled.return_value = False

        lti_h_svc.sync(h_groups=[h_group])

        h_api.bulk_action.assert_not_called()

    def test_sync_catches_HAPIErrors(self, h_api, lti_h_svc, h_group):
        h_api.bulk_action.side_effect = HAPIError

        with pytest.raises(HTTPInternalServerError):
            lti_h_svc.sync(h_groups=[h_group])

    def test_sync_calls_bulk_action_correctly(self, h_api, h_user, lti_h_svc):
        groups = [
            HGroup(name=f"name_{i}", authority_provided_id="test_authority_provided_id")
            for i in range(2)
        ]

        lti_h_svc.sync(h_groups=groups)

        _, kwargs = h_api.bulk_action.call_args

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

    @pytest.fixture
    def h_group(self):
        return HGroup(
            name="test_group_name", authority_provided_id="test_authority_provided_id"
        )


class TestGroupInfoUpdating:
    def test_it_upserts_the_GroupInfo_into_the_db(
        self, params, group_info_service, context, lti_h_svc, pyramid_request
    ):
        lti_h_svc.single_group_sync()

        group_info_service.upsert.assert_called_once_with(
            authority_provided_id=context.h_authority_provided_id,
            consumer_key=pyramid_request.lti_user.oauth_consumer_key,
            params=params,
        )

    def test_it_doesnt_upsert_GroupInfo_into_the_db_if_bulk_action_fails(
        self, group_info_service, h_api, lti_h_svc
    ):
        h_api.bulk_action.side_effect = HAPIError("Oops")

        try:
            lti_h_svc.single_group_sync()
        except:  # pylint: disable=bare-except
            pass

        group_info_service.assert_not_called()

    @pytest.fixture
    def params(self):
        return {
            field.key: f"TEST_{field.key.upper()}" for field in GroupInfo.iter_columns()
        }

    @pytest.fixture
    def pyramid_request(self, params, pyramid_request):
        pyramid_request.params = params
        return pyramid_request


pytestmark = pytest.mark.usefixtures("ai_getter", "h_api", "group_info_service")


@pytest.fixture
def lti_h_svc(pyramid_request):
    return LTIHService(None, pyramid_request)


@pytest.fixture
def h_user():
    return factories.HUser()


@pytest.fixture
def context(h_user):
    class TestContext:
        h_groupid = "test_groupid"
        h_group_name = "test_group_name"
        h_authority_provided_id = "test_authority_provided_id"

    context = TestContext()
    context.h_user = h_user  # pylint:disable=attribute-defined-outside-init
    return context


@pytest.fixture
def pyramid_request(context, pyramid_request):
    pyramid_request.context = context
    return pyramid_request
