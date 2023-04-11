import pytest
from pyramid.httpexceptions import HTTPBadRequest, HTTPFound

from lms.views.admin.email import AdminEmailViews


class TestAdminEmailViews:
    def test_get(self, views):
        assert views.get() == {}

    @pytest.mark.usefixtures("with_valid_post_params")
    def test_post(self, views, send_instructor_email_digests):
        response = views.post()

        send_instructor_email_digests.apply_async.assert_called_once_with(
            (),
            {
                "h_userids": ["userid_1", "userid_2"],
                "updated_after": "2023-02-27T00:00:00",
                "updated_before": "2023-02-28T00:00:00",
                "override_to_email": "someone@hypothes.is",
            },
        )
        assert isinstance(response, HTTPFound)
        assert response.location == "http://example.com/admin/email"

    @pytest.mark.usefixtures("with_valid_post_params")
    @pytest.mark.parametrize(
        "form,expected_error_message",
        [
            (
                {"to_email": ""},
                r"^You must enter an email address to send the test email\(s\) to\.$",
            ),
            (
                {"to_email": " "},
                r"^You must enter an email address to send the test email\(s\) to\.$",
            ),
            (
                {"to_email": "someone@example.com"},
                r"^Test emails can only be sent to @hypothes\.is addresses\.$",
            ),
            (
                {"h_userids": "userid_1 userid_2 userid_3 userid_4"},
                r"^Test emails can only be sent for up to 3 users at once\.$",
            ),
            ({"since": "invalid"}, r"^Times must be in ISO 8601 format"),
            ({"until": "invalid"}, r"^Times must be in ISO 8601 format"),
            (
                {"since": "2023-02-28T00:00:00", "until": "2023-02-27T00:00:00"},
                r"^The 'since' time must be earlier than the 'until' time\.$",
            ),
            (
                {"since": "2023-02-28T00:00:00", "until": "2023-04-28T00:00:00"},
                r"^The 'since' and 'until' times must be less than 30 days apart\.$",
            ),
        ],
    )
    def test_post_crashes_if_you_submit_invalid_values(
        self,
        views,
        pyramid_request,
        send_instructor_email_digests,
        form,
        expected_error_message,
    ):
        for key in form:
            pyramid_request.POST[key] = form[key]

        with pytest.raises(HTTPBadRequest, match=expected_error_message):
            views.post()

        send_instructor_email_digests.apply_async.assert_not_called()

    @pytest.fixture
    def with_valid_post_params(self, pyramid_request):
        pyramid_request.POST["to_email"] = "someone@hypothes.is"
        pyramid_request.POST["h_userids"] = "userid_1 userid_2"
        pyramid_request.POST["since"] = "2023-02-27T00:00:00"
        pyramid_request.POST["until"] = "2023-02-28T00:00:00"

    @pytest.fixture
    def views(self, pyramid_request):
        return AdminEmailViews(pyramid_request)


@pytest.fixture(autouse=True)
def send_instructor_email_digests(patch):
    return patch("lms.views.admin.email.send_instructor_email_digests")
