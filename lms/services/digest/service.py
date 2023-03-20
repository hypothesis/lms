from lms.services.digest._digest_context import DigestContext
from lms.services.mailchimp import EmailRecipient


class DigestService:
    """A service for generating "digests" (activity reports)."""

    def __init__(self, db, h_api, mailchimp_service, sender):
        self._db = db
        self._h_api = h_api
        self._mailchimp_service = mailchimp_service
        self._sender = sender

    def send_instructor_email_digests(
        self, audience, updated_after, updated_before, override_to_email=None
    ):
        """Send instructor email digests for the given users and timeframe."""
        annotations = self._h_api.get_annotations(
            audience, updated_after, updated_before
        )

        # HAPI.get_annotations() returns an iterable.
        # Turn it into a tuple because we need to iterate over it multiple times.
        annotations = tuple(annotations)

        context = DigestContext(self._db, audience, annotations)

        for h_userid in audience:
            digest = context.instructor_digest(h_userid)
            unified_user = context.unified_users[h_userid]

            if digest["total_annotations"] and (
                to_email := override_to_email or unified_user.email
            ):
                # We have something worth sending, and someone to send it to
                self._mailchimp_service.send_template(
                    "instructor-email-digest",
                    self._sender,
                    recipient=EmailRecipient(to_email, unified_user.display_name),
                    template_vars=digest,
                )
