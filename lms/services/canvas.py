from lms.services.exceptions import CanvasAPIPermissionError, CanvasFileNotFoundInCourse


class CanvasService:
    """A high level Canvas service."""

    api = None

    def __init__(self, canvas_api, file_service):
        self.api = canvas_api
        self._finder = CanvasFileFinder(canvas_api, file_service)

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

    @staticmethod
    def is_speedgrader(request) -> bool:
        if "learner_canvas_user_id" in request.GET:
            # Location while launching an assignment
            return bool(request.GET["learner_canvas_user_id"])

        # Location when using the Sync API
        try:
            return "learner" in request.json
        except:  # pylint:disable=bare-except
            return False

    @staticmethod
    def group_set(request) -> int:
        if "group_set" in request.params:
            # Location while launching an assignment
            value = request.params["group_set"]
        else:
            # Location when using the Sync API
            value = request.json["learner"].get("group_set")

        return int(value)

    @staticmethod
    def is_group_launch(request) -> bool:
        try:
            CanvasService.group_set(request)
        except (KeyError, ValueError, TypeError):
            return False
        else:
            return True


class CanvasFileFinder:
    """A helper for finding file IDs in the Canvas API."""

    def __init__(self, canvas_api, file_service):
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
        for file_id in file_ids:
            file = self._file_service.get(file_id, type_="canvas_file")

            if not file:
                continue

            for file_dict in self._api.list_files(course_id):
                if (
                    file_dict["display_name"] == file.name
                    and file_dict["size"] == file.size
                    and str(file_dict["id"]) != file.lms_id
                ):
                    return str(file_dict["id"])

        return None


def factory(_context, request):
    return CanvasService(
        canvas_api=request.find_service(name="canvas_api_client"),
        file_service=request.find_service(name="file"),
    )
