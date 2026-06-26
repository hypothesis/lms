from datetime import datetime
from unittest.mock import MagicMock, create_autospec, sentinel

import pytest

from lms.models.assignment import Assignment
from lms.models.assignment_checkpoint import AssignmentCheckpoint
from lms.views.api.checkpoint import reveal_checkpoint


@pytest.mark.usefixtures("assignment_service", "h_api", "user_is_instructor")
class TestRevealCheckpoint:
    def test_it_rejects_non_instructors(self, pyramid_request, user_is_learner):
        pyramid_request.matchdict = {"assignment_id": "1"}

        result = reveal_checkpoint(pyramid_request)

        assert pyramid_request.response.status_code == 403
        assert "error" in result

    def test_it_reveals_an_unrevealed_checkpoint(
        self, pyramid_request, assignment_service, h_api
    ):
        assignment = self._assignment_with_checkpoint(reveal_date=None)
        assignment_service.get_by_id.return_value = assignment
        pyramid_request.matchdict = {"assignment_id": "1"}

        result = reveal_checkpoint(pyramid_request)

        assignment_service.get_by_id.assert_called_once_with(1)
        assert result["revealed"] is True
        assert "reveal_date" in result
        h_api.sync_checkpoints.assert_called_once()

    def test_it_returns_already_revealed(
        self, pyramid_request, assignment_service, h_api
    ):
        assignment = self._assignment_with_checkpoint(
            reveal_date=datetime(2026, 7, 1, 12, 0, 0)  # noqa: DTZ001
        )
        assignment_service.get_by_id.return_value = assignment
        pyramid_request.matchdict = {"assignment_id": "1"}

        result = reveal_checkpoint(pyramid_request)

        assert result["revealed"] is True
        assert "reveal_date" in result
        h_api.sync_checkpoints.assert_not_called()

    def test_it_returns_404_when_assignment_not_found(
        self, pyramid_request, assignment_service
    ):
        assignment_service.get_by_id.return_value = None
        pyramid_request.matchdict = {"assignment_id": "999"}

        result = reveal_checkpoint(pyramid_request)

        assert pyramid_request.response.status_code == 404
        assert "error" in result

    def test_it_returns_404_when_no_checkpoint(
        self, pyramid_request, assignment_service
    ):
        assignment = MagicMock()
        assignment.checkpoint = None
        assignment_service.get_by_id.return_value = assignment
        pyramid_request.matchdict = {"assignment_id": "1"}

        result = reveal_checkpoint(pyramid_request)

        assert pyramid_request.response.status_code == 404
        assert "error" in result

    def test_it_syncs_checkpoints_to_h(
        self, pyramid_request, assignment_service, h_api
    ):
        assignment = self._assignment_with_checkpoint(reveal_date=None)
        grouping = MagicMock()
        grouping.authority_provided_id = "group1"
        assignment.groupings.all.return_value = [grouping]
        assignment.document_url = "https://example.com/doc"
        assignment_service.get_by_id.return_value = assignment
        pyramid_request.matchdict = {"assignment_id": "1"}

        reveal_checkpoint(pyramid_request)

        h_api.sync_checkpoints.assert_called_once()
        call_kwargs = h_api.sync_checkpoints.call_args[1]
        assert call_kwargs["authority"] == "lms.hypothes.is"
        assert len(call_kwargs["checkpoints"]) == 1
        assert call_kwargs["checkpoints"][0]["group_authority_provided_id"] == "group1"
        assert call_kwargs["checkpoints"][0]["document_uri"] == "https://example.com/doc"

    def test_it_does_not_sync_when_no_groupings(
        self, pyramid_request, assignment_service, h_api
    ):
        assignment = self._assignment_with_checkpoint(reveal_date=None)
        assignment.groupings.all.return_value = []
        assignment_service.get_by_id.return_value = assignment
        pyramid_request.matchdict = {"assignment_id": "1"}

        reveal_checkpoint(pyramid_request)

        h_api.sync_checkpoints.assert_not_called()

    def _assignment_with_checkpoint(self, reveal_date):
        assignment = MagicMock()
        checkpoint = MagicMock()
        checkpoint.reveal_date = reveal_date
        assignment.checkpoint = checkpoint
        assignment.document_url = "https://example.com/doc"
        grouping = MagicMock()
        grouping.authority_provided_id = "group1"
        assignment.groupings.all.return_value = [grouping]
        return assignment

    @pytest.fixture
    def h_api(self, mock_service):
        from lms.services import HAPI

        return mock_service(HAPI)

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.matchdict = {}
        return pyramid_request
