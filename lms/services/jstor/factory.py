from lms.services.jstor.service import JSTORService


def service_factory(_context, request):
    ai_settings = request.lti_user.application_instance.settings
    app_settings = request.registry.settings

    return JSTORService(
        api_url=app_settings.get("jstor_api_url"),
        secret=app_settings.get("jstor_api_secret"),
        enabled=ai_settings.get("jstor", "enabled"),
        site_code=ai_settings.get("jstor", "site_code"),
        # The h username is passed to JSTOR as a tracking ID because it is a
        # conveniently available unique user ID in a standardized format and
        # doesn't contain private info (email addresses etc.).
        headers={
            "Tracking-User-ID": request.lti_user.h_user.username,
            "Tracking-User-Agent": request.headers.get("User-Agent", None),
        },
    )
