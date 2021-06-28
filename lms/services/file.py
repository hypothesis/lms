from lms.models import File


class FileService:
    def __init__(self, db):
        self._db = db

    def get(self, application_instance, lms_id, type_):
        """Return the file with application_instance, lms_id and type_ or None."""
        return (
            self._db.query(File)
            .filter_by(
                application_instance=application_instance, lms_id=lms_id, type=type_
            )
            .one_or_none()
        )


def factory(_context, request):
    return FileService(db=request.db)
