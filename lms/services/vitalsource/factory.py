from lms.services.vitalsource.client import VitalSourceClient
from lms.services.vitalsource.service import VitalSourceService


def service_factory(_context, request):
    return VitalSourceService(
        VitalSourceClient(api_key=request.registry.settings["vitalsource_api_key"])
    )
