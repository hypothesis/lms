from datetime import datetime

from lms.services import OrganizationUsageReportService
from lms.tasks.celery import app


@app.task
def generate_usage_report(
    organization_id: int, tag: str, since: str, until: str
) -> None:
    with app.request_context() as request:
        with request.tm:
            request.find_service(OrganizationUsageReportService).generate_usage_report(
                organization_id,
                tag,
                datetime.fromisoformat(since),
                datetime.fromisoformat(until),
            )
