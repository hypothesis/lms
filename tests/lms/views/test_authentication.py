from lms.views import authentication


class TestAuthentication(object):
    def test_login(self, pyramid_request):
        pyramid_request.params = {
            'username': 'report_viewers',
            'password': 'asdf',
            'form.submitted': True,
        }
        sut = authentication.AuthenticationViews(pyramid_request)

        response = sut.login()

        assert response.status_code == 302
        assert response.location == 'http://example.com'

    def test_failed_login(self, pyramid_request):
        pyramid_request.params = {
            'username': 'report_viewers',
            'password': 'wrongpassword',
            'form.submitted': True,
        }
        sut = authentication.AuthenticationViews(pyramid_request)

        response = sut.login()

        assert response['message'] == 'Failed login'
        assert response['url'] == 'http://example.com/login'
        assert response['username'] == 'report_viewers'

    def test_login_not_submitted(self, pyramid_request):
        sut = authentication.AuthenticationViews(pyramid_request)

        response = sut.login()

        assert response['message'] == ''
        assert response['url'] == 'http://example.com/login'
        assert response['username'] == ''

    def test_logout(self, pyramid_request):
        pyramid_request.params = {
            'username': 'report_viewers',
            'password': 'asdf',
            'form.submitted': True,
        }
        sut = authentication.AuthenticationViews(pyramid_request)

        # First login
        response_login = sut.login()

        assert response_login.status_code == 302
        assert response_login.location == 'http://example.com'

        # Then logout
        response_logout = sut.logout()
        assert response_logout.status_code == 302
        assert response_logout.location == 'http://example.com/login'
