import pytest

from lms.views.admin.application_instance.downgrade import (
    DowngradeApplicationInstanceView,
)
from tests.matchers import temporary_redirect_to


@pytest.mark.usefixtures("application_instance_service")
class TestDowngradeApplicationInstanceView:
    @pytest.mark.usefixtures("lti_v13_application_instance")
    def test_downgrade_instance(self, view, pyramid_request, ai_from_matchdict):
        response = view.downgrade_instance()

        assert not ai_from_matchdict.lti_registration_id
        assert not ai_from_matchdict.deployment_id
        assert response == temporary_redirect_to(
            pyramid_request.route_url("admin.instance", id_=ai_from_matchdict.id)
        )

    @pytest.mark.usefixtures("ai_from_matchdict")
    def test_downgrade_instance_no_lti13(self, view, pyramid_request):
        view.downgrade_instance()

        assert pyramid_request.session.peek_flash("errors")

    @pytest.mark.usefixtures("lti_v13_application_instance")
    def test_downgrade_instance_no_consumer_key(
        self, view, pyramid_request, ai_from_matchdict
    ):
        ai_from_matchdict.consumer_key = None

        view.downgrade_instance()

        assert pyramid_request.session.peek_flash("errors")

    @pytest.fixture
    def view(self, pyramid_request):
        return DowngradeApplicationInstanceView(pyramid_request)
