from pyramid.authentication import AuthTicket


class TestReports:
    def test_it_allows_whitelisted_user(self, app):
        cookie_token = AuthTicket(
            "TEST_LMS_SECRET", "report_viewer", "0.0.0.0", hashalg="sha512"
        ).cookie_value()

        app.set_cookie("auth_tkt", cookie_token)

        response = app.get(
            "/reports",
            status=200,
        )

        assert "Application Instances" in response.text

    def test_it_doesnt_allow_any_user(self, app):
        cookie_token = AuthTicket(
            "TEST_LMS_SECRET", "some-user", "0.0.0.0", hashalg="sha512"
        ).cookie_value()

        app.set_cookie("auth_tkt", cookie_token)

        response = app.get(
            "/reports",
            status=200,
        )
        for field in ["came_from", "username", "password"]:
            assert field in response.forms[0].fields
