from urllib.parse import urlencode

from lms.services.blackboard_api._schemas import (
    BlackboardListFilesSchema,
    BlackboardListGroups,
    BlackboardListGroupSetsSchema,
    BlackboardPublicURLSchema,
)
from lms.services.exceptions import (
    ExternalAsyncRequestError,
    ExternalRequestError,
    FileNotFoundInCourse,
)

# The maximum number of paginated requests we'll make before returning.
PAGINATION_MAX_REQUESTS = 25

# The maximum number of results to request per paginated response.
# 200 is the highest number that Blackboard will accept here.
PAGINATION_LIMIT = 200


class BlackboardAPIClient:
    """A high-level Blackboard API client."""

    def __init__(self, basic_client, request, file_service):
        self._api = basic_client
        self._request = request
        self._file_service = file_service

    def get_token(self, authorization_code):
        """
        Save a new Blackboard access token for the current user to the DB.

        :raise services.ExternalRequestError: if something goes wrong with the
            access token request to Blackboard
        """
        self._api.get_token(authorization_code)

    def refresh_access_token(self):
        """
        Refresh the current user's access token in the DB.

        :raise services.ExternalRequestError: if something goes wrong with the
            refresh token request to Blackboard
        """
        self._api.refresh_access_token()

    def list_files(self, course_id, folder_id=None):
        """Return the list of files in the given course or folder."""

        response = self._api.request("GET", self._list_files_url(course_id, folder_id))
        files = self._get_all_following_pages(response, BlackboardListFilesSchema)

        self._store_files(course_id, files)
        return files

    def list_all_files(self, course_id):
        """Return all files and folders in a course."""
        # Get this level all pages
        response = self._api.request("GET", self._list_files_url(course_id))
        files = self._get_all_following_pages(response, BlackboardListFilesSchema)

        # Get all the subfolder files, recursively
        results = self._get_all_folders_files(course_id, files)

        self._store_files(course_id, results)
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
                raise FileNotFoundInCourse(
                    "blackboard_file_not_found_in_course", file_id
                ) from err
            raise

        return BlackboardPublicURLSchema(response).parse()

    def course_group_sets(self, course_id):
        response = self._api.request(
            "GET",
            f"/learn/api/public/v2/courses/uuid:{course_id}/groups/sets",
        )

        return BlackboardListGroupSetsSchema(response).parse()

    def group_set_groups(self, course_id, group_set_id):
        response = self._api.request(
            "GET",
            f"/learn/api/public/v2/courses/uuid:{course_id}/groups/sets/{group_set_id}/groups",
        )
        return BlackboardListGroups(response).parse()

    def course_groups(
        self, course_id, group_set_id=None, current_student_own_groups_only=True
    ):
        """
        Return the groups in a course.

        :param course_id: ID of the course
        :param group_set_id: Only return groups that belong to this group set
        :param current_student_own_groups_only: Only return groups the current user (a student) belong to.

        :raise services.ExternalAsyncRequestError: if something goes wrong with the async group membership requests.
        """
        response = self._api.request(
            "GET",
            f"/learn/api/public/v2/courses/uuid:{course_id}/groups",
        )
        groups = BlackboardListGroups(response).parse()

        if group_set_id:
            groups = [group for group in groups if group["groupSetId"] == group_set_id]

        if not current_student_own_groups_only:
            return groups

        instructor_only_groups = []
        self_enrollment_groups = []
        self_enrollment_check_urls = []

        for group in groups:
            if group["enrollment"]["type"] == "InstructorOnly":
                # We don't need to check "InstructorOnly" groups, we can only see those if we are member
                instructor_only_groups.append(group)
            else:
                # For the rest will have to make a HTTP request per group
                self_enrollment_groups.append(group)
                self_enrollment_check_urls.append(
                    self._api._api_url(  # noqa: SLF001
                        f"/learn/api/public/v2/courses/uuid:{course_id}/groups/{group['id']}"
                    )
                )

        if self_enrollment_groups:
            responses = self._request.find_service(name="async_oauth_http").request(
                "GET", self_enrollment_check_urls
            )
            # We are going to be modifying `self_enrollment_groups` within the loop
            # Create a copy here to iterate over.
            for group, response in zip(list(self_enrollment_groups), responses):
                # If we are a member of any of the SelfEnrollment groups
                # we'll get a 200 response from the endpoint
                if response.status == 200:
                    continue

                # If we are not a member will get a 403 response.
                if response.status == 403:
                    self_enrollment_groups.remove(group)
                    continue

                # Any other result is unexpected
                raise ExternalAsyncRequestError(response=response)

        return self_enrollment_groups + instructor_only_groups

    def _list_files_url(self, course_id, folder_id=None) -> str:
        """Return the url for the list files API endpoint."""
        path = f"courses/uuid:{course_id}/resources"

        if folder_id:
            # Get the files and folders in the given folder instead of the
            # course's top-level files and folders.
            path += f"/{folder_id}/children"

        return (
            path
            + "?"
            + urlencode(
                {
                    "limit": PAGINATION_LIMIT,
                    "fields": "id,name,type,modified,mimeType,size,parentId",
                }
            )
        )

    def _store_files(self, course_id, files: list[dict]):
        """Store the given files in the DB."""
        self._file_service.upsert(
            [
                {
                    "type": (
                        "blackboard_file"
                        if file["type"] == "File"
                        else "blackboard_folder"
                    ),
                    "course_id": course_id,
                    "lms_id": file["id"],
                    "name": file["name"],
                    "size": file["size"],
                    "parent_lms_id": file["parentId"],
                }
                for file in files
            ]
        )

    def _get_all_following_pages(self, response, schema) -> list:
        """
        Get all the paginated responses to `path`.

        Return the results of all of them in one list after parsing them with `schema`.
        """
        results = schema(response).parse()
        for _ in range(PAGINATION_MAX_REQUESTS - 1):
            path = response.json().get("paging", {}).get("nextPage")
            if not path:
                break

            response = self._api.request("GET", path)
            results.extend(schema(response).parse())

        return results

    def _get_all_folders_files(self, course_id, results: list[dict]) -> list[dict]:
        """Get all the files in the folders included in `results` recursively."""
        # Get all the folder URLs from `results`
        folder_urls = [
            self._api._api_url(  # noqa: SLF001
                self._list_files_url(course_id, result["id"])
            )
            for result in results
            if result["type"] == "Folder"
        ]

        # Query all folders at once
        responses = self._request.find_service(name="async_oauth_http").request(
            "GET", folder_urls
        )

        for response in responses:
            # Get all the pages for this folder
            folder_files = self._get_all_following_pages(
                response, BlackboardListFilesSchema
            )
            # For each folder, get it children too
            results.extend(self._get_all_folders_files(course_id, folder_files))

        return results
