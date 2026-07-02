from unittest.mock import MagicMock

import pytest
from pyramid.httpexceptions import HTTPForbidden, HTTPNotFound

from lms.models import Grouping
from lms.services import HAPI
from lms.views.api.checkpoint import reveal_checkpoint


@pytest.mark.usefixtures("assignment_service", "h_api")
class TestRevealCheckpoint:
    def test_it_rejects_non_instructors(self, pyramid_request):
        pyramid_request.matchdict = {"assignment_id": "1"}

        with pytest.raises(HTTPForbidden):
            reveal_checkpoint(pyramid_request)

    @pytest.mark.usefixtures("user_is_instructor")
    def test_it_reveals_checkpoint_via_h(
        self, pyramid_request, assignment_service, h_api
    ):
        assignment = self._assignment_with_checkpoint()
        assignment_service.get_by_id.return_value = assignment
        h_api.reveal_checkpoints.return_value = [
            {"revealed": True, "reveal_date": "2026-07-01T12:00:00"}
        ]
        pyramid_request.matchdict = {"assignment_id": "1"}

        result = reveal_checkpoint(pyramid_request)

        assignment_service.get_by_id.assert_called_once_with(1)
        assert result["revealed"] is True
        assert result["reveal_date"] == "2026-07-01T12:00:00"
        h_api.reveal_checkpoints.assert_called_once()

    @pytest.mark.usefixtures("user_is_instructor")
    def test_it_returns_404_when_assignment_not_found(
        self, pyramid_request, assignment_service
    ):
        assignment_service.get_by_id.return_value = None
        pyramid_request.matchdict = {"assignment_id": "999"}

        with pytest.raises(HTTPNotFound):
            reveal_checkpoint(pyramid_request)

    @pytest.mark.usefixtures("user_is_instructor")
    def test_it_returns_404_when_checkpoint_not_enabled(
        self, pyramid_request, assignment_service
    ):
        assignment = MagicMock()
        assignment.checkpoint_enabled = False
        assignment_service.get_by_id.return_value = assignment
        pyramid_request.matchdict = {"assignment_id": "1"}

        with pytest.raises(HTTPNotFound):
            reveal_checkpoint(pyramid_request)

    @pytest.mark.usefixtures("user_is_instructor")
    def test_it_reveals_only_non_course_groupings(
        self, pyramid_request, assignment_service, h_api
    ):
        assignment = self._assignment_with_checkpoint()
        course_grouping = MagicMock()
        course_grouping.type = Grouping.Type.COURSE
        course_grouping.authority_provided_id = "course1"
        section_grouping = MagicMock()
        section_grouping.type = Grouping.Type.CANVAS_SECTION
        section_grouping.authority_provided_id = "section1"
        assignment.groupings.all.return_value = [course_grouping, section_grouping]
        assignment_service.get_by_id.return_value = assignment
        h_api.reveal_checkpoints.return_value = [
            {"revealed": True, "reveal_date": "2026-07-01T12:00:00"}
        ]
        pyramid_request.matchdict = {"assignment_id": "1"}

        reveal_checkpoint(pyramid_request)

        call_kwargs = h_api.reveal_checkpoints.call_args[1]
        assert len(call_kwargs["checkpoints"]) == 1
        assert (
            call_kwargs["checkpoints"][0]["group_authority_provided_id"] == "section1"
        )

    @pytest.mark.usefixtures("user_is_instructor")
    def test_it_returns_null_reveal_date_when_no_result_revealed(
        self, pyramid_request, assignment_service, h_api
    ):
        assignment = self._assignment_with_checkpoint()
        assignment_service.get_by_id.return_value = assignment
        h_api.reveal_checkpoints.return_value = [{"revealed": False}]
        pyramid_request.matchdict = {"assignment_id": "1"}

        result = reveal_checkpoint(pyramid_request)

        assert result["revealed"] is True
        assert result["reveal_date"] is None

    @pytest.mark.usefixtures("user_is_instructor")
    def test_it_returns_404_when_no_groupings(
        self, pyramid_request, assignment_service
    ):
        assignment = self._assignment_with_checkpoint()
        assignment.groupings.all.return_value = []
        assignment_service.get_by_id.return_value = assignment
        pyramid_request.matchdict = {"assignment_id": "1"}

        with pytest.raises(HTTPNotFound):
            reveal_checkpoint(pyramid_request)

    def _assignment_with_checkpoint(self):
        assignment = MagicMock()
        assignment.checkpoint_enabled = True
        assignment.document_url = "https://example.com/doc"
        grouping = MagicMock()
        grouping.type = Grouping.Type.CANVAS_SECTION
        grouping.authority_provided_id = "group1"
        assignment.groupings.all.return_value = [grouping]
        return assignment

    @pytest.fixture
    def h_api(self, mock_service):
        return mock_service(HAPI)

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.matchdict = {}
        return pyramid_request
