import hashlib

import pytest

from lms.services.document_uri import (
    ensure_checkpoint_fingerprint,
    initial_document_uri,
    pdf_fingerprint,
)
from tests import factories


class TestInitialDocumentURI:
    @pytest.mark.parametrize(
        "document_url",
        [
            "https://example.com/article",
            "http://example.com/doc.pdf",
            "HTTPS://EXAMPLE.COM/ARTICLE",
        ],
    )
    def test_http_urls_are_returned_as_is(
        self, pyramid_request, application_instance, document_url
    ):
        assert (
            initial_document_uri(pyramid_request, document_url, application_instance)
            == document_url
        )

    @pytest.mark.parametrize(
        "document_url",
        [
            "https://youtu.be/VIDEO_ID",
            "https://www.youtube.com/watch?v=VIDEO_ID&t=30s",
            "https://www.youtube.com/shorts/VIDEO_ID",
        ],
    )
    def test_youtube_urls_return_the_canonical_video_url(
        self, pyramid_request, application_instance, document_url
    ):
        # Via's YouTube player canonicalizes the URL before the client
        # annotates it, whatever form the instructor pasted.
        document_uri = initial_document_uri(
            pyramid_request, document_url, application_instance
        )

        assert document_uri == "https://www.youtube.com/watch?v=VIDEO_ID"

    def test_youtube_urls_are_returned_as_is_when_youtube_is_disabled(
        self, pyramid_request, application_instance
    ):
        application_instance.settings.set("youtube", "enabled", False)  # noqa: FBT003

        document_uri = initial_document_uri(
            pyramid_request, "https://youtu.be/VIDEO_ID", application_instance
        )

        assert document_uri == "https://youtu.be/VIDEO_ID"

    def test_canvas_pages_return_the_canonical_url(
        self, pyramid_request, application_instance
    ):
        document_uri = initial_document_uri(
            pyramid_request, "canvas://page/course/42/page_id/314", application_instance
        )

        assert document_uri == "https://uni.instructure.com/courses/42/pages/314"

    def test_vitalsource_returns_the_bookshelf_url(
        self, pyramid_request, application_instance
    ):
        document_uri = initial_document_uri(
            pyramid_request,
            "vitalsource://book/bookID/BOOK-ID/cfi//6/8",
            application_instance,
        )

        assert document_uri == "https://bookshelf.vitalsource.com/reader/books/BOOK-ID"

    def test_invalid_vitalsource_urls_return_None(
        self, pyramid_request, application_instance
    ):
        assert (
            initial_document_uri(
                pyramid_request, "vitalsource://nonsense", application_instance
            )
            is None
        )

    def test_canvas_studio_returns_the_canonical_video_url(
        self, pyramid_request, application_instance
    ):
        application_instance.settings.set(
            "canvas_studio", "domain", "uni.instructuremedia.com"
        )

        document_uri = initial_document_uri(
            pyramid_request, "canvas-studio://media/55", application_instance
        )

        assert document_uri == "https://uni.instructuremedia.com/api/public/v1/media/55"

    def test_canvas_studio_without_a_domain_returns_None(
        self, pyramid_request, application_instance
    ):
        assert (
            initial_document_uri(
                pyramid_request, "canvas-studio://media/55", application_instance
            )
            is None
        )

    def test_moodle_pages_return_the_proxy_resolved_url(
        self, pyramid_request, application_instance
    ):
        document_uri = initial_document_uri(
            pyramid_request, "moodle://page/course/42/page_id/860", application_instance
        )

        proxy_url = pyramid_request.route_url("moodle_api.pages.proxy")
        assert document_uri == proxy_url.replace(
            "/proxy", "/uni.instructure.com/mod/page/view.php?id=860"
        )

    @pytest.mark.parametrize(
        "document_url",
        [
            # PDF content: the identity is the fingerprint, which can't be
            # derived from the URL (see ensure_checkpoint_fingerprint).
            "canvas://file/course/42/file_id/99",
            "blackboard://content-resource/FILE_ID/",
            "d2l://file/course/42/file_id/99/",
            "moodle://file/course/42/url/https%3A%2F%2Fmoodle.com%2Ffile.pdf",
            "jstor://10.2307/1234",
        ],
    )
    def test_urls_with_no_derivable_identity_return_None(
        self, pyramid_request, application_instance, document_url
    ):
        assert (
            initial_document_uri(pyramid_request, document_url, application_instance)
            is None
        )

    @pytest.fixture
    def application_instance(self):
        return factories.ApplicationInstance(lms_url="https://uni.instructure.com")


@pytest.mark.usefixtures("canvas_service", "http_service")
class TestEnsureCheckpointFingerprint:
    @pytest.mark.usefixtures("user_is_instructor")
    def test_it_computes_and_stores_the_fingerprint(
        self, pyramid_request, assignment, course, canvas_service, http_service
    ):
        http_service.get.return_value.content = PDF_WITH_HEX_ID

        ensure_checkpoint_fingerprint(pyramid_request, assignment, course)

        canvas_service.public_url_for_file.assert_called_once_with(
            assignment, "99", "CANVAS_COURSE_ID"
        )
        http_service.get.assert_called_once_with(
            canvas_service.public_url_for_file.return_value
        )
        assert (
            assignment.document_uri == f"urn:x-pdf:{pdf_fingerprint(PDF_WITH_HEX_ID)}"
        )

    @pytest.mark.usefixtures("user_is_instructor")
    def test_it_does_nothing_if_document_uri_is_already_set(
        self, pyramid_request, assignment, course, canvas_service
    ):
        assignment.document_uri = "urn:x-pdf:already-there"

        ensure_checkpoint_fingerprint(pyramid_request, assignment, course)

        canvas_service.public_url_for_file.assert_not_called()
        assert assignment.document_uri == "urn:x-pdf:already-there"

    @pytest.mark.usefixtures("user_is_learner")
    def test_it_does_nothing_for_non_instructors(
        self, pyramid_request, assignment, course, canvas_service
    ):
        ensure_checkpoint_fingerprint(pyramid_request, assignment, course)

        canvas_service.public_url_for_file.assert_not_called()
        assert assignment.document_uri is None

    @pytest.mark.usefixtures("user_is_instructor")
    def test_it_computes_the_fingerprint_for_blackboard_files(
        self, pyramid_request, assignment, course, blackboard_api_client, http_service
    ):
        assignment.document_url = "blackboard://content-resource/FILE_ID/"
        http_service.get.return_value.content = PDF_WITH_HEX_ID

        ensure_checkpoint_fingerprint(pyramid_request, assignment, course)

        blackboard_api_client.public_url.assert_called_once_with(
            course.lms_id, "FILE_ID"
        )
        assert (
            assignment.document_uri == f"urn:x-pdf:{pdf_fingerprint(PDF_WITH_HEX_ID)}"
        )

    @pytest.mark.usefixtures("user_is_instructor", "oauth2_token_service")
    def test_it_computes_the_fingerprint_for_d2l_files(
        self,
        pyramid_request,
        assignment,
        course,
        d2l_api_client,
        http_service,
        oauth_token,
    ):
        assignment.document_url = "d2l://file/course/42/file_id/99/"
        http_service.get.return_value.content = PDF_WITH_HEX_ID

        ensure_checkpoint_fingerprint(pyramid_request, assignment, course)

        d2l_api_client.public_url.assert_called_once_with(course.lms_id, "99")
        http_service.get.assert_called_once_with(
            d2l_api_client.public_url.return_value,
            headers={"Authorization": f"Bearer {oauth_token.access_token}"},
        )
        assert (
            assignment.document_uri == f"urn:x-pdf:{pdf_fingerprint(PDF_WITH_HEX_ID)}"
        )

    @pytest.mark.usefixtures("user_is_instructor")
    def test_it_computes_the_fingerprint_for_moodle_files(
        self, pyramid_request, assignment, course, moodle_api_client, http_service
    ):
        assignment.document_url = (
            "moodle://file/course/42/url/https://moodle.com/file.pdf"
        )
        http_service.get.return_value.content = PDF_WITH_HEX_ID

        ensure_checkpoint_fingerprint(pyramid_request, assignment, course)

        http_service.get.assert_called_once_with(
            "https://moodle.com/file.pdf", params={"token": moodle_api_client.token}
        )
        assert (
            assignment.document_uri == f"urn:x-pdf:{pdf_fingerprint(PDF_WITH_HEX_ID)}"
        )

    @pytest.mark.usefixtures("user_is_instructor")
    def test_it_computes_the_fingerprint_for_jstor(
        self, pyramid_request, assignment, course, jstor_service, http_service
    ):
        assignment.document_url = "jstor://10.2307/1234"
        jstor_service.enabled = True
        http_service.get.return_value.content = PDF_WITH_HEX_ID

        ensure_checkpoint_fingerprint(pyramid_request, assignment, course)

        jstor_service.public_url.assert_called_once_with("jstor://10.2307/1234")
        http_service.get.assert_called_once_with(jstor_service.public_url.return_value)
        assert (
            assignment.document_uri == f"urn:x-pdf:{pdf_fingerprint(PDF_WITH_HEX_ID)}"
        )

    @pytest.mark.usefixtures("user_is_instructor")
    def test_it_does_nothing_for_jstor_when_disabled(
        self, pyramid_request, assignment, course, jstor_service, http_service
    ):
        assignment.document_url = "jstor://10.2307/1234"
        jstor_service.enabled = False

        ensure_checkpoint_fingerprint(pyramid_request, assignment, course)

        http_service.get.assert_not_called()
        assert assignment.document_uri is None

    @pytest.mark.usefixtures("user_is_instructor")
    def test_it_does_nothing_for_non_file_urls(
        self, pyramid_request, assignment, course, canvas_service, http_service
    ):
        assignment.document_url = "moodle://page/course/42/page_id/314"

        ensure_checkpoint_fingerprint(pyramid_request, assignment, course)

        canvas_service.public_url_for_file.assert_not_called()
        http_service.get.assert_not_called()
        assert assignment.document_uri is None

    @pytest.mark.usefixtures("user_is_instructor")
    def test_it_swallows_errors(
        self, pyramid_request, assignment, course, canvas_service
    ):
        canvas_service.public_url_for_file.side_effect = RuntimeError("API is down")

        ensure_checkpoint_fingerprint(pyramid_request, assignment, course)

        assert assignment.document_uri is None

    @pytest.fixture
    def assignment(self):
        return factories.Assignment(
            document_url="canvas://file/course/42/file_id/99", checkpoint_enabled=True
        )

    @pytest.fixture
    def course(self):
        course = factories.Course()
        course.extra = {"canvas": {"custom_canvas_course_id": "CANVAS_COURSE_ID"}}
        return course


# A minimal classic-trailer PDF tail with a hex /ID.
PDF_WITH_HEX_ID = (
    b"%PDF-1.4\nsome pdf content here\n"
    b"trailer\n<< /Size 10 /Root 1 0 R /ID [<DEADBEEFDEADBEEFDEADBEEFDEADBEEF>"
    b"<CAFEBABECAFEBABECAFEBABECAFEBABE>] >>\nstartxref\n123\n%%EOF\n"
)


class TestPDFFingerprint:
    def test_it_uses_the_original_id_when_present(self):
        assert pdf_fingerprint(PDF_WITH_HEX_ID) == "deadbeefdeadbeefdeadbeefdeadbeef"

    def test_it_uses_the_last_id_in_the_file(self):
        # Incremental updates append a new trailer: the last one wins.
        pdf = (
            b"%PDF-1.4\n"
            b"trailer\n<< /ID [<11111111111111111111111111111111>"
            b"<11111111111111111111111111111111>] >>\n%%EOF\n"
            b"trailer\n<< /ID [<22222222222222222222222222222222>"
            b"<33333333333333333333333333333333>] >>\n%%EOF\n"
        )

        assert pdf_fingerprint(pdf) == "22222222222222222222222222222222"

    def test_it_allows_whitespace_inside_hex_ids(self):
        pdf = b"/ID [ <DEAD BEEF\nDEAD BEEF DEAD BEEF DEAD BEEF> <00> ]"

        assert pdf_fingerprint(pdf) == "deadbeefdeadbeefdeadbeefdeadbeef"

    def test_it_pads_odd_length_hex_ids(self):
        # Per the PDF spec an odd number of hex digits gets a trailing 0.
        pdf = b"/ID [<DEADBEE><00>]"

        assert pdf_fingerprint(pdf) == "deadbee0"

    def test_it_decodes_literal_string_ids(self):
        pdf = rb"/ID [(AB\\C\)D\101) (other)]"

        assert pdf_fingerprint(pdf) == b"AB\\C)DA".hex()

    def test_it_falls_back_to_md5_when_there_is_no_id(self):
        pdf = b"%PDF-1.4\nno id in this file\n" * 100

        assert (
            pdf_fingerprint(pdf) == hashlib.md5(pdf[:1024]).hexdigest()  # noqa: S324
        )

    def test_it_falls_back_to_md5_when_the_id_is_all_zeroes(self):
        # Same validation as PDF.js: an all-NUL 16-byte ID is "empty".
        pdf = b"/ID [<00000000000000000000000000000000><00>]"

        assert (
            pdf_fingerprint(pdf) == hashlib.md5(pdf[:1024]).hexdigest()  # noqa: S324
        )

    def test_it_falls_back_to_md5_when_the_id_is_empty(self):
        pdf = b"/ID [<><>]"

        assert (
            pdf_fingerprint(pdf) == hashlib.md5(pdf[:1024]).hexdigest()  # noqa: S324
        )
