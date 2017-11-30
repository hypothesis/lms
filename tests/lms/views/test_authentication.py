from lms.views.authentication import AuthenticationViews


class TestAuthentication(object):
    def test_login(self, pyramid_request):
        pyramid_request.method = 'POST'
        pyramid_request.params = {
            'username': 'report_viewers',
            'password': 'asdf',
            'form.submitted': True,
        }
        sut = AuthenticationViews(pyramid_request)

        response = sut.login

        self.assertEqual(response.status_code, 200)
        assert False
