from lms.services.jstor.service import JSTORService


def service_factory(_context, request):
    ai_settings = (
        request.find_service(name="application_instance").get_current().settings
    )

    app_settings = request.registry.settings

    return JSTORService(
        api_url=app_settings.get("jstor_api_url"),
        secret=app_settings.get("jstor_api_secret"),
        enabled=ai_settings.get("jstor", "enabled"),
        site_code=ai_settings.get("jstor", "site_code"),
        http_service=request.find_service(name="http"),
    )
