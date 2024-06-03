from datetime import datetime

from lms.services import OrganizationService
from lms.tasks.celery import app


@app.task
def generate_usage_report(
    organization_id: int, tag: str, since: str, until: str
) -> None:
    with app.request_context() as request:
        with request.tm:
            request.find_service(OrganizationService).generate_usage_report(
                organization_id,
                tag,
                datetime.fromisoformat(since),
                datetime.fromisoformat(until),
            )
