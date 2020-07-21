import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict

from lms.db import BASE

__all__ = ["GroupInfo"]


class GroupInfo(BASE):
    """
    Some info about an LMS group that was created in h.

    This info is stored purely for metrics/analytics purposes and shouldn't be
    used for application logic. The app should treat the h API as the
    "single-source of truth" about what h groups exist and what their IDs and
    other properties are.
    """

    __tablename__ = "group_info"

    id = sa.Column(sa.Integer(), autoincrement=True, primary_key=True)

    #: The authority_provided_id of the group in h.
    #:
    #: This corresponds to the ID part of the groupid that's used in h's groups
    #: API. For example if the groupid is "group:SOME_ID@lms.hypothesis.is"
    #: then the authority_provided_id is the "SOME_ID" part without the leading
    #: "group:" or the trailing "@lms.hypothes.is".
    #:
    #: This also corresponds to the group.authority_provided_id column in h's
    #: DB.
    authority_provided_id = sa.Column(sa.UnicodeText(), nullable=False, unique=True)

    #: The LTI consumer_key (oauth_consumer_key) of the application instance
    #: that this access token belongs to.
    consumer_key = sa.Column(
        sa.String(),
        sa.ForeignKey("application_instances.consumer_key", ondelete="cascade"),
        nullable=False,
    )

    #: The ApplicationInstance that this group belongs to.
    application_instance = sa.orm.relationship(
        "ApplicationInstance", back_populates="group_infos"
    )

    #: The value of the context_id param this group was last launched with.
    context_id = sa.Column(sa.UnicodeText())

    #: The value of the context_title param this group was last launched with.
    context_title = sa.Column(sa.UnicodeText())

    #: The value of the context_label param this group was last launched with.
    context_label = sa.Column(sa.UnicodeText())

    #: The value of the tool_consumer_info_product_family_code param this group was last launched with.
    tool_consumer_info_product_family_code = sa.Column(sa.UnicodeText())

    #: The value of the tool_consumer_info_version param this group was last launched with.
    tool_consumer_info_version = sa.Column(sa.UnicodeText())

    #: The value of the tool_consumer_instance_name param this group was last launched with.
    tool_consumer_instance_name = sa.Column(sa.UnicodeText())

    #: The value of the tool_consumer_instance_description param this group was last launched with.
    tool_consumer_instance_description = sa.Column(sa.UnicodeText())

    #: The value of the tool_consumer_instance_url param this group was last launched with.
    tool_consumer_instance_url = sa.Column(sa.UnicodeText())

    #: The value of the tool_consumer_instance_contact_email param this group was last launched with.
    tool_consumer_instance_contact_email = sa.Column(sa.UnicodeText())

    #: The value of the tool_consumer_instance_guid param this group was last launched with.
    tool_consumer_instance_guid = sa.Column(sa.UnicodeText())

    #: The value of the custom_canvas_api_domain param this group was last launched with.
    custom_canvas_api_domain = sa.Column(sa.UnicodeText())

    #: The value of the custom_canvas_course_id param this group was last launched with.
    custom_canvas_course_id = sa.Column(sa.UnicodeText())

    #: A dict of info about this group.
    _info = sa.Column("info", MutableDict.as_mutable(JSONB))

    @property
    def _safe_info(self):
        if self._info is None:
            self._info = {}

        return self._info

    @property
    def instructors(self):
        return self._safe_info.get("instructors", [])

    @instructors.setter
    def instructors(self, new_instructors):
        self._safe_info["instructors"] = new_instructors

    @property
    def type(self):
        return self._safe_info.get("type", None)

    @type.setter
    def type(self, new_type):
        self._safe_info["type"] = new_type

    def upsert_instructor(self, new_instructor):
        updated_instructors = []
        found = False

        for existing_instructor in self.instructors:
            if existing_instructor["username"] == new_instructor["username"]:
                updated_instructors.append(new_instructor)
                found = True
            else:
                updated_instructors.append(existing_instructor)

        if not found:
            updated_instructors.append(new_instructor)

        if updated_instructors != self.instructors:
            self.instructors = updated_instructors
