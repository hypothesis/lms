from unittest.mock import sentinel

import pytest

from lms.models import LTIParams
from lms.services import DocumentURLService
from lms.services.document_url import factory
from tests import factories


class TestDocumentURLService:
    def test_get_document_url(self, svc, pyramid_request):
        assert not svc.get_document_url(pyramid_request)

    @pytest.mark.parametrize(
        "url,expected",
        (
            (None, None),
            # URL encoded paths
            (
                "https%3A%2F%2Fexample.com%2Fpath%3Fparam%3Dvalue",
                "https://example.com/path?param=value",
            ),
            (
                "http%3A%2F%2Fexample.com%2Fpath%3Fparam%3Dvalue",
                "http://example.com/path?param=value",
            ),
            (
                "HTTP%3a%2F%2Fexample.com%2Fpath%3Fparam%3Dvalue",
                "HTTP://example.com/path?param=value",
            ),
            (
                "canvas%3A%2F%2Ffile%2Fcourse_id%2FCOURSE_ID%2Ffile_if%2FFILE_ID",
                "canvas://file/course_id/COURSE_ID/file_if/FILE_ID",
            ),
            (
                "jstor%3A%2F%2FDOI",
                "jstor://DOI",
            ),
            (
                "vitalsource%3A%2F%2Fbook%2FbookID%2FL-999-70469%2Fcfi%2F%2F6%2F8",
                "vitalsource://book/bookID/L-999-70469/cfi//6/8",
            ),
            # Non-URL encoded paths
            (
                "https://example.com/path?param=value",
                "https://example.com/path?param=value",
            ),
            (
                "http://example.com/path?param=%25foo%25",
                "http://example.com/path?param=%25foo%25",
            ),
            (
                "canvas://file/course_id/COURSE_ID/file_if/FILE_ID",
                "canvas://file/course_id/COURSE_ID/file_if/FILE_ID",
            ),
            ("jstor://DOI", "jstor://DOI"),
            (
                "vitalsource://book/bookID/L-999-70469/cfi//6/8",
                "vitalsource://book/bookID/L-999-70469/cfi//6/8",
            ),
            # Unknown but valid (RFC3986) schemas get decoded
            (
                "j5-tor.r%3A%2F%2FDOI",
                "j5-tor.r://DOI",
            ),
            # Invalid schemas don't get decoded
            (
                "1stor%3A%2F%2FDOI",
                "1stor%3A%2F%2FDOI",
            ),
        ),
    )
    def test_get_document_url_with_deeplinking_url(
        self, svc, pyramid_request, url, expected
    ):
        if url:
            pyramid_request.params["url"] = url

        assert svc.get_document_url(pyramid_request) == expected

    def test_get_document_url_with_canvas_files(self, svc, pyramid_request):
        pyramid_request.params["canvas_file"] = "any"
        pyramid_request.params["file_id"] = "FILE_ID"
        pyramid_request.lti_params["custom_canvas_course_id"] = "COURSE_ID"

        result = svc.get_document_url(pyramid_request)

        assert result == "canvas://file/course/COURSE_ID/file_id/FILE_ID"

    @pytest.mark.parametrize("cfi", (None, sentinel.cfi))
    def test_get_document_url_with_legacy_vitalsource_book(
        self, svc, pyramid_request, VSBookLocation, cfi
    ):
        pyramid_request.params["vitalsource_book"] = "any"
        pyramid_request.params["book_id"] = sentinel.book_id
        if cfi:
            pyramid_request.params["cfi"] = cfi

        result = svc.get_document_url(pyramid_request)

        VSBookLocation.assert_called_once_with(book_id=sentinel.book_id, cfi=cfi)
        assert result == VSBookLocation.return_value.document_url

    @pytest.mark.parametrize(
        "param",
        (
            "resource_link_id",
            "ext_d2l_resource_link_id_history",
            "resource_link_id_history",
            "custom_ResourceLink.id.history",
        ),
    )
    def test_get_document_url_with_assignment_in_db(
        self, svc, pyramid_request, assignment_service, param
    ):
        assignment_service.get_assignment.return_value = factories.Assignment(
            document_url=sentinel.document_url
        )
        pyramid_request.lti_params[param] = sentinel.link_id

        result = svc.get_document_url(pyramid_request)

        assignment_service.get_assignment.assert_called_once_with(
            tool_consumer_instance_guid=pyramid_request.lti_params[
                "tool_consumer_instance_guid"
            ],
            resource_link_id=sentinel.link_id,
        )
        assert result == sentinel.document_url

    @pytest.fixture
    def svc(self, assignment_service):
        return DocumentURLService(assignment_service)

    @pytest.fixture
    def assignment_service(self, assignment_service):
        assignment_service.get_assignment.return_value = None
        return assignment_service

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.lti_params = LTIParams({"tool_consumer_instance_guid": "guid"})
        return pyramid_request

    @pytest.fixture
    def VSBookLocation(self, patch):
        return patch("lms.services.document_url.VSBookLocation")


class TestFactory:
    def test_it(self, pyramid_request, DocumentURLService, assignment_service):
        svc = factory(sentinel.context, pyramid_request)

        DocumentURLService.assert_called_once_with(
            assignment_service=assignment_service
        )
        assert svc == DocumentURLService.return_value

    @pytest.fixture
    def DocumentURLService(self, patch):
        return patch("lms.services.document_url.DocumentURLService")
