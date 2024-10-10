from collections.abc import Callable
from typing import Any

from lms.models import File
from lms.services.exceptions import ExternalRequestError, OAuth2TokenError
from lms.services.file import FileService


class CourseCopyFilesHelper:
    """Helper class to abstract common behaviour around LMS file / course copy."""

    def __init__(self, file_service: FileService):
        self._file_service = file_service

    def is_file_in_course(self, course_id, file_id, type_) -> bool:
        """Check if `file_id` belongs to `course_id`."""

        return bool(
            self._file_service.get(lms_id=file_id, type_=type_, course_id=course_id)
        )

    def find_matching_file_in_course(
        self,
        store_new_course_files: Callable[[str], Any] | Callable[[int], Any],
        file_type: str,
        original_file_id,
        new_course_id,
    ) -> File | None:
        try:
            # Get the current (copied) courses files, that will have the side effect of storing files in the DB
            _ = store_new_course_files(new_course_id)
        except OAuth2TokenError:
            # If the issue while trying to talk to the API is OAuth related
            # let that bubble up and be dealt with.
            raise
        except ExternalRequestError:
            # We might not have access to use the API for that endpoint.
            # That will depend on our role and the course's permissions settings.
            # We will continue anyway, maybe the files of the new course are already in the DB
            # after an instructor launched corrected the issue.
            pass

        # We get the original file record from the DB
        file = self._file_service.get(original_file_id, type_=file_type)
        if not file:
            # That file must have been recorded when the original assignment was configured.
            # If we can't find that one something odd is going on, stop here.
            return None

        # Now we'll try to find a matching file in the DB in the new course
        # We might have a record of this because we just called `_store_new_course_files` as the current user
        # or another user might have done it before for us.

        if new_file := self._file_service.find_copied_file(new_course_id, file):
            # We found the equivalent file in the new course
            return new_file

        # No match for the file.
        # This could be an issue with our heuristic to find the new file
        # or other edge case, for example a file was deleted after course copy or similar.
        return None

    @classmethod
    def factory(cls, _context, request):
        return cls(request.find_service(name="file"))


class CourseCopyGroupsHelper:
    def __init__(self, course_service, grouping_plugin):
        self._course_service = course_service
        self._grouping_plugin = grouping_plugin

    def find_matching_group_set_in_course(self, course, group_set_id):
        """
        Find the corresponding `group_set_id` in course.

        This could different from `group_set_id` if course has been course copied and we still point to the old's course group set.
        """
        try:
            # Get the current (copied) group sets, that will have the side effect of storing them in the DB
            _ = self._grouping_plugin.get_group_sets(course)
        except OAuth2TokenError:
            # If the issue while trying to talk to the API is OAuth related
            # let that bubble up and be dealt with.
            raise
        except ExternalRequestError:
            # We might not have access to use the API for that endpoint.
            # That will depend on our role and the course's permissions settings.
            # We will continue anyway, maybe the group sets of the new course are already in the DB
            # after an instructor launch corrected the issue.
            pass

        # Get the original group set from the DB
        group_set = self._course_service.find_group_set(group_set_id=group_set_id)
        if not group_set:
            # If we haven't found it could that either:
            # - The group set doesn't belong to this course
            # - The original assignment was configured before we rolled out this feature,
            #   and we didn't store the group sets in the DB.
            return None

        # Try to find a matching group set in the new course.
        # We might have a record of this because we just called `grouping_plugin.get_group_sets` as the current user
        # or another user might have done it before for us.
        if new_group_set := self._course_service.find_group_set(
            name=group_set["name"], context_id=course.lms_id
        ):
            # We found a match, store it to save the search for next time
            course.set_mapped_group_set_id(group_set_id, new_group_set["id"])
            return new_group_set["id"]

        # No match
        return None

    @classmethod
    def factory(cls, _context, request):
        return cls(request.find_service(name="course"), request.product.plugin.grouping)


class CourseCopyPlugin:  # pragma: nocover
    """
    Empty implementation of the CourseCopyPlugin protocol.

    We'll have implementations for each product where we support course copy
    """

    def is_file_in_course(self, course_id, file_id):
        raise NotImplementedError()

    def find_matching_file_in_course(self, original_file_id, new_course_id):
        raise NotImplementedError()

    def find_matching_group_set_in_course(self, _course, group_set_id):
        raise NotImplementedError()

    def find_matching_page_in_course(self, original_file_id, new_course_id):
        raise NotImplementedError()
