from unittest.mock import sentinel

import pytest
from pyramid.httpexceptions import HTTPNotFound

from lms.services import ApplicationInstanceNotFound
from lms.views.admin.application_instance._core import BaseApplicationInstanceView


@pytest.mark.usefixtures("application_instance_service")
class TestBaseApplicationInstanceView:
    def test_application_instance(
        self, view, application_instance_service, ai_from_matchdict
    ):
        ai = view.application_instance

        application_instance_service.get_by_id.assert_called_once_with(id_=sentinel.id_)

        assert ai == ai_from_matchdict

    @pytest.mark.usefixtures("ai_from_matchdict")
    def test_application_instance_with_no_ai(self, view, application_instance_service):
        application_instance_service.get_by_id.side_effect = ApplicationInstanceNotFound
        with pytest.raises(HTTPNotFound):
            assert view.application_instance

    @pytest.fixture
    def view(self, pyramid_request):
        return BaseApplicationInstanceView(pyramid_request)
