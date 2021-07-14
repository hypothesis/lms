from urllib.parse import urlencode

from lms.services.blackboard_api._schemas import (
    BlackboardListFilesSchema,
    BlackboardPublicURLSchema,
)
from lms.services.exceptions import BlackboardFileNotFoundInCourse, HTTPError

# The maxiumum number of paginated requests we'll make before returning.
PAGINATION_MAX_REQUESTS = 25

# The maximum number of results to request per paginated response.
# 200 is the highest number that Blackboard will accept here.
PAGINATION_LIMIT = 200


class BlackboardAPIClient:
    """A high-level Blackboard API client."""

    def __init__(self, basic_client):
        self._api = basic_client

    def get_token(self, authorization_code):
        """
        Save a new Blackboard access token for the current user to the DB.

        :raise services.HTTPError: if something goes wrong with the access
            token request to Blackboard
        """
        self._api.get_token(authorization_code)

    def list_files(self, course_id):
        """Return the list of files in the given course."""

        files = []
        path = f"courses/uuid:{course_id}/resources?" + urlencode(
            {
                "type": "file",
                "limit": PAGINATION_LIMIT,
                "fields": "id,name,modified,mimeType",
            }
        )

        for _ in range(PAGINATION_MAX_REQUESTS):
            response = self._api.request("GET", path)
            files.extend(BlackboardListFilesSchema(response).parse())
            path = response.json().get("paging", {}).get("nextPage")
            if not path:
                break

        return files

    def public_url(self, course_id, file_id):
        """Return a public URL for the given file."""

        try:
            response = self._api.request(
                "GET",
                f"courses/uuid:{course_id}/resources/{file_id}?fields=downloadUrl",
            )
        except HTTPError as err:
            if err.response.status_code == 404:
                raise BlackboardFileNotFoundInCourse(file_id) from err
            raise

        return BlackboardPublicURLSchema(response).parse()
