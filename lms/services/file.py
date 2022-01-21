from lms.models import File
from lms.services.upsert import bulk_upsert


class FileService:
    def __init__(self, application_instance, db):
        self._application_instance = application_instance
        self._db = db

    def get(self, lms_id, type_):
        """Return the file with the given lms_id and type_ or None."""
        return (
            self._db.query(File)
            .filter_by(
                application_instance=self._application_instance,
                lms_id=lms_id,
                type=type_,
            )
            .one_or_none()
        )

    def upsert(self, values):
        """Inset or update a batch of files."""
        for value in values:
            value["application_instance_id"] = self._application_instance.id

        return bulk_upsert(
            self._db,
            File,
            values,
            index_elements=["application_instance_id", "lms_id", "type", "course_id"],
            update_columns=["name", "size"],
        )


def factory(_context, request):
    return FileService(
        application_instance=request.find_service(
            name="application_instance"
        ).get_current(),
        db=request.db,
    )
