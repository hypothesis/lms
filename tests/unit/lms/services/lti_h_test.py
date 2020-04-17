from unittest import mock
from unittest.mock import create_autospec

import pytest
from pyramid.httpexceptions import HTTPBadRequest, HTTPInternalServerError

from lms.models import GroupInfo
from lms.services import HAPIError
from lms.services.lti_h import Group, LTIHService
from tests import factories


class TestSync:
    def test_single_group_sync_calls_sync(self, lti_h_svc, group):
        lti_h_svc.sync = create_autospec(lti_h_svc.sync)

        lti_h_svc.single_group_sync()

        lti_h_svc.sync.assert_called_once_with(groups=[group])

    def test_sync_does_nothing_if_provisioning_is_disabled(
        self, ai_getter, lti_h_svc, h_api, group
    ):
        ai_getter.provisioning_enabled.return_value = False

        lti_h_svc.sync(groups=[group])

        h_api.upsert_user.assert_not_called()

    def test_sync_catches_HAPIErrors(self, h_api, lti_h_svc, group):
        h_api.upsert_user.side_effect = HAPIError

        with pytest.raises(HTTPInternalServerError):
            lti_h_svc.sync(groups=[group])

    @pytest.fixture
    def group(self):
        return Group(name="test_group_name", groupid="test_groupid")


class TestGroupUpdating:
    def test_it_upserts_the_group(self, h_api, lti_h_svc):
        lti_h_svc.single_group_sync()

        h_api.upsert_group.assert_called_once_with(
            group_id="test_groupid", group_name="test_group_name"
        )

    def test_it_raises_if_upserting_the_group_fails(self, h_api, lti_h_svc):
        h_api.upsert_group.side_effect = HAPIError("Oops")

        with pytest.raises(HTTPInternalServerError, match="Oops"):
            lti_h_svc.single_group_sync()

    def test_it_upserts_the_GroupInfo_into_the_db(
        self, params, group_info_service, context, lti_h_svc, pyramid_request
    ):
        lti_h_svc.single_group_sync()

        group_info_service.upsert.assert_called_once_with(
            authority_provided_id=context.h_authority_provided_id,
            consumer_key=pyramid_request.lti_user.oauth_consumer_key,
            params=params,
        )

    def test_it_doesnt_upsert_GroupInfo_into_the_db_if_upserting_the_group_fails(
        self, group_info_service, h_api, lti_h_svc
    ):
        h_api.upsert_group.side_effect = HAPIError("Oops")

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


class TestUserUpserting:
    def test_it_calls_h_api_for_user_update(self, h_api, lti_h_svc, h_user):
        lti_h_svc.single_group_sync()

        h_api.upsert_user.assert_called_once_with(
            h_user=h_user,
            provider="test_provider",
            provider_unique_id="test_provider_unique_id",
        )

    def test_it_raises_if_upsert_user_raises_unexpected_error(self, h_api, lti_h_svc):
        h_api.upsert_user.side_effect = HAPIError("whatever")

        with pytest.raises(HTTPInternalServerError, match="whatever"):
            lti_h_svc.single_group_sync()

    def test_it_doesnt_use_the_h_api_if_feature_not_enabled(
        self, ai_getter, h_api, lti_h_svc
    ):
        ai_getter.provisioning_enabled.return_value = False

        lti_h_svc.single_group_sync()

        h_api.upsert_user.assert_not_called()

    def test_it_raises_if_h_user_raises(self, context, lti_h_svc):
        type(context).h_user = mock.PropertyMock(side_effect=HTTPBadRequest("Oops"))

        with pytest.raises(HTTPBadRequest, match="Oops"):
            lti_h_svc.single_group_sync()

    def test_it_raises_if_h_provider_raises(self, context, lti_h_svc):
        type(context).h_provider = mock.PropertyMock(side_effect=HTTPBadRequest("Oops"))

        with pytest.raises(HTTPBadRequest, match="Oops"):
            lti_h_svc.single_group_sync()

    def test_it_raises_if_provider_unique_id_raises(self, context, lti_h_svc):
        type(context).h_provider_unique_id = mock.PropertyMock(
            side_effect=HTTPBadRequest("Oops")
        )

        with pytest.raises(HTTPBadRequest, match="Oops"):
            lti_h_svc.single_group_sync()


class TestAddingUserToGroups:
    def test_it_adds_the_user_to_the_group(self, h_api, lti_h_svc, h_user):
        lti_h_svc.single_group_sync()

        h_api.add_user_to_group.assert_called_once_with(
            h_user=h_user, group_id="test_groupid"
        )

    def test_it_raises_if_post_raises(self, h_api, lti_h_svc):
        h_api.add_user_to_group.side_effect = HAPIError("Oops")

        with pytest.raises(HTTPInternalServerError, match="Oops"):
            lti_h_svc.single_group_sync()


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
        h_provider = "test_provider"
        h_provider_unique_id = "test_provider_unique_id"
        h_authority_provided_id = "test_authority_provided_id"

    context = TestContext()
    context.h_user = h_user  # pylint:disable=attribute-defined-outside-init
    return context


@pytest.fixture
def pyramid_request(context, pyramid_request):
    pyramid_request.context = context
    return pyramid_request
