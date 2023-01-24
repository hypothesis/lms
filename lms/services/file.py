from typing import Optional

from sqlalchemy import func

from lms.models import File
from lms.services.upsert import bulk_upsert


class FileService:
    def __init__(self, application_instance, db):
        self._application_instance = application_instance
        self._db = db

    def get(self, lms_id, type_) -> Optional[File]:
        """Return the file with the given lms_id and type_."""
        return self._search_query(
            application_instance=self._application_instance,
            lms_id=lms_id,
            type_=type_,
        ).one_or_none()

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

    def _search_query(self, application_instance=None, lms_id=None, type_=None):
        """Build a SQLA query *and-ing* all the search criteria."""
        clauses = []
        query = self._db.query(File)

        if application_instance:
            clauses.append(File.application_instance == application_instance)

        if lms_id:
            clauses.append(File.lms_id == lms_id)

        if type_:
            clauses.append(File.type == type_)

        if clauses:
            query = query.filter(*clauses)

        return query


def factory(_context, request):
    return FileService(
        application_instance=request.find_service(
            name="application_instance"
        ).get_current(),
        db=request.db,
    )
