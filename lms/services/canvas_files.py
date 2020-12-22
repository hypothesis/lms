from lms.models import CanvasFile


class CanvasFilesService:
    """Methods for working with the models.CanvasFile DB model."""

    def __init__(self, db):
        self._db = db

    def upsert(self, canvas_file):
        existing_file = (
            self._db.query(CanvasFile)
            .filter_by(
                consumer_key=canvas_file.consumer_key,
                tool_consumer_instance_guid=canvas_file.tool_consumer_instance_guid,
                course_id=canvas_file.course_id,
                file_id=canvas_file.file_id,
            )
            .one_or_none()
        )

        if existing_file:
            existing_file.filename = canvas_file.filename
            existing_file.size = canvas_file.size
        else:
            self._db.add(canvas_file)


def factory(_context, request):
    return CanvasFilesService(request.db)
