import pytest

from lms.services import HTTPError
from lms.views.api.blackboard.exceptions import BlackboardFileNotFoundInCourse
from lms.views.api.blackboard.files import BlackboardFilesAPIViews
from tests import factories

pytestmark = pytest.mark.usefixtures("oauth2_token_service", "blackboard_api_client")


class TestListFiles:
    def test_it(
        self,
        view,
        blackboard_api_client,
        BlackboardListFilesSchema,
        blackboard_list_files_schema,
    ):
        files = view()

        blackboard_api_client.request.assert_called_once_with(
            "GET", "courses/uuid:COURSE_ID/resources"
        )
        BlackboardListFilesSchema.assert_called_once_with(
            blackboard_api_client.request.return_value
        )
        assert files == blackboard_list_files_schema.parse.return_value

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.matchdict["course_id"] = "COURSE_ID"
        return pyramid_request

    @pytest.fixture
    def view(self, views):
        return views.list_files


class TestViaURL:
    def test_it(
        self,
        view,
        pyramid_request,
        blackboard_api_client,
        BlackboardPublicURLSchema,
        blackboard_public_url_schema,
        helpers,
    ):
        response = view()

        blackboard_api_client.request.assert_called_once_with(
            "GET", "courses/uuid:COURSE_ID/resources/FILE_ID"
        )
        BlackboardPublicURLSchema.assert_called_once_with(
            blackboard_api_client.request.return_value
        )
        helpers.via_url.assert_called_once_with(
            pyramid_request,
            blackboard_public_url_schema.parse.return_value,
            content_type="pdf",
        )
        assert response == {"via_url": helpers.via_url.return_value}

    def test_it_raises_BlackboardFileNotFoundInCourse_if_the_Blackboard_API_404s(
        self, view, blackboard_api_client
    ):
        blackboard_api_client.request.side_effect = HTTPError(
            factories.requests.Response(status_code=404)
        )

        with pytest.raises(BlackboardFileNotFoundInCourse):
            view()

    def test_it_raises_HTTPError_if_the_Blackboard_API_fails_in_any_other_way(
        self, view, blackboard_api_client
    ):
        blackboard_api_client.request.side_effect = HTTPError(
            factories.requests.Response(status_code=400)
        )

        with pytest.raises(HTTPError):
            view()

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.matchdict["course_id"] = "COURSE_ID"
        pyramid_request.params[
            "document_url"
        ] = "blackboard://content-resource/FILE_ID/"
        return pyramid_request

    @pytest.fixture
    def view(self, views):
        return views.via_url


@pytest.fixture(autouse=True)
def helpers(patch):
    return patch("lms.views.api.blackboard.files.helpers")


@pytest.fixture
def views(pyramid_request):
    return BlackboardFilesAPIViews(pyramid_request)


@pytest.fixture(autouse=True)
def BlackboardListFilesSchema(patch):
    return patch("lms.views.api.blackboard.files.BlackboardListFilesSchema")


@pytest.fixture
def blackboard_list_files_schema(BlackboardListFilesSchema):
    return BlackboardListFilesSchema.return_value


@pytest.fixture(autouse=True)
def BlackboardPublicURLSchema(patch):
    return patch("lms.views.api.blackboard.files.BlackboardPublicURLSchema")


@pytest.fixture
def blackboard_public_url_schema(BlackboardPublicURLSchema):
    return BlackboardPublicURLSchema.return_value
