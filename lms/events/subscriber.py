from pyramid.events import subscriber

from lms.models.file import File


class FilesDiscoveredEvent:
    """Notify that a file has been found in an LMS."""

    def __init__(self, request, values):
        """
        Initialize the event.

        :param request: Pyramid request object
        :param values: List of dicts of file information
        """
        self.request = request
        self.values = values


@subscriber(FilesDiscoveredEvent)
def files_discovered(event):
    """Record discovered files in the DB."""

    application_instance = event.request.find_service(name="application_instance").get()

    for value in event.values:
        value["application_instance_id"] = application_instance.id

    event.request.db.bulk.upsert(File, values=event.values)
