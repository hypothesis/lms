import pytest
from pyramid.authorization import ACLAuthorizationPolicy

from lms.resources import DefaultResource


class TestDefaultResource:
    def test_it_allows_report_viewers_to_view_the_reports_page(
        self, pyramid_config, pyramid_request
    ):
        pyramid_config.testing_securitypolicy("jeremy", groupids=["report_viewers"])
        pyramid_config.set_authorization_policy(ACLAuthorizationPolicy())

        resource = DefaultResource(pyramid_request)

        assert pyramid_request.has_permission("view", resource)

    def test_it_doesnt_allow_others_to_view_the_reports_page(
        self, pyramid_config, pyramid_request
    ):
        pyramid_config.testing_securitypolicy("someone_else", groupids=["others"])
        pyramid_config.set_authorization_policy(ACLAuthorizationPolicy())

        resource = DefaultResource(pyramid_request)

        assert not pyramid_request.has_permission("view", resource)

    def test_it_allows_lti_users_to_use_the_canvas_api(
        self, pyramid_config, pyramid_request
    ):
        pyramid_config.testing_securitypolicy("some_lti_user", groupids=["lti_user"])
        pyramid_config.set_authorization_policy(ACLAuthorizationPolicy())

        resource = DefaultResource(pyramid_request)

        assert pyramid_request.has_permission("canvas_api", resource)

    def test_it_doesnt_allow_others_to_use_the_canvas_api(
        self, pyramid_config, pyramid_request
    ):
        pyramid_config.testing_securitypolicy("someone_else", groupids=["others"])
        pyramid_config.set_authorization_policy(ACLAuthorizationPolicy())

        resource = DefaultResource(pyramid_request)

        assert not pyramid_request.has_permission("canvas_api", resource)

    @pytest.mark.parametrize(
        "groupid,permission", [("lti_user", True), ("others", False)]
    )
    def test_sync_api_permission(
        self, pyramid_config, pyramid_request, groupid, permission
    ):
        pyramid_config.testing_securitypolicy("some_lti_user", groupids=[groupid])
        pyramid_config.set_authorization_policy(ACLAuthorizationPolicy())

        resource = DefaultResource(pyramid_request)

        assert pyramid_request.has_permission("sync_api", resource) == permission
