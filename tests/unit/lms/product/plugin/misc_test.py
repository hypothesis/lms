from unittest.mock import sentinel

import pytest

from lms.models import LTIParams
from lms.product.plugin.misc import MiscPlugin
from tests import factories


class TestMiscPlugin:
    def test_deep_linking_prompt_for_title(self, plugin):
        assert not plugin.deep_linking_prompt_for_title

    @pytest.mark.parametrize(
        "service_url,expected", [(None, False), (sentinel.service_url, True)]
    )
    def test_is_assignment_gradable(
        self, plugin, pyramid_request, service_url, expected
    ):
        pyramid_request.lti_params["lis_outcome_service_url"] = service_url

        assert plugin.is_assignment_gradable(pyramid_request.lti_params) == expected

    @pytest.mark.parametrize("lti_v13", [True, False])
    def test_accept_grading_comments(self, request, plugin, lti_v13):
        application_instance = request.getfixturevalue(
            "lti_v13_application_instance" if lti_v13 else "application_instance"
        )
        assert plugin.accept_grading_comments(application_instance) == lti_v13

    def test_get_ltia_aud_claim(self, plugin, lti_registration):
        assert plugin.get_ltia_aud_claim(lti_registration) == lti_registration.token_url

    def test_get_document_url_with_assignment_in_db_existing_assignment(
        self, plugin, pyramid_request
    ):
        assignment = factories.Assignment(document_url=sentinel.document_url)
        pyramid_request.lti_params["resource_link_id"] = sentinel.link_id

        result = plugin.get_document_url(
            pyramid_request, assignment, sentinel.historical_assignment
        )

        assert result == sentinel.document_url

    def test_get_document_url_with_assignment_in_db_copied_assignment(
        self, plugin, pyramid_request
    ):
        historical_assignment = factories.Assignment(document_url=sentinel.document_url)

        result = plugin.get_document_url(pyramid_request, None, historical_assignment)

        assert result == sentinel.document_url

    def test_get_document_url_with_no_document(self, plugin, pyramid_request):
        assert not plugin.get_document_url(pyramid_request, None, None)

    def test_get_deeplinking_launch_url(self, plugin, pyramid_request):
        assert (
            plugin.get_deeplinking_launch_url(pyramid_request, sentinel.config)
            == "http://example.com/lti_launches"
        )

    @pytest.mark.parametrize(
        "custom,expected",
        [
            (
                {"url": sentinel.url, "group_set": sentinel.group_set},
                {"url": sentinel.url, "group_set": sentinel.group_set},
            ),
            ({"url": sentinel.url}, {"url": sentinel.url}),
            ({"group_set": sentinel.group_set}, {"group_set": sentinel.group_set}),
            ({"other_param": sentinel.other_param}, {}),
        ],
    )
    def test_get_deep_linked_assignment_configuration(
        self, plugin, custom, expected, pyramid_request_with_custom_lti_params
    ):
        pyramid_request = pyramid_request_with_custom_lti_params(custom)

        assert (
            plugin.get_deep_linked_assignment_configuration(pyramid_request) == expected
        )

    def test_clean_lms_grading_comment(self, plugin, strip_html_tags):
        result = plugin.clean_lms_grading_comment(sentinel.comment)

        strip_html_tags.assert_called_once_with(sentinel.comment)
        assert result == strip_html_tags.return_value

    def test_format_grading_comment_for_lms(self, plugin):
        assert (
            plugin.format_grading_comment_for_lms(sentinel.comment) == sentinel.comment
        )

    @pytest.fixture
    def lti_registration(self):
        return factories.LTIRegistration()

    @pytest.fixture
    def strip_html_tags(self, patch):
        return patch("lms.product.plugin.misc.strip_html_tags")

    @pytest.fixture
    def pyramid_request_with_custom_lti_params(self, pyramid_request):
        def _with_custom(custom):
            pyramid_request.lti_jwt = {
                "https://purl.imsglobal.org/spec/lti/claim/custom": custom
            }
            pyramid_request.lti_params = LTIParams.from_request(pyramid_request)
            return pyramid_request

        return _with_custom

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.lti_params = LTIParams({"tool_consumer_instance_guid": "guid"})
        return pyramid_request

    @pytest.fixture
    def plugin(self):
        return MiscPlugin()
