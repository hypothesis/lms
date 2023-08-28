from unittest.mock import sentinel

import pytest

from lms.services.document import DocumentService, factory


class TestDocumentService:
    @pytest.mark.parametrize(
        "url,course_id,file_id",
        [
            ("canvas://file/course/COURSE_ID/file_id/FILE_ID", "COURSE_ID", "FILE_ID"),
            ("d2l://file/course/COURSE_ID/file_id/FILE_ID/", "COURSE_ID", "FILE_ID"),
            ("blackboard://content-resource/FILE_ID/", None, "FILE_ID"),
            ("unknown://NO_COURSE/NO_FILE/", None, None),
        ],
    )
    def test_get_document_url_parts(self, svc, url, course_id, file_id):
        parts = svc.get_document_url_parts(url)

        if file_id:
            assert parts.course_id == course_id
            assert parts.file_id == file_id
        else:
            assert not parts

    @pytest.fixture
    def svc(self):
        return DocumentService()


class TestServiceFactory:
    def test_it(self, pyramid_request, DocumentService):
        svc = factory(sentinel.context, pyramid_request)

        DocumentService.assert_called_once()
        assert svc == DocumentService.return_value

    @pytest.fixture
    def DocumentService(self, patch):
        return patch("lms.services.document.DocumentService")
