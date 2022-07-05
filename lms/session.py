"""The app's Pyramid session."""
from pyramid.session import JSONSerializer, SignedCookieSessionFactory

__all__ = []


def includeme(config):
    """Set up the app's Pyramid session."""
    # ``secure=True`` is recommended by the Pyramid docs (see
    # https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/sessions.html)
    # but is inconvenient in development environments, so use insecure cookies
    # in dev for convenience but use secure (HTTPS-only) cookies otherwise.
    secure = not config.registry.settings.get("debug", False)

    config.set_session_factory(
        SignedCookieSessionFactory(
            secret=config.registry.settings["session_cookie_secret"],
            secure=secure,
            # ``httponly=True`` is recommended by the Pyramid docs to protect
            # the cookie from cross-site scripting vulnerabilities, see:
            # https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/sessions.html
            httponly=True,
            # 30 days
            max_age=60 * 60 * 24 * 30,
            # The Pyramid docs recommend JSONSerializer instead of the default
            # serializer for security reasons. See:
            # https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/sessions.html
            serializer=JSONSerializer(),
        )
    )
