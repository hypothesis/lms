import sqlalchemy as sa

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

    NON_METADATA_FIELDS = {"id", "authority_provided_id", "consumer_key"}

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

    def __str__(self):
        return self.__repr__(_class_name="GroupInfo")

    def __repr__(self, _class_name="lms.models.GroupInfo"):
        return (
            f"<{_class_name}"
            f" authority_provided_id:'{self.authority_provided_id}'"
            f" consumer_key:'{self.consumer_key}'>"
        )

    @classmethod
    def metadata_fields(cls):
        for column in cls.iter_columns():
            if column.key not in cls.NON_METADATA_FIELDS:
                yield column.key
