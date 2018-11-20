# -*- coding: utf-8 -*-

import json
from unittest import mock
import pytest

from pyramid.httpexceptions import HTTPBadRequest

from requests import ConnectionError
from requests import HTTPError
from requests import ReadTimeout
from requests import Response
from requests import TooManyRedirects

from lms.views import HAPIError
from lms.views.decorators import h_api
from lms.util import MissingToolConsumerIntanceGUIDError
from lms.util import MissingUserIDError
from lms.models import CourseGroup


@pytest.mark.usefixtures("post")
class TestCreateHUser:
    def test_it_raises_if_post_raises(self, create_h_user, pyramid_request, post):
        post.side_effect = HAPIError("Oops")

        with pytest.raises(HAPIError, match="Oops"):
            create_h_user(pyramid_request, mock.sentinel.jwt)

    def test_it_continues_to_the_wrapped_func_if_feature_not_enabled(
        self, create_h_user, pyramid_request, wrapped
    ):
        pyramid_request.params["oauth_consumer_key"] = "foo"

        returned = create_h_user(pyramid_request, mock.sentinel.jwt)

        wrapped.assert_called_once_with(pyramid_request, mock.sentinel.jwt)
        assert returned == wrapped.return_value

    def test_it_doesnt_use_the_h_api_if_feature_not_enabled(
        self, create_h_user, post, pyramid_request
    ):
        pyramid_request.params["oauth_consumer_key"] = "foo"

        create_h_user(pyramid_request, mock.sentinel.jwt)

        assert not post.called

    def test_it_400s_if_generate_username_raises_MissingToolConsumerInstanceGUIDError(
        self, create_h_user, pyramid_request, util
    ):
        util.generate_username.side_effect = MissingToolConsumerIntanceGUIDError()

        with pytest.raises(HTTPBadRequest, match="tool_consumer_instance_guid"):
            create_h_user(pyramid_request, mock.sentinel.jwt)

    def test_it_400s_if_generate_username_raises_MissingUserIDError(
        self, create_h_user, pyramid_request, util
    ):
        util.generate_username.side_effect = MissingUserIDError()

        with pytest.raises(HTTPBadRequest, match="user_id"):
            create_h_user(pyramid_request, mock.sentinel.jwt)

    def test_it_400s_if_generate_provider_raises_MissingToolConsumerInstanceGUIDError(
        self, create_h_user, pyramid_request, util
    ):
        util.generate_provider.side_effect = MissingToolConsumerIntanceGUIDError()

        with pytest.raises(HTTPBadRequest, match="tool_consumer_instance_guid"):
            create_h_user(pyramid_request, mock.sentinel.jwt)

    def test_it_400s_if_generate_provider_unique_id_raises_MissingUserIDError(
        self, create_h_user, pyramid_request, util
    ):
        util.generate_provider_unique_id.side_effect = MissingUserIDError()

        with pytest.raises(HTTPBadRequest, match="user_id"):
            create_h_user(pyramid_request, mock.sentinel.jwt)

    def test_it_creates_the_user_in_h(self, create_h_user, post, pyramid_request):
        create_h_user(pyramid_request, mock.sentinel.jwt)

        post.assert_called_once_with(
            pyramid_request.registry.settings,
            "/users",
            {
                "username": "test_username",
                "display_name": "test_display_name",
                "authority": "TEST_AUTHORITY",
                "identities": [
                    {
                        "provider": "test_provider",
                        "provider_unique_id": "test_provider_unique_id",
                    }
                ],
            },
            statuses=[409],
        )

    def test_it_continues_to_the_wrapped_function(
        self, create_h_user, pyramid_request, wrapped
    ):
        returned = create_h_user(pyramid_request, mock.sentinel.jwt)

        wrapped.assert_called_once_with(pyramid_request, mock.sentinel.jwt)
        assert returned == wrapped.return_value

    @pytest.fixture
    def create_h_user(self, wrapped):
        # Return the actual wrapper function so that tests can call it directly.
        return h_api.create_h_user(wrapped)


@pytest.mark.usefixtures("post")
class TestCreateCourseGroup:
    @pytest.mark.parametrize(
        "required_param_name", ("tool_consumer_instance_guid", "context_id", "roles")
    )
    def test_it_400s_if_theres_a_required_param_missing(
        self, create_course_group, pyramid_request, required_param_name
    ):
        del pyramid_request.params[required_param_name]

        with pytest.raises(HTTPBadRequest, match=required_param_name):
            create_course_group(pyramid_request, mock.sentinel.jwt)

    def test_it_400s_if_the_user_isnt_allowed_to_create_groups(
        self, create_course_group, pyramid_request
    ):
        pyramid_request.params["roles"] = "Learner"

        with pytest.raises(
            HTTPBadRequest, match="Instructor must launch assignment first"
        ):
            create_course_group(pyramid_request, mock.sentinel.jwt)

    def test_it_does_nothing_if_the_user_isnt_allowed_to_create_groups_but_the_group_already_exists(
        self, create_course_group, pyramid_request, models, post, wrapped
    ):
        models.CourseGroup.get.return_value = mock.create_autospec(
            CourseGroup, instance=True
        )
        pyramid_request.params["roles"] = "Learner"

        returned = create_course_group(pyramid_request, mock.sentinel.jwt)

        assert not post.called
        assert not pyramid_request.db.add.called
        wrapped.assert_called_once_with(pyramid_request, mock.sentinel.jwt)
        assert returned == wrapped.return_value

    def test_it_does_nothing_if_the_feature_isnt_enabled(
        self, create_course_group, pyramid_request, wrapped, post
    ):
        # If the auto provisioning feature isn't enabled for this application
        # instance then create_course_group() doesn't do anything - just calls the
        # wrapped view.
        pyramid_request.params["oauth_consumer_key"] = "foo"

        returned = create_course_group(pyramid_request, mock.sentinel.jwt)

        assert not post.called
        assert not pyramid_request.db.add.called
        wrapped.assert_called_once_with(pyramid_request, mock.sentinel.jwt)
        assert returned == wrapped.return_value

    def test_it_does_nothing_if_the_course_group_already_exists(
        self, create_course_group, models, pyramid_request, wrapped, post
    ):
        models.CourseGroup.get.return_value = mock.create_autospec(
            CourseGroup, instance=True
        )

        returned = create_course_group(pyramid_request, mock.sentinel.jwt)

        assert not post.called
        assert not pyramid_request.db.add.called
        wrapped.assert_called_once_with(pyramid_request, mock.sentinel.jwt)
        assert returned == wrapped.return_value

    def test_it_posts_to_the_group_create_api(
        self, create_course_group, pyramid_request, post
    ):
        create_course_group(pyramid_request, mock.sentinel.jwt)

        post.assert_called_once_with(
            pyramid_request.registry.settings,
            "/groups",
            {"name": "test_group_name"},
            "test_username",
        )

    def test_it_raises_if_post_raises(self, create_course_group, pyramid_request, post):
        post.side_effect = HAPIError("Oops")

        with pytest.raises(HAPIError, match="Oops"):
            create_course_group(pyramid_request, mock.sentinel.jwt)

    def test_it_saves_the_group_to_the_db(
        self, create_course_group, pyramid_request, models
    ):
        # It saves a record of the created group to the DB so that next time
        # this course is used it'll retrieve it from the DB and know not to
        # create another group for the same course.
        create_course_group(pyramid_request, mock.sentinel.jwt)

        class CourseGroupMatcher:
            """An object equal to any other object with matching CourseGroup properties."""

            def __init__(self, pubid, tool_consumer_instance_guid, context_id):
                self.pubid = pubid
                self.tool_consumer_instance_guid = tool_consumer_instance_guid
                self.context_id = context_id

            def __eq__(self, other):
                return all(
                    (
                        other.pubid == self.pubid,
                        other.tool_consumer_instance_guid
                        == self.tool_consumer_instance_guid,
                        other.context_id == self.context_id,
                    )
                )

        pyramid_request.db.add.assert_called_once_with(
            CourseGroupMatcher(
                pubid="TEST_PUBID",
                tool_consumer_instance_guid="TEST_GUID",
                context_id="TEST_CONTEXT",
            )
        )

    def test_it_calls_and_returns_the_wrapped_view(
        self, create_course_group, pyramid_request, wrapped
    ):
        returned = create_course_group(pyramid_request, mock.sentinel.jwt)

        wrapped.assert_called_once_with(pyramid_request, mock.sentinel.jwt)
        assert returned == wrapped.return_value

    @pytest.fixture
    def create_course_group(self, wrapped):
        # Return the actual wrapper function so that tests can call it directly.
        return h_api.create_course_group(wrapped)


@pytest.mark.usefixtures("post")
class TestAddUserToGroup:
    def test_it_doesnt_post_to_the_api_if_feature_not_enabled(
        self, add_user_to_group, pyramid_request, post
    ):
        pyramid_request.params["oauth_consumer_key"] = "foo"

        add_user_to_group(pyramid_request, mock.sentinel.jwt)

        post.assert_not_called()

    def test_it_continues_to_the_wrapped_func_if_feature_not_enabled(
        self, add_user_to_group, pyramid_request, wrapped
    ):
        pyramid_request.params["oauth_consumer_key"] = "foo"

        returned = add_user_to_group(pyramid_request, mock.sentinel.jwt)

        wrapped.assert_called_once_with(pyramid_request, mock.sentinel.jwt)
        assert returned == wrapped.return_value

    @pytest.mark.parametrize(
        "required_param_name", ("tool_consumer_instance_guid", "context_id")
    )
    def test_it_400s_if_theres_a_required_param_missing(
        self, add_user_to_group, pyramid_request, required_param_name
    ):
        del pyramid_request.params[required_param_name]

        with pytest.raises(HTTPBadRequest, match=required_param_name):
            add_user_to_group(pyramid_request, mock.sentinel.jwt)

    def test_it_raises_if_the_group_doesnt_exist(
        self, add_user_to_group, pyramid_request, models
    ):
        models.CourseGroup.get.return_value = None

        with pytest.raises(AssertionError, match="group should never be None"):
            add_user_to_group(pyramid_request, mock.sentinel.jwt)

    def test_it_gets_the_group_from_the_db(
        self, add_user_to_group, models, pyramid_request
    ):
        add_user_to_group(pyramid_request, mock.sentinel.jwt)

        models.CourseGroup.get.assert_called_once_with(
            pyramid_request.db, "test_tool_consumer_instance_guid", "test_context_id"
        )

    def test_it_adds_the_user_to_the_group(
        self, add_user_to_group, pyramid_request, post
    ):
        add_user_to_group(pyramid_request, mock.sentinel.jwt)

        post.assert_called_once_with(
            pyramid_request.registry.settings,
            "/groups/test_pubid/members/acct:test_username@TEST_AUTHORITY",
        )

    def test_it_raises_if_post_raises(self, add_user_to_group, pyramid_request, post):
        post.side_effect = HAPIError("Oops")

        with pytest.raises(HAPIError, match="Oops"):
            add_user_to_group(pyramid_request, mock.sentinel.jwt)

    def test_it_continues_to_the_wrapped_func(
        self, add_user_to_group, pyramid_request, wrapped
    ):
        returned = add_user_to_group(pyramid_request, mock.sentinel.jwt)

        wrapped.assert_called_once_with(pyramid_request, mock.sentinel.jwt)
        assert returned == wrapped.return_value

    @pytest.fixture
    def add_user_to_group(self, wrapped):
        # Return the actual wrapper function so that tests can call it directly.
        return h_api.add_user_to_group(wrapped)

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.params[
            "tool_consumer_instance_guid"
        ] = "test_tool_consumer_instance_guid"
        pyramid_request.params["context_id"] = "test_context_id"
        return pyramid_request

    @pytest.fixture
    def models(self, models):
        models.CourseGroup.get.return_value = mock.create_autospec(
            CourseGroup, instance=True, pubid="test_pubid"
        )
        return models


class TestPost:
    @pytest.mark.parametrize(
        "setting", ["h_client_id", "h_client_secret", "h_authority", "h_api_url"]
    )
    def test_it_crashes_if_a_required_setting_is_missing(
        self, pyramid_request, setting
    ):
        del pyramid_request.registry.settings[setting]

        with pytest.raises(KeyError, match=setting):
            h_api.post(pyramid_request.registry.settings, "/path")

    def test_it_posts_to_the_h_api(self, pyramid_request, requests):
        h_api.post(pyramid_request.registry.settings, "/path")

        requests.post.assert_called_once_with(
            url="https://example.com/api/path",
            auth=("TEST_CLIENT_ID", "TEST_CLIENT_SECRET"),
            timeout=10,
        )

    def test_it_posts_data_as_json(self, pyramid_request, requests):
        h_api.post(pyramid_request.registry.settings, "/path", data={"foo": "bar"})

        assert requests.post.call_args[1]["data"] == '{"foo": "bar"}'

    def test_it_posts_username_as_x_forwarded_user(self, pyramid_request, requests):
        h_api.post(pyramid_request.registry.settings, "/path", username="seanh")

        assert requests.post.call_args[1]["headers"]["X-Forwarded-User"] == (
            "acct:seanh@TEST_AUTHORITY"
        )

    @pytest.mark.parametrize(
        "exception", [ConnectionError(), HTTPError(), ReadTimeout(), TooManyRedirects()]
    )
    def test_it_raises_HAPIError_if_the_request_fails(
        self, exception, pyramid_request, requests
    ):
        requests.post.side_effect = exception

        with pytest.raises(HAPIError):
            h_api.post(pyramid_request.registry.settings, "/path")

    def test_it_raises_HAPIError_if_it_receives_an_error_response(
        self, pyramid_request, requests
    ):
        requests.post.return_value.raise_for_status.side_effect = HTTPError(
            response=requests.post.return_value
        )

        with pytest.raises(HAPIError) as exc_info:
            h_api.post(pyramid_request.registry.settings, "/path")

        assert (
            exc_info.value.response == requests.post.return_value
        ), "It passes the h API response to HAPIError so that it gets logged"

    def test_you_can_tell_it_not_to_raise_for_certain_error_statuses(
        self, pyramid_request, requests
    ):
        response = Response()
        response.status_code = requests.post.return_value.status_code = 409
        requests.post.return_value.raise_for_status.side_effect = HTTPError(
            response=response
        )

        h_api.post(pyramid_request.registry.settings, "/path", statuses=[409])

    @pytest.fixture(autouse=True)
    def requests(self, patch):
        return patch("lms.views.decorators.h_api.requests")


@pytest.fixture(autouse=True)
def models(patch):
    models = patch("lms.views.decorators.h_api.models")

    def side_effect(**kwargs):
        return mock.create_autospec(CourseGroup, instance=True, **kwargs)

    models.CourseGroup.side_effect = side_effect

    models.CourseGroup.get.return_value = None

    return models


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.params.update(
        {
            # A valid oauth_consumer_key (matches one for which the
            # provisioning features are enabled).
            "oauth_consumer_key": "Hypothesise3f14c1f7e8c89f73cefacdd1d80d0ef",
            "tool_consumer_instance_guid": "TEST_GUID",
            "context_id": "TEST_CONTEXT",
            "roles": "Instructor,urn:lti:instrole:ims/lis/Administrator",
        }
    )
    pyramid_request.db = mock.MagicMock()
    return pyramid_request


@pytest.fixture(autouse=True)
def util(patch):
    util = patch("lms.views.decorators.h_api.util")
    util.generate_display_name.return_value = "test_display_name"
    util.generate_group_name.return_value = "test_group_name"
    util.generate_username.return_value = "test_username"
    util.generate_provider.return_value = "test_provider"
    util.generate_provider_unique_id.return_value = "test_provider_unique_id"
    return util


@pytest.fixture
def wrapped():
    """Return the wrapped view function."""
    return mock.MagicMock()


@pytest.fixture
def post(patch):
    post = patch("lms.views.decorators.h_api.post")
    post.return_value = mock.create_autospec(
        Response, instance=True, status_code=200, reason="OK", text=""
    )
    post.return_value.json.return_value = {"id": "TEST_PUBID"}
    return post
