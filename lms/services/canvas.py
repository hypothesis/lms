from functools import cached_property, lru_cache
from logging import getLogger

from sqlalchemy import and_

from lms.models import File
from lms.services.exceptions import CanvasAPIPermissionError, CanvasFileNotFoundInCourse

LOG = getLogger(__name__)


class CanvasService:
    """A high level Canvas service."""

    api = None

    def __init__(
        self, canvas_api, application_instance_service, assignment_service, db_session
    ):
        self.api = canvas_api

        self._application_instance_service = application_instance_service
        self._assignment_service = assignment_service
        self._db_session = db_session

    def public_url_for_file(
        self, file_id, course_id, resource_link_id, check_in_course=False
    ):
        """
        Get a public URL for a Canvas file.

        This will also attempt to use any file with the same size and name if
        one can be found.

        :param file_id: The file to look up
        :param course_id: The course the file should be in
        :param resource_link_id: The id of the assignment
        :param check_in_course: Attempt to map detect and map the file if it's
            not in the course before attempting to retrieve it. This is more
            thorough, but causes an extra API request
        :return: A URL suitable for public presentation of the file
        :raise CanvasFileNotFoundInCourse: if the file is not accessible and
            cannot be mapped to a file in the course
        :raise CanvasAPIResourceNotFound: if the file is not valid at all, and
            cannot be mapped to a file in the course
        :raise CanvasAPIPermissionError: If we cannot retrieve the file for
            any other reason
        """
        # Check to see if we've mapped this file id to something else before
        file_mapping = self._file_mapping(resource_link_id)
        mapped_id = file_mapping.get(file_id, default=file_id)

        # If we are told to check up front, try and fix the file if it's not in
        # the current course (as far as we can tell from this users point of
        # view)
        already_mapped = False
        if check_in_course and not self._is_file_in_course(mapped_id, course_id):
            mapped_id = self._match_file_in_course(file_id, course_id, file_mapping)
            already_mapped = True

            if not mapped_id:
                raise CanvasFileNotFoundInCourse(file_id)

        try:
            return self.api.public_url(mapped_id)

        except CanvasAPIPermissionError:
            # If we've already mapped this once, we aren't going to get a
            # better answer now. So bail out
            if already_mapped:
                raise

            if not (
                mapped_id := self._match_file_in_course(
                    file_id, course_id, file_mapping
                )
            ):
                # We don't know why this failed, could be a course copy, could
                # just be a permissions issue, all we know is we can't fix it
                raise

        return self.api.public_url(mapped_id)

    @lru_cache
    def _file_mapping(self, resource_link_id):
        assignment = self._assignment_service.get(
            tool_consumer_instance_guid=self._application_instance.tool_consumer_instance_guid,
            resource_link_id=resource_link_id,
        )
        return CanvasFileMapping(assignment.extra)

    @cached_property
    def _application_instance(self):
        return self._application_instance_service.get()

    @lru_cache
    def _files_in_course(self, course_id):
        return self.api.list_files(course_id)

    def _is_file_in_course(self, file_id, course_id):
        LOG.debug("Checking if Canvas file %s is in course %s", file_id, course_id)

        return any(
            str(file_["id"]) == str(file_id)
            for file_ in self._files_in_course(course_id)
        )

    def _match_file_in_course(self, file_id, course_id, file_mapping):
        """
        Find matches in the current course for the specified files.

        And update the mapping to match

        :param file_id: The original file to match
        :param course_id: The course to find a matching file in
        :return: A mapped file, or None
        """

        file_ids_to_match = [file_id]

        # We match not only the original id, but also the mapped id too. This
        # allows us to code with some low probability scenarios where we have
        # a mapping, the source and target of the mapping are inaccessible,
        # and the source's name or size has changed. In this case we can use
        # the information from the target to try and find a new matching file.
        if target := file_mapping.get(file_id):
            file_ids_to_match.append(target)

        files_to_match = (
            self._db_session.query(File)
            .filter(
                and_(
                    File.application_instance_id == self._application_instance.id,
                    File.lms_id.in_(file_ids_to_match),
                    File.type == "canvas_file",
                )
            )
            .all()
        )

        if files_to_match:
            matching_keys = set((file.name, file.size) for file in files_to_match)
            LOG.debug(
                "Looking for matches in current course for Canvas files %s",
                matching_keys,
            )

            for candidate in self._files_in_course(course_id):
                if (candidate["display_name"], candidate["size"]) in matching_keys:
                    # Update the mapping first!
                    file_mapping[file_id] = candidate["id"]
                    LOG.info(
                        "Found match for inaccessible Canvas file %s -> %s",
                        file_id,
                        candidate["id"],
                    )

                    return candidate["id"]
        else:
            LOG.debug("No historical records of Canvas files found to perform match")

        return None


class CanvasFileMapping:
    """
    An abstraction the file mapping to appear dict like.

    This is a little tricky because we need to deal with a sub-key of a JSON
    field in the DB. This makes this look like a dict in some ways.
    """

    KEY = ("canvas", "file_mapping")

    def __init__(self, settings):
        self._settings = settings

    def get(self, file_id, default=None):
        return self._mapping.get(file_id, default)

    def __setitem__(self, old_file_id, new_file_id):
        mapping = self._mapping
        mapping[old_file_id] = new_file_id

        self._settings.set(*self.KEY, mapping)

    @property
    def _mapping(self):
        return self._settings.get(*self.KEY) or {}


def factory(_context, request):
    return CanvasService(
        application_instance_service=request.find_service(name="application_instance"),
        assignment_service=request.find_service(name="assignment"),
        canvas_api=request.find_service(name="canvas_api_client"),
        db_session=request.db,
    )
