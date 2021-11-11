from urllib.parse import urlencode

from lms.events import FilesDiscoveredEvent
from lms.services.blackboard_api._schemas import (
    BlackboardListFilesSchema,
    BlackboardListGroupSetsSchema,
    BlackboardListGroupsSchema,
    BlackboardPublicURLSchema,
)
from lms.services.exceptions import BlackboardFileNotFoundInCourse, ExternalRequestError

# The maxiumum number of paginated requests we'll make before returning.
PAGINATION_MAX_REQUESTS = 25

# The maximum number of results to request per paginated response.
# 200 is the highest number that Blackboard will accept here.
PAGINATION_LIMIT = 200


class BlackboardAPIClient:
    """A high-level Blackboard API client."""

    def __init__(self, basic_client, request):
        self._api = basic_client
        self._request = request

    def get_token(self, authorization_code):
        """
        Save a new Blackboard access token for the current user to the DB.

        :raise services.ExternalRequestError: if something goes wrong with the
            access token request to Blackboard
        """
        self._api.get_token(authorization_code)

    def list_files(self, course_id, folder_id=None):
        """Return the list of files in the given course or folder."""

        path = f"courses/uuid:{course_id}/resources"

        if folder_id:
            # Get the files and folders in the given folder instead of the
            # course's top-level files and folders.
            path += f"/{folder_id}/children"

        path = (
            path
            + "?"
            + urlencode(
                {
                    "limit": PAGINATION_LIMIT,
                    "fields": "id,name,type,modified,mimeType,size,parentId",
                }
            )
        )

        results = []

        for _ in range(PAGINATION_MAX_REQUESTS):
            response = self._api.request("GET", path)
            results.extend(BlackboardListFilesSchema(response).parse())
            path = response.json().get("paging", {}).get("nextPage")
            if not path:
                break

        # Notify that we've found some files
        self._request.registry.notify(
            FilesDiscoveredEvent(
                request=self._request,
                values=[
                    {
                        "type": "blackboard_file"
                        if file["type"] == "File"
                        else "blackboard_folder",
                        "course_id": course_id,
                        "lms_id": file["id"],
                        "name": file["name"],
                        "size": file["size"],
                        "parent_lms_id": file["parentId"],
                    }
                    for file in results
                ],
            )
        )

        return results

    def public_url(self, course_id, file_id):
        """Return a public URL for the given file."""

        try:
            response = self._api.request(
                "GET",
                f"courses/uuid:{course_id}/resources/{file_id}?fields=downloadUrl",
            )
        except ExternalRequestError as err:
            if err.status_code == 404:
                raise BlackboardFileNotFoundInCourse(file_id) from err
            raise

        return BlackboardPublicURLSchema(response).parse()

    def course_group_categories(self, course_id):
        response = self._api.request(
            "GET",
            f"/learn/api/public/v2/courses/uuid:{course_id}/groups/sets",
        )

        return BlackboardListGroupSetsSchema(response).parse()

    def group_category_groups(self, course_id, group_set_id):
        response = self._api.request(
            "GET",
            f"/learn/api/public/v2/courses/uuid:{course_id}/groups/sets/{group_set_id}/groups",
        )
        return BlackboardListGroupsSchema(response).parse()

    def course_groups(self, course_id, group_category_id=None, user_id=None):
        response = self._api.request(
            "GET",
            f"/learn/api/public/v2/courses/uuid:{course_id}/groups",
        )
        groups = BlackboardListGroupsSchema(response).parse()

        if group_category_id:
            groups = [
                group
                for group in self.course_groups(course_id)
                if group["groupSetId"] == group_category_id
            ]

        if user_id:
            confirmed_groups = []
            for group in groups:
                try:
                    response = self._api.request(
                        "GET",
                        f"/learn/api/public/v2/courses/uuid:{course_id}/groups/{group['id']}",
                    )

                except Exception as err:
                    pass
                else:
                    confirmed_groups.append(group)

            groups = confirmed_groups

        return groups
