import pytest

from lms.views.admin.application_instance.show import ShowApplicationInstanceView


@pytest.mark.usefixtures("application_instance_service")
class TestAdminApplicationInstanceViews:
    def test_show_instance_id(self, view, ai_from_matchdict):
        response = view.show_instance()

        assert response["instance"].id == ai_from_matchdict.id

    @pytest.fixture
    def view(self, pyramid_request):
        return ShowApplicationInstanceView(pyramid_request)
