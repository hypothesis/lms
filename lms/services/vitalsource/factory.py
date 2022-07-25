from lms.services.vitalsource._client import VitalSourceClient
from lms.services.vitalsource.service import VitalSourceService


def service_factory(_context, request):
    settings = request.find_service(name="application_instance").get_current().settings

    return VitalSourceService(
        client=VitalSourceClient(
            api_key=request.registry.settings["vitalsource_api_key"]
        ),
        enabled=settings.get("vitalsource", "enabled", False),
    )
