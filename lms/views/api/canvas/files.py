"""Proxy API views for files-related Canvas API endpoints."""
from functools import lru_cache

from pyramid.view import view_config, view_defaults
from sqlalchemy import or_

from lms.services import CanvasFileNotFoundInCourse, CanvasAPIPermissionError
from lms.views import helpers
from lms.models import CanvasFile


@view_defaults(permission="api", renderer="json")
class FilesAPIViews:
    def __init__(self, request):
        self.request = request
        self.canvas_api_client = request.find_service(name="canvas_api_client")

    @view_config(request_method="GET", route_name="canvas_api.courses.files.list")
    def list_files(self):
        """
        Return the list of files in the given course.

        :raise lms.services.CanvasAPIError: if the Canvas API request fails.
            This exception is caught and handled by an exception view.
        """
        return self.canvas_api_client.list_files(
            self.request.matchdict["course_id"],
            self.request.lti_user.oauth_consumer_key,
            self.request.lti_user.tool_consumer_instance_guid,
        )

    @view_config(request_method="GET", route_name="canvas_api.files.via_url")
    def via_url(self):
        """
        Return the Via URL for annotating the given Canvas file.

        :raise lms.services.CanvasAPIError: if the Canvas API request fails.
            This exception is caught and handled by an exception view.
        """
        tool_consumer_instance_guid = self.request.lti_user.tool_consumer_instance_guid
        consumer_key = self.request.lti_user.oauth_consumer_key
        matchdict = self.request.matchdict
        course_id = self.request.matchdict["course_id"]

        def get_file_from_db(file_id=None, course_id=None, filename=None, size=None):
            query = self.request.db.query(CanvasFile).filter_by(
                consumer_key=consumer_key,
                tool_consumer_instance_guid=tool_consumer_instance_guid,
            )

            if file_id:
                query = query.filter(
                    or_(
                        CanvasFile.file_id == file_id,
                        CanvasFile.file_id_override == file_id,
                    )
                )

            if course_id:
                query = query.filter_by(course_id=course_id)

            if filename:
                query = query.filter_by(filename=filename)

            if size:
                query = query.filter_by(size=size)

            return query.first()

        def get_file_id():
            canvas_file = get_file_from_db(matchdict["file_id"], course_id)

            if canvas_file:
                return canvas_file.file_id

            # The original Canvas file, in another course, from which this
            # assignment's file was copied.
            original_file = get_file_from_db(matchdict["file_id"])

            if original_file:
                # A file in this course that has the same filename and size as
                # the original assignment's file.
                matching_file = get_file_from_db(
                    course_id=course_id,
                    filename=original_file.filename,
                    size=original_file.size,
                )

                if matching_file:
                    self.request.db.add(
                        CanvasFile(
                            consumer_key=consumer_key,
                            tool_consumer_instance_guid=tool_consumer_instance_guid,
                            course_id=course_id,
                            filename=matching_file.filename,
                            size=matching_file.size,
                            file_id=matchdict["file_id"],
                            file_id_override=matching_file.file_id,
                        )
                    )

                    return matching_file.file_id

            return None

        file_id = get_file_id()

        if not file_id:
            # Update the DB with the latest listing of files (that the current
            # user can see) from this Canvas course.
            self.canvas_api_client.list_files(
                course_id, consumer_key, tool_consumer_instance_guid
            )
            file_id = get_file_id()

        if file_id:
            # Return a successful response (if the public_url API call succeeds).
            public_url = self.canvas_api_client.public_url(file_id)

            # Currently we only let users pick PDF files, so we can save a little
            # time by specifying this, instead of Via having to work it out
            via_url = helpers.via_url(self.request, public_url, content_type="pdf")

            return {"via_url": via_url}
        else:
            # We couldn't find a matching file in the course, either by looking
            # in our DB or by listing the course's files from the Canvas API.
            # Return an error response.
            if self.request.lti_user.is_instructor:
                raise CanvasFileNotFoundInCourse(matchdict["file_id"])
            raise CanvasAPIPermissionError()
