from sqlalchemy import func

from lms.models import ApplicationInstance, File
from lms.services.upsert import bulk_upsert


class FileService:
    def __init__(self, application_instance, db):
        self._application_instance = application_instance
        self._db = db

    def get(self, lms_id, type_, course_id=None) -> File | None:
        """Return the file with the given parameters or None."""
        return (
            self._file_search_query(
                guid=self._application_instance.tool_consumer_instance_guid,
                lms_id=lms_id,
                type_=type_,
                course_id=course_id,
            )
            # We might have recorded the same file twice in different ApplicationInstances
            # as we query by GUID we might get more than once row, in that case we prefer the newest
            .order_by(File.id.desc())
            .first()
        )

    def find_copied_file(self, new_course_id, original_file: File):
        """Find an equivalent file to `original_file` in our DB."""
        return (
            self._file_search_query(
                # Both files should be in the same institution
                guid=self._application_instance.tool_consumer_instance_guid,
                # Files of the same type
                type_=original_file.type,
                # Looking for files in the new course only
                course_id=new_course_id,
                # And as a heuristic, we reckon same name, same size, probably the same file
                name=original_file.name,
                size=original_file.size,
            )
            .filter(
                # We don't want to find the same file we are looking for
                File.id != original_file.id,
            )
            # We might find more than one matching file, prefer the newest
            .order_by(File.id.desc())
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

    def _file_search_query(  # noqa: PLR0913
        self, guid, type_, *, lms_id=None, course_id=None, name=None, size=None
    ):
        """Return a `File` query with the passed parameters applied as filters."""
        query = (
            self._db.query(File)
            .join(ApplicationInstance)
            .filter(
                # We don't query by application_instance but any file belonging to an AI with the same GUID
                ApplicationInstance.tool_consumer_instance_guid == guid,
                File.type == type_,
            )
        )

        if lms_id:
            query = query.filter(File.lms_id == lms_id)

        if course_id:
            query = query.filter(File.course_id == course_id)

        if name:
            query = query.filter(File.name == name)

        if size:
            query = query.filter(File.size == size)

        return query


def factory(_context, request):
    return FileService(
        application_instance=request.lti_user.application_instance, db=request.db
    )
