from datetime import datetime, timedelta

from pyramid.httpexceptions import HTTPBadRequest, HTTPFound
from pyramid.view import view_config, view_defaults

from lms.security import Permissions
from lms.tasks.email_digests import send_instructor_email_digests


@view_defaults(route_name="admin.email", permission=Permissions.ADMIN)
class AdminEmailViews:
    def __init__(self, request):
        self.request = request

    @view_config(
        route_name="admin.email",
        request_method="GET",
        renderer="lms:templates/admin/email.html.jinja2",
    )
    def get(self):
        return {}

    @view_config(route_name="admin.email", request_method="POST")
    def post(self):
        to_email = self.request.POST["to_email"].strip()
        h_userids = self.request.POST["h_userids"].strip().split()
        since = self.request.POST["since"].strip()
        until = self.request.POST["until"].strip()

        if not to_email:
            raise HTTPBadRequest(
                "You must enter an email address to send the test email(s) to."
            )

        if not to_email.endswith("@hypothes.is"):
            raise HTTPBadRequest(
                "Test emails can only be sent to @hypothes.is addresses."
            )

        if len(h_userids) > 3:
            raise HTTPBadRequest(
                "Test emails can only be sent for up to 3 users at once."
            )

        try:
            since = datetime.fromisoformat(since)
            until = datetime.fromisoformat(until)
        except ValueError as exc:
            raise HTTPBadRequest(
                "Times must be in ISO 8601 format, for example: '2023-02-27T00:00:00'."
            ) from exc

        if until <= since:
            raise HTTPBadRequest(
                "The 'since' time must be earlier than the 'until' time."
            )

        if (until - since) > timedelta(days=30):
            raise HTTPBadRequest(
                "The 'since' and 'until' times must be less than 30 days apart."
            )

        send_instructor_email_digests.apply_async(
            [h_userids, since.isoformat(), until.isoformat()],
            {"override_to_email": to_email},
        )

        self.request.session.flash(
            f"If the given users have any activity in the given timeframe then emails will be sent to {to_email}."
        )

        return HTTPFound(location=self.request.route_url("admin.email"))
