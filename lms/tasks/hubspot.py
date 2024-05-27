from lms.services import HubSpotService
from lms.tasks.celery import app


@app.task
def refresh_hubspot_data():
    """
    Refresh the HubSpot companies, scheduled daily in h-periodic.
    """
    with app.request_context() as request:  # pylint: disable=no-member
        with request.tm:
            hs = request.find_service(HubSpotService)

            hs.refresh_companies()
