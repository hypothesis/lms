from dataclasses import dataclass
from typing import List

from pyramid.events import subscriber
from pyramid.request import Request

from lms.models.file import File


@dataclass
class FilesDiscoveredEvent:
    """Notify that a file has been found in an LMS."""

    request: Request
    values: List[dict]


@subscriber(FilesDiscoveredEvent)
def files_discovered(event):
    """Record discovered files in the DB."""

    application_instance = event.request.find_service(
        name="application_instance"
    ).get_current()

    for value in event.values:
        value["application_instance_id"] = application_instance.id

    event.request.db.bulk.upsert(File, values=event.values)
