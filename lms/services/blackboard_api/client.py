from urllib.parse import urlencode

from lms.models import File
from lms.services.blackboard_api._schemas import (
    BlackboardListFilesSchema,
    BlackboardListGroups,
    BlackboardListGroupSetsSchema,
    BlackboardPublicURLSchema,
)
from lms.services.exceptions import BlackboardFileNotFoundInCourse, ExternalRequestError
from lms.services.upsert import bulk_upsert

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

        application_instance = self._request.find_service(
            name="application_instance"
        ).get_current()

        bulk_upsert(
            self._request.db,
            File,
            [
                {
                    "application_instance_id": application_instance.id,
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
            ["application_instance_id", "lms_id", "type", "course_id"],
            ["name", "size"],
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
                    self._api._api_url(  # pylint: disable=protected-access
                        f"/learn/api/public/v2/courses/uuid:{course_id}/groups/{group['id']}"
                    )
                )

        if self_enrollment_groups:
            responses = self._request.find_service(name="async_oauth_http").request(
                "GET", self_enrollment_check_urls
            )
            # If we are a member of any of the SelfEnrollment groups
            # we'll get a 200 response from the endpoint
            self_enrollment_groups = [
                group
                for group, response in zip(self_enrollment_groups, responses)
                if response.status == 200
            ]
        return self_enrollment_groups + instructor_only_groups
