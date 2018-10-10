import pytest
from pyramid.httpexceptions import HTTPBadRequest

from lms.util import lti_params_for


class TestLTIParamsFor:
    def test_with_lti_launch_request(self, pyramid_request):
        # If the request is an LTI launch request then it just returns
        # request.params.
        assert lti_params_for(pyramid_request) == pyramid_request.params

    def test_with_oauth_redirect_request(self, models, pyramid_request):
        # If the request is an OAuth 2.0 redirect URL request then it retrieves
        # the LTI launch params that were previously stashed in the database
        # and returns those instead of request.params.
        pyramid_request.params = {"state": "foo"}

        assert lti_params_for(pyramid_request) == models.find_lti_params.return_value
        models.find_lti_params.assert_called_once_with(pyramid_request.db, "foo")

    def test_with_invalid_oauth_redirect_request(self, models, pyramid_request):
        # If the request is an OAuth 2.0 redirect URL request but somehow we
        # haven't stashed any LTI params in the DB that match this request's
        pyramid_request.params = {"state": "foo"}
        models.find_lti_params.return_value = None

        with pytest.raises(HTTPBadRequest):
            lti_params_for(pyramid_request)

    @pytest.fixture(autouse=True)
    def models(self, patch):
        return patch("lms.util.lti.models")
