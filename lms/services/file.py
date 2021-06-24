from lms.models import File


class FileService:
    def __init__(self, application_instance, db):
        self._application_instance = application_instance
        self._db = db

    def get(self, lms_id, type_):
        return self._query.filter_by(lms_id=lms_id, type=type_).one_or_none()

    @property
    def _query(self):
        return self._db.query(File).filter_by(
            application_instance=self._application_instance
        )


def factory(_context, request):
    return FileService(
        application_instance=request.find_service(name="application_instance").get(),
        db=request.db,
    )
