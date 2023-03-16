class DigestService:
    """A service for generating "digests" (activity reports)."""

    def send_instructor_email_digests(
        self, audience, updated_after, updated_before, override_to_email=None
    ):
        """Send instructor email digests for the given users and timeframe."""


def service_factory(_context, _request):
    return DigestService()
