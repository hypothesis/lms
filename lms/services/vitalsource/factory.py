from lms.services.vitalsource._client import VitalSourceClient
from lms.services.vitalsource.service import VitalSourceService


def service_factory(_context, request):
    settings = request.lti_user.application_instance.settings

    global_key = request.registry.settings["vitalsource_api_key"]
    customer_key = settings.get("vitalsource", "api_key")

    return VitalSourceService(
        # It's important to pass None here if there's no key, so the service
        # knows it's been disabled. The client will raise an error anyway if
        # you try and create one with no API key.
        enabled=settings.get("vitalsource", "enabled", False),
        global_client=VitalSourceClient(global_key) if global_key else None,
        customer_client=VitalSourceClient(customer_key) if customer_key else None,
        user_lti_param=settings.get("vitalsource", "user_lti_param"),
        user_lti_pattern=settings.get("vitalsource", "user_lti_pattern"),
    )
