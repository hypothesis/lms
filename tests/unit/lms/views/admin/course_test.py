from unittest.mock import sentinel

import pytest
from pyramid.httpexceptions import HTTPNotFound

from lms.models.public_id import InvalidPublicId
from lms.views.admin.course import AdminCourseViews


@pytest.mark.usefixtures("course_service", "organization_service")
class TestAdminCourseViews:
    def test_show(self, pyramid_request, course_service, views):
        pyramid_request.matchdict["id_"] = sentinel.id_

        response = views.show()

        course_service.get_by_id.assert_called_once_with(id_=sentinel.id_)

        assert response == {
            "course": course_service.get_by_id.return_value,
        }

    def test_show_not_found(self, pyramid_request, course_service, views):
        pyramid_request.matchdict["id_"] = sentinel.id_
        course_service.get_by_id.return_value = None

        with pytest.raises(HTTPNotFound):
            views.show()

    def test_search(self, pyramid_request, course_service, views):
        pyramid_request.params["context_id"] = " PUBLIC_ID "
        pyramid_request.params["name"] = " NAME "
        pyramid_request.params["id"] = " 100 "
        pyramid_request.params["h_id"] = " H_ID "

        result = views.search()

        course_service.search.assert_called_once_with(
            id_="100",
            name="NAME",
            context_id="PUBLIC_ID",
            h_id="H_ID",
            organization=None,
        )
        assert result == {"courses": course_service.search.return_value}

    def test_search_by_public_id(
        self, pyramid_request, views, organization_service, course_service
    ):
        pyramid_request.params["org_public_id"] = " PUBLIC_ID "
        organization_service.get_by_public_id.return_value = sentinel.org

        views.search()

        course_service.search.assert_called_once_with(
            id_="",
            name="",
            context_id="DUMMY-CONTEXT-ID",
            h_id="",
            organization=sentinel.org,
        )

    def test_search_invalid_public_id(
        self, pyramid_request, views, organization_service
    ):
        pyramid_request.params["org_public_id"] = " PUBLIC_ID "
        organization_service.get_by_public_id.side_effect = InvalidPublicId

        views.search()

        assert pyramid_request.session.peek_flash("errors")

    def test_search_invalid(self, pyramid_request, views):
        pyramid_request.params["id"] = "not a number"

        assert not views.search()
        assert pyramid_request.session.peek_flash

    def test_blank_search(self, views, course_service):
        views.search()

        course_service.search.assert_called_once_with(
            id_="", name="", context_id="DUMMY-CONTEXT-ID", h_id="", organization=None
        )

    @pytest.fixture
    def views(self, pyramid_request):
        return AdminCourseViews(pyramid_request)
