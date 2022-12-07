from unittest.mock import sentinel

import pytest

from lms.product.d2l._plugin.misc import D2LMiscPlugin


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
        plugin._create_line_item = True

        plugin.post_configure_assignment(pyramid_request)

        lti_grading_service.create_line_item.assert_called_once_with(
            sentinel.resource_link_id, sentinel.resource_link_title
        )

    def test_post_configure_assignment_gradable_assignment(
        self, plugin, lti_grading_service, pyramid_request
    ):
        pyramid_request.lti_params = {
            "lineitems": sentinel.lineitems,
            "resource_link_id": sentinel.resource_link_id,
            "resource_link_title": sentinel.resource_link_title,
            "lis_outcome_service_url": sentinel.lis_outcome_service_url,
        }
        # pylint:disable=protected-access
        plugin._create_line_item = True

        plugin.post_configure_assignment(pyramid_request)

        lti_grading_service.create_line_item.assert_not_called()

    def test_post_configure_assignment_create_line_item_disabled(
        self, plugin, lti_grading_service, pyramid_request
    ):
        plugin.post_configure_assignment(pyramid_request)

        lti_grading_service.create_line_item.assert_not_called()

    @pytest.mark.parametrize(
        "create_line_item,version,expected",
        [
            (False, "1.1", False),
            (False, "1.3.0", False),
            (True, "1.1", False),
            (True, "1.3.0", True),
        ],
    )
    def test_is_assignment_gradable(self, plugin, create_line_item, version, expected):
        # pylint:disable=protected-access
        plugin._create_line_item = create_line_item

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
        return D2LMiscPlugin(create_line_item=False)
