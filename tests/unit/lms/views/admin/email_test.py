from unittest.mock import call

import pytest
from h_matchers import Any
from pyramid.httpexceptions import HTTPBadRequest, HTTPFound
from pyramid.renderers import render

from lms.views.admin.email import (
    INSTRUCTOR_EMAIL_DIGEST_TEMPLATE_VARS,
    MENTION_EMAIL_TEMPLATE_VARS,
    AdminEmailViews,
)


class TestAdminEmailViews:
    def test_get(self, views):
        assert views.get() == {
            "instructor_email_digest_subject": Any.string(),
            "mention_email_subject": Any.string(),
        }

    @pytest.mark.usefixtures("with_valid_post_params")
    def test_post(self, views, send_instructor_email_digest):
        response = views.post()

        assert send_instructor_email_digest.apply_async.call_args_list == [
            call(
                (),
                {
                    "h_userid": h_userid,
                    "created_after": "2023-02-27T00:00:00",
                    "created_before": "2023-02-28T00:00:00",
                    "override_to_email": "someone@hypothes.is",
                    "deduplicate": False,
                },
            )
            for h_userid in ["userid_1", "userid_2"]
        ]
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
        send_instructor_email_digest,
        form,
        expected_error_message,
    ):
        for key in form:
            pyramid_request.POST[key] = form[key]

        with pytest.raises(HTTPBadRequest, match=expected_error_message):
            views.post()

        send_instructor_email_digest.apply_async.assert_not_called()

    def test_preview_instructor_email_digest(self, views):
        template_vars = views.preview_instructor_email_digest()

        assert template_vars == INSTRUCTOR_EMAIL_DIGEST_TEMPLATE_VARS
        # Test that rendering the template using the template vars at least
        # doesn't crash.
        render(
            "lms:templates/email/instructor_email_digest/body.html.jinja2",
            template_vars,
        )

    def test_preview_mention_email(self, views):
        template_vars = views.preview_mention_email()

        assert template_vars == MENTION_EMAIL_TEMPLATE_VARS
        # Test that rendering the template using the template vars at least
        # doesn't crash.
        render(
            "lms:templates/email/mention/body.html.jinja2",
            template_vars,
        )

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
def send_instructor_email_digest(patch):
    return patch("lms.views.admin.email.send_instructor_email_digest")
