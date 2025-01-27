from lms.models import LMSTerm, LTIParams
from lms.services.upsert import bulk_upsert


class LMSTermService:
    def __init__(self, db):
        self._db = db

    def get_term(self, lti_params: LTIParams) -> LMSTerm | None:
        term_starts_at = lti_params.get_datetime("custom_term_start")
        term_ends_at = lti_params.get_datetime("custom_term_end")
        term_id = lti_params.get("custom_term_id")
        term_name = lti_params.get("custom_term_name")
        guid = lti_params["tool_consumer_instance_guid"]

        if not any([term_starts_at, term_ends_at]):
            # We need to have at least one date to consider a term.
            return None

        if term_id:
            # If we get an ID from the LMS we'll use it as the key.
            # We'll scope it the installs GUID
            key = f"{guid}:{term_id}"
        else:
            # Otherwise we'll use the name and dates as part of the key
            key = f"{guid}:{term_name if term_name else '-'}:{term_starts_at if term_starts_at else '-'}:{term_ends_at if term_ends_at else '-'}"

        values = [
            {
                "name": term_name,
                "tool_consumer_instance_guid": guid,
                "starts_at": term_starts_at,
                "ends_at": term_ends_at,
                "key": key,
                "lms_id": term_id,
            }
        ]
        return bulk_upsert(
            self._db,
            model_class=LMSTerm,
            values=values,
            index_elements=["key"],
            update_columns=["updated", "name", "starts_at", "ends_at"],
        ).first()


def factory(_context, request):
    return LMSTermService(db=request.db)
