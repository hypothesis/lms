from unittest.mock import sentinel

import pytest
from pyramid.httpexceptions import HTTPNotFound

from lms.views.admin.assignment import AdminAssignmentViews


class TestAdminAssignmentViews:
    def test_show(self, pyramid_request, assignment_service, views):
        pyramid_request.matchdict["id_"] = sentinel.id_

        response = views.show()

        assignment_service.get_by_id.assert_called_once_with(id_=sentinel.id_)

        assert response == {
            "assignment": assignment_service.get_by_id.return_value,
        }

    def test_show_not_found(self, pyramid_request, assignment_service, views):
        pyramid_request.matchdict["id_"] = sentinel.id_
        assignment_service.get_by_id.return_value = None

        with pytest.raises(HTTPNotFound):
            views.show()

    @pytest.fixture
    def views(self, pyramid_request):
        return AdminAssignmentViews(pyramid_request)
