import logging

from lms.services.exceptions import CanvasAPIPermissionError, CanvasFileNotFoundInCourse


logger = logging.getLogger(__name__)


class CanvasService:
    """A high level Canvas service."""

    api = None

    def __init__(self, canvas_api, file_service):
        self.api = canvas_api
        self._file_service = file_service

    def public_url_for_file(
        self, file_id, course_id, module_item_configuration, check_in_course=False
    ):
        mapped_file_id = module_item_configuration.get_mapped_file_id(file_id)

        if mapped_file_id:
            # If there's a previously stored mapping for file_id use that instead.
            logger.info("Found a previously mapped_file_id: %s", mapped_file_id)
            effective_file_id = mapped_file_id
        else:
            logger.info("No previously mapped_file_id")
            effective_file_id = file_id

        try:
            return self._public_url(
                effective_file_id,
                course_id=course_id if check_in_course else None,
            )
        except (CanvasFileNotFoundInCourse, CanvasAPIPermissionError) as err:
            if isinstance(err, CanvasFileNotFoundInCourse):
                logger.info("File not found in course")
            else:
                logger.info("Got a permissions error from Canvas")

            # Look up the file's metadata in our DB.
            file_ = self._file_service.get(effective_file_id, type_="canvas_file")

            if not file_:
                logger.info("File was not found in DB")
                raise

            # Find a matching file in the current course.
            found_file_id = self.find(course_id, file_)

            if not found_file_id:
                logger.info("No matching file was found in course")
                raise

            logger.info("A matching file was found in the course")
            logger.info("Updating the mapping and trying again")

            # Update the mapping.
            module_item_configuration.set_mapped_file_id(file_id, found_file_id)

            # Try again with the new file_id.
            return self._public_url(found_file_id)

    def _public_url(self, file_id, course_id=None):
        if course_id and not self.is_file_in_course(file_id, course_id):
            raise CanvasFileNotFoundInCourse(file_id)

        return self.api.public_url(file_id)

    def find(self, course_id, file_):
        file_dicts = self.api.list_files(course_id)

        for file_dict in file_dicts:
            display_name = file_dict["display_name"]
            size = file_dict["size"]

            if display_name == file_.name and size == file_.size:
                return str(file_dict["id"])

        return None

    def is_file_in_course(self, file_id, course_id):
        files_in_course = self.api.list_files(course_id)

        for file_ in files_in_course:
            if str(file_["id"]) == file_id:
                return True

        return False


def factory(_context, request):
    return CanvasService(
        canvas_api=request.find_service(name="canvas_api_client"),
        file_service=request.find_service(name="file"),
    )
