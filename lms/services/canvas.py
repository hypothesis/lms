from lms.services.exceptions import CanvasAPIPermissionError, CanvasFileNotFoundInCourse

from lms.models import File


class CanvasService:
    """A high level Canvas service."""

    api = None

    def __init__(self, db, canvas_api, file_service):
        self.api = canvas_api
        self._finder = CanvasFileFinder(db, canvas_api, file_service)

    def public_url_for_file(
        self, assignment, file_id, course_id, check_in_course=False
    ):
        """
        Return a public URL for file_id.

        :param assignment: the current assignment
        :param file_id: the Canvas API ID of the file
        :param course_id: the Canvas API ID of the course that the file is in
        :param check_in_course: whether to check that file_id is in course_id

        :raise CanvasFileNotFoundInCourse: if check_in_course was True and the
            current user can't see file_id in course_id's list of files

        :raise CanvasAPIPermissionError: if the user gets a permissions error
            from the Canvas API when trying to get a public URL for file_id
        """
        # If there's a previously stored mapping for file_id use that instead.
        effective_file_id = assignment.get_canvas_mapped_file_id(file_id)

        try:
            if check_in_course:
                self._finder.assert_file_in_course(course_id, effective_file_id)
            return self.api.public_url(effective_file_id)
        except (CanvasFileNotFoundInCourse, CanvasAPIPermissionError):
            # The user can't see the file in the course. This could be because:
            #
            # * The course has been copied so the assignment's file_id is from
            #   the original course (and the user isn't in the original course)
            # * The assignment's file has been deleted from Canvas
            # * The file *is* in the course but the user can't see it
            #   (only instructors can see "unpublished" files in Canvas)
            #
            # We'll try to find another copy of the same file that the current
            # user *can* see in the current course and use that instead.
            found_file_id = self._finder.find_matching_file_in_course(
                course_id,
                # Use a set to avoid searching for the same ID twice if file_id
                # and effective_file_id are the same.
                {file_id, effective_file_id},
            )

            if not found_file_id:
                raise

            # Try again to return a public URL, this time using found_file_id.
            url = self.api.public_url(found_file_id)

            # Store a mapping so we don't have to re-search next time.
            assignment.set_canvas_mapped_file_id(file_id, found_file_id)

            return url


class CanvasFileFinder:
    """A helper for finding file IDs in the Canvas API."""

    def __init__(self, db, canvas_api, file_service):
        self._db = db
        self._api = canvas_api
        self._file_service = file_service

    def assert_file_in_course(self, course_id, file_id):
        """Raise if the current user can't see file_id in course_id."""
        for file in self._api.list_files(course_id):
            # The Canvas API returns file IDs as ints but the file_id param
            # that this method receives (from our proxy API) is a string.
            # Convert ints to strings so that we can compare them.
            if str(file["id"]) == file_id:
                return

        raise CanvasFileNotFoundInCourse(file_id)

    def find_matching_file_in_course(self, course_id, file_ids):
        """
        Return the ID of a file in course_id that matches one of the files in file_ids.

        Search for a file that the current Canvas user can see in course_id and
        that matches one of the files in file_id's (same filename and size) and
        return the matching file's ID.

        Return None if no matching file is found.
        """

        try:
            # Get the current (copied) courses files, that will have the side effect of storing files in the DB
            _ = self._api.list_files(course_id)
        except:
            # We might not have access to use the API for that endpoint.
            # That will depend on our role and the course's file navigation settings
            # We will continue anyway, maybe the files of the new course are already in the DB
            # after an instructor launched
            pass

        # Go over the potential file_ids for the current course file
        for file_id in file_ids:
            # This is odd, we are querying by just "file_id", should't original_course_id be part of the query
            # (note that original_course_id) is not around but we could get it from LTIParams
            # Anyway, we get the original file record from the DB
            file = self._file_service.get(file_id, type_="canvas_file")
            if not file:
                continue

            # Now we'll try to find a matching file in the DB in the new course
            # We might have a record of this because we jsut called `list_files` as teh current user
            # or another user might have done it before for us.
            new_file = (
                self._db.query(File)
                .filter(
                    # Same application instance, not enterly correct but fine (it should be same tool_guid, or ideally same org)
                    File.application_instance == file.application_instance,
                    # Same type, `canvas_file` here
                    File.type_ == file.type_,
                    # We don't want to find the same file we are looking for
                    File.lms_id == file.lms_id,
                    # And as a heuristic, we reckon same name, same size, probably the sme file
                    File.name == file.name,
                    File.size == file.size,
                )
                .first()
            )

            if new_file:
                return new_file.lms_id

        # No match for the file.
        # This will always be the case if:
        #    - Course file's navigation is disabled
        #     - The first launch on the course is by a student
        # Other edge cases might also be possible if for example a file
        # is deleted after course copy or similar.
        return None


def factory(_context, request):
    return CanvasService(
        db=request.db,
        canvas_api=request.find_service(name="canvas_api_client"),
        file_service=request.find_service(name="file"),
    )
