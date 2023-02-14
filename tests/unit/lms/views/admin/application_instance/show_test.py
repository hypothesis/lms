import pytest
from pyramid.httpexceptions import HTTPNotFound

from lms.services import ApplicationInstanceNotFound
from lms.views.admin.application_instance.show import ShowApplicationInstanceView


@pytest.mark.usefixtures("application_instance_service")
class TestAdminApplicationInstanceViews:
    def test_show_instance_id(self, view, ai_from_matchdict):
        response = view.show_instance()

        assert response["instance"].id == ai_from_matchdict.id

    @pytest.mark.usefixtures("ai_from_matchdict")
    def test_show_instance_not_found(self, view, application_instance_service):
        application_instance_service.get_by_id.side_effect = ApplicationInstanceNotFound

        with pytest.raises(HTTPNotFound):
            view.show_instance()

    @pytest.fixture
    def view(self, pyramid_request):
        return ShowApplicationInstanceView(pyramid_request)
