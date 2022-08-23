from sqlalchemy import func

from lms.models import ApplicationInstance, File
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

    def get_with_guid(self, lms_id, type_):
        """
        Return with the given lms_id and type_ that belongs to the same GUID as the current ApplicationInstance.

        Once we have "Organization" or a similar entity that groups together multiple
        ApplicationInstance we should use that concept instead of GUID but for now
        this allows us to find files across multiple installs in for example
        migrations from course/account/global level install or in some LTI1.3 upgrade
        scenarios.
        """
        return (
            self._db.query(File)
            .join(
                ApplicationInstance,
                ApplicationInstance.tool_consumer_instance_guid
                == self._application_instance.tool_consumer_instance_guid,
            )
            .filter(
                File.lms_id == lms_id,
                File.type == type_,
            )
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


def factory(_context, request):
    return FileService(
        application_instance=request.find_service(
            name="application_instance"
        ).get_current(),
        db=request.db,
    )
