from lms.models import File
from lms.services.exceptions import CanvasFileNotFoundInCourse


class CourseCopyPlugin:
    file_type = None

    def assert_file_in_course(self, course_id, file_id):
        """Raise if the current user can't see file_id in course_id."""
        raise NotImplementedError()

    def find_matching_file_in_course(self, original_file_id, new_course_id):
        try:
            # Get the current (copied) courses files, that will have the side effect of storing files in the DB
            _ = self._store_new_course_files(new_course_id)
            self._db.flush()
            print("GET ALL")
        except:  # TODO only API related expceionts
            raise
            # We might not have access to use the API for that endpoint.
            # That will depend on our role and the course's file navigation settings
            # We will continue anyway, maybe the files of the new course are already in the DB
            # after an instructor launched
            pass

        # This is odd, we are querying by just "file_id", should't original_course_id be part of the query
        # (note that original_course_id) is not around but we could get it from LTIParams
        # Anyway, we get the original file record from the DB
        file = self._file_service.get(original_file_id, type_=self.file_type)
        print("OLD FILE", file, original_file_id)
        if not file:
            return

        # Now we'll try to find a matching file in the DB in the new course
        # We might have a record of this because we just called `list_files` as teh current user
        # or another user might have done it before for us.
        new_file = (
            self._db.query(File)
            .filter(
                # Same application instance, not entirely correct but fine (it should be same tool_guid, or ideally same org)
                File.application_instance == file.application_instance,
                # Looking for files in the original course only
                File.course_id == new_course_id,
                # Same type, `canvas_file` here
                File.type == file.type,
                # We don't want to find the same file we are looking for
                File.lms_id != file.lms_id,
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
        #    - The first launch on the course is by a student
        # Other edge cases might also be possible if for example a file
        # is deleted after course copy or similar.
        return None

    @staticmethod
    def get_mapped_file_id(course, file_id):
        print("GETTING mapped", course.extra, file_id)
        mapped = course.extra.get("course_copy_file_mappings", {}).get(file_id, file_id)

        print("mapped from method", mapped)
        return mapped

    @staticmethod
    def set_mapped_file_id(course, old_file_id, new_file_id):
        course.extra.setdefault("course_copy_file_mappings", {})[
            old_file_id
        ] = new_file_id

    def _store_new_course_files(self, course_id):
        raise NotImplementedError()
