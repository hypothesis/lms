from lms.product.plugin.course_copy import CourseCopyFilesHelper, CourseCopyGroupsHelper
from lms.services.moodle import MoodleAPIClient


class MoodleCourseCopyPlugin:
    file_type = "moodle_file"
    page_type = "moodle_page"

    def __init__(
        self,
        api: MoodleAPIClient,
        files_helper: CourseCopyFilesHelper,
        groups_helper: CourseCopyGroupsHelper,
    ):
        self._api = api
        self._groups_helper = groups_helper
        self._files_helper = files_helper

    def find_matching_file_in_course(self, original_file_id, new_course_id):
        return self._files_helper.find_matching_file_in_course(
            self._api.list_files, self.file_type, original_file_id, new_course_id
        )

    def find_matching_page_in_course(self, original_page_id, new_course_id):
        return self._files_helper.find_matching_file_in_course(
            self._api.list_pages, self.page_type, original_page_id, new_course_id
        )

    def find_matching_group_set_in_course(self, course, group_set_id):
        return self._groups_helper.find_matching_group_set_in_course(
            course, group_set_id
        )

    def effective_document_id(
        self,
        log,
        document_url,
        document_course_id,
        document_file_id,
        course,
        current_course_id,
        store_document_mappings,
        get_document_mappings,
        not_found_error_code,
    ) -> str:
        if current_course_id == document_course_id:
            # Not in a course copy scenario, use the IDs from the document_url
            log.debug("Via URL for document in the same course. %s", document_url)
            return document_file_id

        mapped_file_id = get_document_mappings(document_file_id)
        if mapped_file_id != document_file_id:
            log.debug(
                "Via URL for file already mapped for course copy. Document: %s, course: %s, mapped file: %s",
                document_url,
                current_course_id,
                mapped_file_id,
            )
            return mapped_file_id

        # In moodle course copy for files is easier to solve because we don't make
        # requests in the name of the user so we can fix it for all launches.
        # It won't only not succeed if the file doesn't have an equivalent file in the new course
        found_file = self.find_matching_file_in_course(document_file_id, course.lms_id)
        if not found_file:
            log.debug(
                "Via URL for document, couldn't find it in the new course. Document: %s, course: %s.",
                document_url,
                current_course_id,
            )
            raise FileNotFoundInCourse(not_found_error_code, document_url)

        # Store a mapping so we don't have to re-search next time.
        log.debug(
            "Via URL for document, found it in the new course. Document: %s, course: %s, document_id: %s",
            document_url,
            current_course_id,
            found_file.lms_id,
        )
        store_document_mappings(document_file_id, found_file.lms_id)
        return found_file.lms_id

    @classmethod
    def factory(cls, _context, request):
        return cls(
            request.find_service(MoodleAPIClient),
            files_helper=request.find_service(CourseCopyFilesHelper),
            groups_helper=request.find_service(CourseCopyGroupsHelper),
        )
