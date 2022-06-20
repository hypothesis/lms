from unittest.mock import create_autospec, sentinel

import pytest

from lms.models import LTIParams
from lms.resources import LTILaunchResource
from lms.services import DocumentURLService
from lms.services.document_url import factory
from tests import factories


class TestDocumentURLService:
    def test_get_document_url(self, svc, context, pyramid_request):
        assert not svc.get_document_url(context, pyramid_request)

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
                "http%3a%2F%2Fexample.com%2Fpath%3Fparam%3Dvalue",
                "http://example.com/path?param=value",
            ),
            (
                "canvas%3A%2F%2Ffile%2Fcourse_id%2FCOURSE_ID%2Ffile_if%2FFILE_ID",
                "canvas://file/course_id/COURSE_ID/file_if/FILE_ID",
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
        ),
    )
    def test_get_document_url_with_deeplinking_url(
        self, svc, context, pyramid_request, url, expected
    ):
        if url:
            pyramid_request.params["url"] = url

        assert svc.get_document_url(context, pyramid_request) == expected

    def test_get_document_url_with_canvas_files(self, svc, context, pyramid_request):
        pyramid_request.params["canvas_file"] = "any"
        pyramid_request.params["file_id"] = "FILE_ID"
        context.lti_params["custom_canvas_course_id"] = "COURSE_ID"

        result = svc.get_document_url(context, pyramid_request)

        assert result == "canvas://file/course/COURSE_ID/file_id/FILE_ID"

    @pytest.mark.parametrize("cfi", (None, sentinel.cfi))
    def test_get_document_url_with_legacy_vitalsource_book(
        self, svc, context, pyramid_request, VitalSourceService, cfi
    ):
        pyramid_request.params["vitalsource_book"] = "any"
        pyramid_request.params["book_id"] = sentinel.book_id
        if cfi:
            pyramid_request.params["cfi"] = cfi

        result = svc.get_document_url(context, pyramid_request)

        VitalSourceService.generate_document_url.assert_called_once_with(
            book_id=sentinel.book_id, cfi=cfi
        )
        assert result == VitalSourceService.generate_document_url.return_value

    @pytest.mark.parametrize(
        "param",
        (
            "resource_link_id",
            "ext_d2l_resource_link_id_history",
            "resource_link_id_history",
        ),
    )
    def test_get_document_url_with_assignment_in_db(
        self, svc, context, pyramid_request, assignment_service, param
    ):
        assignment_service.get_assignment.return_value = factories.Assignment(
            document_url=sentinel.document_url
        )
        context.lti_params[param] = sentinel.link_id
        # Horrible work around
        if param == "resource_link_id":
            context.resource_link_id = sentinel.link_id
        else:
            context.resource_link_id = None

        result = svc.get_document_url(context, pyramid_request)

        assignment_service.get_assignment.assert_called_once_with(
            tool_consumer_instance_guid=context.lti_params[
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
    def context(self):
        context = create_autospec(LTILaunchResource, spec_set=True, instance=True)
        context.lti_params = LTIParams({"tool_consumer_instance_guid": "guid"})
        return context

    @pytest.fixture
    def VitalSourceService(self, patch):
        return patch("lms.services.document_url.VitalSourceService")


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
