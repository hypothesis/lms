from datetime import datetime, timedelta

from pyramid.httpexceptions import HTTPBadRequest, HTTPFound
from pyramid.renderers import render
from pyramid.view import view_config, view_defaults

from lms.security import Permissions
from lms.tasks.email_digests import send_instructor_email_digest


@view_defaults(route_name="admin.email", permission=Permissions.STAFF)
class AdminEmailViews:
    def __init__(self, request):
        self.request = request

    @view_config(request_method="GET", renderer="lms:templates/admin/email.html.jinja2")
    @view_config(
        route_name="admin.email.section",
        request_method="GET",
        renderer="lms:templates/admin/email.html.jinja2",
    )
    def get(self):
        return {
            "instructor_email_digest_subject": render(
                "lms:templates/email/instructor_email_digest/subject.jinja2",
                INSTRUCTOR_EMAIL_DIGEST_TEMPLATE_VARS,
            ),
            "mention_email_subject": render(
                "lms:templates/email/mention/subject.jinja2",
                MENTION_EMAIL_TEMPLATE_VARS,
            ),
        }

    @view_config(request_method="POST")
    def post(self):
        to_email = self.request.POST["to_email"].strip()
        h_userids = self.request.POST["h_userids"].strip().split()
        since = self.request.POST["since"].strip()
        until = self.request.POST["until"].strip()

        if not to_email:
            raise HTTPBadRequest(  # noqa: TRY003
                "You must enter an email address to send the test email(s) to."  # noqa: EM101
            )

        if not to_email.endswith("@hypothes.is"):
            raise HTTPBadRequest(  # noqa: TRY003
                "Test emails can only be sent to @hypothes.is addresses."  # noqa: EM101
            )

        if len(h_userids) > 3:
            raise HTTPBadRequest(  # noqa: TRY003
                "Test emails can only be sent for up to 3 users at once."  # noqa: EM101
            )

        try:
            since = datetime.fromisoformat(since)
            until = datetime.fromisoformat(until)
        except ValueError as exc:
            raise HTTPBadRequest(  # noqa: TRY003
                "Times must be in ISO 8601 format, for example: '2023-02-27T00:00:00'."  # noqa: EM101
            ) from exc

        if until <= since:
            raise HTTPBadRequest(  # noqa: TRY003
                "The 'since' time must be earlier than the 'until' time."  # noqa: EM101
            )

        if (until - since) > timedelta(days=30):
            raise HTTPBadRequest(  # noqa: TRY003
                "The 'since' and 'until' times must be less than 30 days apart."  # noqa: EM101
            )

        for h_userid in h_userids:
            send_instructor_email_digest.apply_async(
                (),
                {
                    "h_userid": h_userid,
                    "created_before": until.isoformat(),
                    "created_after": since.isoformat(),
                    "override_to_email": to_email,
                    "deduplicate": False,
                },
            )

        self.request.session.flash(
            f"If the given users have any activity in the given timeframe then emails will be sent to {to_email}."
        )

        return HTTPFound(location=self.request.route_url("admin.email"))

    @view_config(
        route_name="admin.email.preview.instructor_email_digest",
        request_method="GET",
        renderer="lms:templates/email/instructor_email_digest/body.html.jinja2",
    )
    def preview_instructor_email_digest(self):
        return INSTRUCTOR_EMAIL_DIGEST_TEMPLATE_VARS

    @view_config(
        route_name="admin.email.preview.mention_email",
        request_method="GET",
        renderer="lms:templates/email/mention/body.html.jinja2",
    )
    def preview_mention_email(self):
        return MENTION_EMAIL_TEMPLATE_VARS


MENTION_EMAIL_TEMPLATE_VARS = {
    "course_title": "COURSE TITLE",
    "assignment_title": "ASSIGNMENT TITLE",
    "annotation_text": 'ANNOTATION TEXT <a data-hyp-mention="" data-userid="acct:1234567@lms.hypothes.is">@John Doe</a>',
    "annotation_quote": "ANNOTATION QUOTE",
}


#: Test template variables that the admin page will pass to the instructor_email_digest templates.
INSTRUCTOR_EMAIL_DIGEST_TEMPLATE_VARS = {
    "total_annotations": 78,
    "annotators": [f"learner{i}" for i in range(12)],
    "courses": [
        {
            "title": "History of Jazz Music",
            "annotators": [f"learner{i}" for i in range(10)],
            "num_annotations": 67,
            "assignments": [
                {
                    "title": "First Assignment",
                    "annotators": [f"learner{i}" for i in range(5)],
                    "num_annotations": 33,
                },
                {
                    "title": "Second Assignment",
                    "annotators": [f"learner{i}" for i in range(5, 10)],
                    "num_annotations": 34,
                },
            ],
        },
        {
            "title": "Making Sociology Fun",
            "annotators": ["learner01", "learner02"],
            "num_annotations": 10,
            "assignments": [
                {
                    "title": "Assignment A",
                    "annotators": ["learner01", "learner02"],
                    "num_annotations": 10,
                },
            ],
        },
        {
            "title": "Amusement Park Engineering",
            "annotators": [f"learner{i}" for i in range(32)],
            "num_annotations": 101,
            "assignments": [],
        },
    ],
}
