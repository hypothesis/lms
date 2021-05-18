import pytest

from lms.services import CanvasAPIError
from lms.views.api.canvas.groups import GroupsAPIViews

pytestmark = pytest.mark.usefixtures("canvas_api_client")


class TestListGroupSets:
    def test_it_gets_group_sets_from_canvas(self, canvas_api_client, pyramid_request):
        GroupsAPIViews(pyramid_request).course_group_sets()

        canvas_api_client.course_group_categories.assert_called_once_with(
            "test_course_id"
        )

    def test_it_returns_the_list_of_group_sets(
        self, canvas_api_client, pyramid_request
    ):
        assert (
            GroupsAPIViews(pyramid_request).course_group_sets()
            == canvas_api_client.course_group_categories.return_value
        )

    # CanvasAPIError's are caught and handled by an exception view, so the
    # normal view just lets them raise.
    def test_it_doesnt_catch_CanvasAPIErrors_from_list_group_sets(
        self, canvas_api_client, pyramid_request
    ):
        canvas_api_client.course_group_categories.side_effect = CanvasAPIError("Oops")

        with pytest.raises(CanvasAPIError, match="Oops"):
            GroupsAPIViews(pyramid_request).course_group_sets()

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.matchdict = {"course_id": "test_course_id"}
        return pyramid_request
