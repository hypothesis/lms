from contextlib import contextmanager

import pytest

from lms.models import AssignmentGrouping
from lms.tasks.checkpoint import fingerprint_checkpoint_document
from tests import factories


class TestFingerprintCheckpointDocument:
    def test_it_identifies_the_document_and_creates_the_checkpoint(
        self, assignment, http_service, h_api, pdf_fingerprint, section
    ):
        fingerprint_checkpoint_document(
            assignment_id=assignment.id, public_url="https://example.com/file.pdf"
        )

        http_service.get.assert_called_once_with("https://example.com/file.pdf")
        assert assignment.document_uri == f"urn:x-pdf:{pdf_fingerprint.return_value}"
        h_api.sync_checkpoints.assert_called_once_with(
            checkpoints=[
                {
                    "group_authority_provided_id": section.authority_provided_id,
                    "document_uri": assignment.document_uri,
                }
            ]
        )

    def test_it_uses_the_course_when_there_are_no_other_groupings(
        self,
        assignment,
        course,
        h_api,
        section,
        db_session,
        http_service,  # noqa: ARG002
        pdf_fingerprint,  # noqa: ARG002
    ):
        # A course's checkpoint is shared with every assignment on the same
        # document, so it is only the fallback.
        db_session.query(AssignmentGrouping).filter_by(
            assignment_id=assignment.id, grouping_id=section.id
        ).delete()
        db_session.flush()

        fingerprint_checkpoint_document(
            assignment_id=assignment.id, public_url="https://example.com/file.pdf"
        )

        h_api.sync_checkpoints.assert_called_once_with(
            checkpoints=[
                {
                    "group_authority_provided_id": course.authority_provided_id,
                    "document_uri": assignment.document_uri,
                }
            ]
        )

    def test_it_does_nothing_when_the_document_is_already_identified(
        self, assignment, http_service, h_api, db_session
    ):
        # Every viewer queues this until it lands, so most runs find the work
        # already done by an earlier one.
        assignment.document_uri = "urn:x-pdf:already"
        db_session.flush()

        fingerprint_checkpoint_document(
            assignment_id=assignment.id, public_url="https://example.com/file.pdf"
        )

        http_service.get.assert_not_called()
        h_api.sync_checkpoints.assert_not_called()

    def test_it_does_nothing_when_the_assignment_is_gone(self, http_service, h_api):
        fingerprint_checkpoint_document(
            assignment_id=1234567890, public_url="https://example.com/file.pdf"
        )

        http_service.get.assert_not_called()
        h_api.sync_checkpoints.assert_not_called()

    @pytest.fixture
    def course(self, application_instance):
        return factories.Course(application_instance=application_instance)

    @pytest.fixture
    def section(self, application_instance):
        return factories.CanvasSection(application_instance=application_instance)

    @pytest.fixture
    def assignment(self, course, section, db_session):
        assignment = factories.Assignment(
            course=course,
            checkpoint_enabled=True,
            document_url="canvas://file/course/1/file_id/2",
        )
        factories.AssignmentGrouping(assignment=assignment, grouping=course)
        factories.AssignmentGrouping(assignment=assignment, grouping=section)
        db_session.flush()
        return assignment

    @pytest.fixture
    def pdf_fingerprint(self, patch):
        return patch("lms.tasks.checkpoint.pdf_fingerprint")


@pytest.fixture(autouse=True)
def app(patch, pyramid_request):
    app = patch("lms.tasks.checkpoint.app")

    @contextmanager
    def request_context():
        yield pyramid_request

    app.request_context = request_context

    return app
