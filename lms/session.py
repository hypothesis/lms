"""The app's Pyramid session."""

from pyramid.session import JSONSerializer, SignedCookieSessionFactory


def includeme(config):
    """Set up the app's Pyramid session."""
    # ``secure=True`` is recommended by the Pyramid docs (see
    # https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/sessions.html)
    # but is inconvenient in development environments, so use insecure cookies
    # in dev for convenience but use secure (HTTPS-only) cookies otherwise.
    secure = not config.registry.settings["dev"]

    config.set_session_factory(
        SignedCookieSessionFactory(
            # https://docs.pylonsproject.org/projects/pyramid/en/latest/api/session.html#pyramid.session.SignedCookieSessionFactory
            secret=config.registry.settings["session_cookie_secret"],
            secure=secure,
            # ``httponly=True`` is recommended by the Pyramid docs to protect
            # the cookie from cross-site scripting vulnerabilities.
            httponly=True,
            # 30 days
            max_age=60 * 60 * 24 * 30,
            # Disable autoexpiring sessions. Rely only on max_age
            timeout=None,
            # The Pyramid docs recommend JSONSerializer instead of the default
            # serializer for security reasons.
            serializer=JSONSerializer(),
        )
    )
