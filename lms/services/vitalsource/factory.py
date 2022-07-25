from lms.services.vitalsource._client import VitalSourceClient
from lms.services.vitalsource.service import VitalSourceService


def service_factory(_context, request):
    settings = request.find_service(name="application_instance").get_current().settings

    customer_key = settings.get("vitalsource", "api_key")

    return VitalSourceService(
        # It's important to pass None here if there's no key, so the service
        # knows it's been disabled. The client will raise an error anyway if
        # you try and create one with no API key.
        client=VitalSourceClient(customer_key) if customer_key else None,
        user_lti_param=settings.get("vitalsource", "user_lti_param"),
        enabled=settings.get("vitalsource", "enabled", False),
    )
