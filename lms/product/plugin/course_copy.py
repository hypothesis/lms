from typing import Callable, Optional

from lms.models import File
from lms.services.exceptions import ExternalRequestError, OAuth2TokenError
from lms.services.file import FileService


class CourseCopyGroupsHelper:
    def __init__(self, course_service, grouping_plugin):
        self._course_service = course_service
        self._grouping_plugin = grouping_plugin

    def find_matching_group_set_in_course(self, course, group_set_id):
        mapped_group_set_id = course.get_mapped_group_set_id(group_set_id)

        if mapped_group_set_id != group_set_id:
            return mapped_group_set_id

        try:
            # Get the current (copied) courses files, that will have the side effect of storing files in the DB
            _ = self._grouping_plugin.get_group_sets(course, course.lms_id)
        except Exception as error:
            # We might not have access to use the API for that endpoint.
            # That will depend on our role and the course's permissions settings.
            # We will continue anyway, maybe the files of the new course are already in the DB
            # after an instructor launched corrected the issue.
            raise error
            pass

        # We get the original file record from the DB
        group_set = self._course_service.find_group_set(group_set_id=group_set_id)
        if not group_set:
            # That file must have been recorded when the original assignment was configured.
            # If we can't find that one something odd is going on, stop here.
            return group_set_id

        # Now we'll try to find a matching file in the DB in the new course
        # We might have a record of this because we just called `_store_new_course_files` as the current user
        # or another user might have done it before for us.

        if new_group_set := self._course_service.find_group_set(
            name=group_set["name"], context_id=course.lms_id
        ):
            # We found the equivalent file in the new course
            course.set_mapped_group_set_id(group_set_id, new_group_set["id"])
            return new_group_set["id"]

        # No match for the file.
        # This could be an issue with our heuristic to find the new file
        # or other edge case, for example a file was deleted after course copy or similar.
        return group_set_id

    @classmethod
    def factory(cls, _context, request):
        return cls(request.find_service(name="course"), request.product.plugin.grouping)


class CourseCopyFilesHelper:
    """Helper class to abstract common behaviour around LMS file / course copy."""

    @staticmethod
    def is_file_in_course(file_service: FileService, course_id, file_id, type_) -> bool:
        """Check if `file_id` belongs to `course_id`."""

        file = file_service.get(lms_id=file_id, type_=type_)
        if not file or file.course_id != course_id:
            return False

        return True

    @staticmethod
    def find_matching_file_in_course(
        store_new_course_files: Callable[[str], None],
        file_service: FileService,
        file_type: str,
        original_file_id,
        new_course_id,
    ) -> Optional[File]:
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
        file = file_service.get(original_file_id, type_=file_type)
        if not file:
            # That file must have been recorded when the original assignment was configured.
            # If we can't find that one something odd is going on, stop here.
            return None

        # Now we'll try to find a matching file in the DB in the new course
        # We might have a record of this because we just called `_store_new_course_files` as the current user
        # or another user might have done it before for us.

        if new_file := file_service.find_copied_file(new_course_id, file):
            # We found the equivalent file in the new course
            return new_file

        # No match for the file.
        # This could be an issue with our heuristic to find the new file
        # or other edge case, for example a file was deleted after course copy or similar.
        return None

    @staticmethod
    def get_mapped_file_id(course, file_id):
        """
        Get a previously mapped file id in course.

        Returns the original `file_id` if no mapped one can be found.
        """
        return course.extra.get("course_copy_file_mappings", {}).get(file_id, file_id)

    @staticmethod
    def set_mapped_file_id(course, old_file_id, new_file_id):
        """Store the mapping between old_file_id and new_file_id for future launches."""
        course.extra.setdefault("course_copy_file_mappings", {})[
            old_file_id
        ] = new_file_id


class CourseCopyPlugin:  # pragma: nocover
    """
    Empty implementation of the CourseCopyPlugin protocol.

    We'll have implementations for each product where we support course copy
    """

    def is_file_in_course(self, course_id, file_id):
        raise NotImplementedError()

    def find_matching_file_in_course(self, *args, **kwargs):
        raise NotImplementedError()

    def find_mapped_group_set_id(self, course, group_set_id):
        raise NotImplementedError()
