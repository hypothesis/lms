# -*- coding: utf-8 -*-

import json
import mock
import pytest

from pyramid.httpexceptions import HTTPBadGateway
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.httpexceptions import HTTPGatewayTimeout
import requests.exceptions

from lms.views.decorators.h_api import create_h_user
from lms.views.decorators.h_api import create_course_group
from lms.util import MissingToolConsumerIntanceGUIDError
from lms.util import MissingUserIDError
from lms.models import CourseGroup


@pytest.mark.usefixtures("post", "util")
class TestCreateHUser:
    def test_it_400s_if_no_oauth_consumer_key_param(self, create_h_user, pyramid_request):
        del pyramid_request.params["oauth_consumer_key"]

        with pytest.raises(HTTPBadRequest, match="oauth_consumer_key"):
            create_h_user(pyramid_request, mock.sentinel.jwt)

    def test_it_continues_to_the_wrapped_func_if_feature_not_enabled(self, create_h_user, pyramid_request, wrapped):
        pyramid_request.params = {"oauth_consumer_key": "foo"}

        returned = create_h_user(pyramid_request, mock.sentinel.jwt)

        wrapped.assert_called_once_with(pyramid_request, mock.sentinel.jwt)
        assert returned == wrapped.return_value

    def test_it_doesnt_use_the_h_api_if_feature_not_enabled(self, create_h_user, post, pyramid_request):
        pyramid_request.params = {"oauth_consumer_key": "foo"}

        create_h_user(pyramid_request, mock.sentinel.jwt)

        assert not post.called

    def test_it_400s_if_generate_username_raises_MissingToolConsumerInstanceGUIDError(self, create_h_user, pyramid_request, util):
        util.generate_username.side_effect = MissingToolConsumerIntanceGUIDError()

        with pytest.raises(HTTPBadRequest, match="tool_consumer_instance_guid"):
            create_h_user(pyramid_request, mock.sentinel.jwt)

    def test_it_400s_if_generate_username_raises_MissingUserIDError(self, create_h_user, pyramid_request, util):
        util.generate_username.side_effect = MissingUserIDError()

        with pytest.raises(HTTPBadRequest, match="user_id"):
            create_h_user(pyramid_request, mock.sentinel.jwt)

    def test_it_400s_if_generate_provider_raises_MissingToolConsumerInstanceGUIDError(self, create_h_user, pyramid_request, util):
        util.generate_provider.side_effect = MissingToolConsumerIntanceGUIDError()

        with pytest.raises(HTTPBadRequest, match="tool_consumer_instance_guid"):
            create_h_user(pyramid_request, mock.sentinel.jwt)

    def test_it_400s_if_generate_provider_unique_id_raises_MissingUserIDError(self, create_h_user, pyramid_request, util):
        util.generate_provider_unique_id.side_effect = MissingUserIDError()

        with pytest.raises(HTTPBadRequest, match="user_id"):
            create_h_user(pyramid_request, mock.sentinel.jwt)

    def test_it_creates_the_user_in_h(self, create_h_user, post, pyramid_request):
        create_h_user(pyramid_request, mock.sentinel.jwt)

        post.assert_called_once_with(
            "https://example.com/api/users",
            auth=("TEST_CLIENT_ID", "TEST_CLIENT_SECRET"),
            data=json.dumps({
                "username": "test_username",
                "display_name": "test_display_name",
                "authority": "TEST_AUTHORITY",
                "identities": [{
                    "provider": "test_provider",
                    "provider_unique_id": "test_provider_unique_id",
                }],
            }),
            timeout=1,
        )

    def test_it_504s_if_the_h_request_times_out(self, create_h_user, patch, post, pyramid_request):
        post.side_effect = requests.exceptions.ReadTimeout()

        with pytest.raises(HTTPGatewayTimeout):
            create_h_user(pyramid_request, mock.sentinel.jwt)

    def test_it_continues_to_the_wrapped_function_if_h_200s(self, create_h_user, pyramid_request, wrapped):
        returned = create_h_user(pyramid_request, mock.sentinel.jwt)

        wrapped.assert_called_once_with(pyramid_request, mock.sentinel.jwt)
        assert returned == wrapped.return_value

    def test_it_continues_to_the_wrapped_function_if_h_409s(self, create_h_user, post, pyramid_request, wrapped):
        post.return_value.status_code = 409

        returned = create_h_user(pyramid_request, mock.sentinel.jwt)

        wrapped.assert_called_once_with(pyramid_request, mock.sentinel.jwt)
        assert returned == wrapped.return_value

    @pytest.mark.parametrize("status", (500, 501, 502, 503, 504, 400, 401, 403, 404, 408))
    def test_it_502s_for_unexpected_errors_from_h(self, create_h_user, post, pyramid_request, status):
        post.return_value.status_code = status

        with pytest.raises(HTTPBadGateway, match="Connecting to Hypothesis failed"):
            create_h_user(pyramid_request, mock.sentinel.jwt)

    @pytest.fixture
    def create_h_user(self, wrapped):
        # Return the actual wrapper function so that tests can call it directly.
        return create_h_user(wrapped)

    @pytest.fixture
    def post(self, patch):
        post = patch("lms.views.decorators.h_api.requests.post")
        post.return_value = mock.create_autospec(
            requests.models.Response,
            instance=True,
            status_code=200,
        )
        return post

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.params = {
            # A valid oauth_consumer_key (matches one for which the
            # provisioning features are enabled).
            "oauth_consumer_key": "Hypothesise3f14c1f7e8c89f73cefacdd1d80d0ef",
        }
        return pyramid_request

    @pytest.fixture
    def util(self, patch):
        util = patch("lms.views.decorators.h_api.util")
        util.generate_username.return_value = "test_username"
        util.generate_display_name.return_value = "test_display_name"
        util.generate_provider.return_value = "test_provider"
        util.generate_provider_unique_id.return_value = "test_provider_unique_id"
        return util

    @pytest.fixture
    def wrapped(self):
        """Return the wrapped view function."""
        return mock.MagicMock()


@pytest.mark.usefixtures("models", "util", "post")
class TestCreateCourseGroup:
    @pytest.mark.parametrize("required_param_name", (
        "oauth_consumer_key",
        "tool_consumer_instance_guid",
        "context_id",
        "roles",
    ))
    def test_it_400s_if_theres_a_required_param_missing(self, create_course_group, pyramid_request, required_param_name):
        del pyramid_request.params[required_param_name]

        with pytest.raises(HTTPBadRequest, match=required_param_name):
            create_course_group(pyramid_request, mock.sentinel.jwt)

    def test_it_400s_if_the_user_isnt_allowed_to_create_groups(self, create_course_group, pyramid_request):
        pyramid_request.params["roles"] = "Learner"

        with pytest.raises(HTTPBadRequest, match="Instructor must launch assignment first"):
            create_course_group(pyramid_request, mock.sentinel.jwt)

    def test_it_does_nothing_if_the_user_isnt_allowed_to_create_groups_but_the_group_already_exists(
        self, create_course_group, pyramid_request, models, post, wrapped
    ):
        models.CourseGroup.get.return_value = mock.create_autospec(CourseGroup, instance=True)
        pyramid_request.params["roles"] = "Learner"

        returned = create_course_group(pyramid_request, mock.sentinel.jwt)

        assert not post.called
        assert not pyramid_request.db.add.called
        wrapped.assert_called_once_with(pyramid_request, mock.sentinel.jwt)
        assert returned == wrapped.return_value

    def test_it_does_nothing_if_the_feature_isnt_enabled(self, create_course_group, pyramid_request, wrapped, post):
        # If the auto provisioning feature isn't enabled for this application
        # instance then create_course_group() doesn't do anything - just calls the
        # wrapped view.
        pyramid_request.params = {"oauth_consumer_key": "foo"}

        returned = create_course_group(pyramid_request, mock.sentinel.jwt)

        assert not post.called
        assert not pyramid_request.db.add.called
        wrapped.assert_called_once_with(pyramid_request, mock.sentinel.jwt)
        assert returned == wrapped.return_value

    def test_it_does_nothing_if_the_course_group_already_exists(self, create_course_group, models, pyramid_request, wrapped, post):
        models.CourseGroup.get.return_value = mock.create_autospec(CourseGroup, instance=True)

        returned = create_course_group(pyramid_request, mock.sentinel.jwt)

        assert not post.called
        assert not pyramid_request.db.add.called
        wrapped.assert_called_once_with(pyramid_request, mock.sentinel.jwt)
        assert returned == wrapped.return_value

    def test_it_posts_to_the_group_create_api(self, create_course_group, pyramid_request, post):
        create_course_group(pyramid_request, mock.sentinel.jwt)

        post.assert_called_once_with(
            "https://example.com/api/groups",
            auth=("TEST_CLIENT_ID", "TEST_CLIENT_SECRET"),
            data='{"name": "TEST_GROUP"}',
            headers={
                "X-Forwarded-User": "acct:TEST_USERNAME@TEST_AUTHORITY",
            },
            timeout=1,
        )

    @pytest.mark.parametrize("request_exception", (
        requests.ConnectionError(),
        requests.TooManyRedirects(),
        requests.ReadTimeout(),
    ))
    def test_it_504s_if_the_h_request_errors(self, create_course_group, post, pyramid_request, request_exception):
        post.side_effect = request_exception

        with pytest.raises(HTTPGatewayTimeout):
            create_course_group(pyramid_request, mock.sentinel.jwt)

    def test_it_504s_if_the_h_response_is_unsuccessful(self, create_course_group, post, pyramid_request):
        post.return_value.raise_for_status.side_effect = requests.HTTPError()

        with pytest.raises(HTTPGatewayTimeout):
            create_course_group(pyramid_request, mock.sentinel.jwt)

    def test_it_saves_the_group_to_the_db(self, create_course_group, pyramid_request, models):
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
                return all((
                    other.pubid == self.pubid,
                    other.tool_consumer_instance_guid == self.tool_consumer_instance_guid,
                    other.context_id == self.context_id,
                ))

        pyramid_request.db.add.assert_called_once_with(CourseGroupMatcher(
            pubid="TEST_PUBID",
            tool_consumer_instance_guid="TEST_GUID",
            context_id="TEST_CONTEXT",
        ))

    def test_it_calls_and_returns_the_wrapped_view(self, create_course_group, pyramid_request, wrapped):
        returned = create_course_group(pyramid_request, mock.sentinel.jwt)

        wrapped.assert_called_once_with(pyramid_request, mock.sentinel.jwt)
        assert returned == wrapped.return_value

    @pytest.fixture
    def create_course_group(self, wrapped):
        # Return the actual wrapper function so that tests can call it directly.
        return create_course_group(wrapped)

    @pytest.fixture
    def wrapped(self):
        """Return the wrapped view function."""
        return mock.MagicMock()

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.params = {
            # A valid oauth_consumer_key (matches one for which the
            # provisioning features are enabled).
            "oauth_consumer_key": "Hypothesise3f14c1f7e8c89f73cefacdd1d80d0ef",
            "tool_consumer_instance_guid": "TEST_GUID",
            "context_id": "TEST_CONTEXT",
            "roles": "Instructor,urn:lti:instrole:ims/lis/Administrator",
        }
        pyramid_request.db = mock.MagicMock()
        return pyramid_request

    @pytest.fixture
    def models(self, patch):
        models = patch("lms.views.decorators.h_api.models")

        def side_effect(**kwargs):
            return mock.create_autospec(CourseGroup, instance=True, **kwargs)
        models.CourseGroup.side_effect = side_effect

        models.CourseGroup.get.return_value = None

        return models

    @pytest.fixture
    def util(self, patch):
        util = patch("lms.views.decorators.h_api.util")
        util.generate_group_name.return_value = "TEST_GROUP"
        util.generate_username.return_value = "TEST_USERNAME"
        return util

    @pytest.fixture
    def post(self, patch):
        post = patch("lms.views.decorators.h_api.requests.post")
        post.return_value = mock.create_autospec(
            requests.models.Response,
            instance=True,
            status_code=200,
        )
        post.return_value.json.return_value = {"id": "TEST_PUBID"}
        return post
