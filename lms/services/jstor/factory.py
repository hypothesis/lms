from lms.services.jstor.service import JSTORService


def service_factory(_context, request):
    ai_settings = (
        request.find_service(name="application_instance").get_current().settings
    )

    app_settings = request.registry.settings

    # The h username is passed to JSTOR as a tracking ID because it is a
    # conveniently available unique user ID in a standardized format and doesn't
    # contain private info (email addresses etc.).
    if request.lti_user:
        tracking_user_id = request.lti_user.h_user.username
    else:
        tracking_user_id = None

    return JSTORService(
        api_url=app_settings.get("jstor_api_url"),
        secret=app_settings.get("jstor_api_secret"),
        enabled=ai_settings.get("jstor", "enabled"),
        site_code=ai_settings.get("jstor", "site_code"),
        http_service=request.find_service(name="http"),
        tracking_user_agent=request.headers.get("User-Agent", None),
        tracking_user_id=tracking_user_id,
    )
