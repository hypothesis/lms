from sqlalchemy import func

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

    def find_copied_file(self, new_course_id, original_file: File):
        """Find an equivalent file to `original_file` in our DB."""
        return (
            self._db.query(File).filter(
                # Both files should be in the same application instance
                File.application_instance == original_file.application_instance,
                # Looking for files in the new course only
                File.course_id == new_course_id,
                # Files of the same type
                File.type == original_file.type,
                # We don't want to find the same file we are looking for
                File.lms_id != original_file.lms_id,
                # And as a heuristic, we reckon same name, same size, probably the same file
                File.name == original_file.name,
                File.size == original_file.size,
            )
            # We might find more than one matching file, take any of them
            .first()
        )

    def upsert(self, file_dicts):
        """Insert or update a batch of files."""
        for value in file_dicts:
            value["application_instance_id"] = self._application_instance.id
            value["updated"] = func.now()

        return bulk_upsert(
            self._db,
            File,
            file_dicts,
            index_elements=["application_instance_id", "lms_id", "type", "course_id"],
            update_columns=["name", "size", "updated"],
        )


def factory(_context, request):
    return FileService(
        application_instance=request.find_service(
            name="application_instance"
        ).get_current(),
        db=request.db,
    )
