from unittest.mock import sentinel

import pytest

from lms.product.d2l._plugin.misc import D2LMiscPlugin
from lms.product.product import Settings


class TestD2LMiscPlugin:
    def test_post_configure_assignment(
        self, plugin, lti_grading_service, pyramid_request
    ):
        pyramid_request.lti_params = {
            "lineitems": sentinel.lineitems,
            "resource_link_id": sentinel.resource_link_id,
            "resource_link_title": sentinel.resource_link_title,
        }
        # pylint:disable=protected-access
        plugin._settings.create_lineitem = True
        lti_grading_service.read_lineitems.return_value = []

        plugin.post_configure_assignment(pyramid_request)

        lti_grading_service.read_lineitems.assert_called_once_with(
            sentinel.lineitems,
            sentinel.resource_link_id,
        )
        lti_grading_service.create_lineitem.assert_called_once_with(
            sentinel.lineitems,
            sentinel.resource_link_id,
            sentinel.resource_link_title,
        )

    def test_post_configure_assignment_existing_lineitem(
        self, plugin, lti_grading_service, pyramid_request
    ):
        pyramid_request.lti_params = {
            "lineitems": sentinel.lineitems,
            "resource_link_id": sentinel.resource_link_id,
            "resource_link_title": sentinel.resource_link_title,
        }
        # pylint:disable=protected-access
        plugin._settings.create_lineitem = True
        lti_grading_service.read_lineitems.return_value = sentinel.lineitem

        plugin.post_configure_assignment(pyramid_request)

        lti_grading_service.read_lineitems.assert_called_once_with(
            sentinel.lineitems,
            sentinel.resource_link_id,
        )
        lti_grading_service.create_lineitem.assert_not_called()

    def test_post_configure_assignment_create_lineitem_disabled(
        self, plugin, lti_grading_service, pyramid_request
    ):
        plugin.post_configure_assignment(pyramid_request)

        lti_grading_service.read_lineitems.assert_not_called()

    @pytest.mark.parametrize(
        "create_lineitem,version,expected",
        [
            (False, "1.1", False),
            (False, "1.3.0", False),
            (True, "1.1", False),
            (True, "1.3.0", True),
        ],
    )
    def test_is_assignment_gradable(self, plugin, create_lineitem, version, expected):
        # pylint:disable=protected-access
        plugin._settings.create_lineitem = create_lineitem

        assert plugin.is_assignment_gradable({"lti_version": version}) == expected

    def test_get_ltia_aud_claim(self, plugin):
        assert (
            plugin.get_ltia_aud_claim(sentinel.registration)
            == "https://api.brightspace.com/auth/token"
        )

    def test_factory(self, pyramid_request):
        plugin = D2LMiscPlugin.factory(sentinel.context, pyramid_request)
        assert isinstance(plugin, D2LMiscPlugin)

    @pytest.fixture
    def plugin(self):
        return D2LMiscPlugin(Settings({}))
