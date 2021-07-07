from lms.views.api.blackboard._schemas import BlackboardListFilesSchema


class BlackboardService:
    """A high-level Blackboard API service."""

    api = None

    # The maxiumum number of paginated requests we'll make before returning.
    PAGINATION_MAX_REQUESTS = 25

    # The maximum number of results to request per paginated response.
    # 200 is the highest number that Blackboard will accept here.
    PAGINATION_LIMIT = 200

    def __init__(self, blackboard_api_client):
        self.api = blackboard_api_client

    def get_files(self, course_id, folder_id=None):
        """Return the list of files and folders in a course or folder."""

        path = f"courses/uuid:{course_id}/resources"

        if folder_id:
            # Get the files and folders in the given folder instead of the
            # course's top-level files and folders.
            path += f"/{folder_id}/children"

        path += f"?limit={self.PAGINATION_LIMIT}"

        results = []

        for _ in range(self.PAGINATION_MAX_REQUESTS):
            response = self.api.request("GET", path)
            results.extend(BlackboardListFilesSchema(response).parse())
            path = response.json().get("paging", {}).get("nextPage")
            if not path:
                break

        return results


def factory(_context, request):
    return BlackboardService(request.find_service(name="blackboard_api_client"))
