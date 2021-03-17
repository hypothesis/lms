from lms.views.api.grant_token import grant_token


class TestGrantToken:
    def test_it_generates_token(self, pyramid_request, grant_token_service):
        ctx = grant_token(pyramid_request)
        grant_token_service.generate_token.assert_called_with(
            pyramid_request.lti_user.h_user
        )
        assert ctx["grant_token"] == grant_token_service.generate_token.return_value
