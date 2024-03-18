"""A service for managing `GroupInfo` records."""

from lms.models import GroupInfo, Grouping


class GroupInfoService:
    """A service for managing `GroupInfo` records."""

    def __init__(self, _context, request):
        self._db = request.db
        self._lti_user = request.lti_user

    _GROUPING_TYPES = {
        "course": "course_group",
        "canvas_section": "section_group",
        "canvas_group": "canvas_group_group",
        "blackboard_group": "blackboard_group_group",
        "d2l_group": "d2l_group_group",
        "moodle_group": "moodle_group_group",
    }

    def upsert_group_info(self, grouping: Grouping, params: dict):
        """
        Upsert a row into the `group_info` DB table.

        :param grouping: grouping to upsert based on
        :param params: columns to set on the row ("authority_provided_id",
            "id", "info" and any non-matching items will be ignored)
        """
        group_info = (
            self._db.query(GroupInfo)
            .filter_by(authority_provided_id=grouping.authority_provided_id)
            .one_or_none()
        )

        if not group_info:
            group_info = GroupInfo(
                authority_provided_id=grouping.authority_provided_id,
                application_instance=grouping.application_instance,
            )
            self._db.add(group_info)

        # This is very strange. The DB layout is wrong here. You can "steal" a
        # group info row from another application instance by updating it with
        # a grouping from another AI. This is wrong in because grouping to
        # AI should be many:many, and we reflect that wrongness here.
        group_info.application_instance = grouping.application_instance

        group_info.type = self._GROUPING_TYPES[grouping.type]  # type: ignore

        for field in [
            # Most (all) of these are duplicated elsewhere, we'll keep updating for now
            # because external analytics query rely on this table.
            "context_id",
            "context_title",
            "context_label",
            "tool_consumer_info_product_family_code",
            "tool_consumer_info_version",
            "tool_consumer_instance_name",
            "tool_consumer_instance_description",
            "tool_consumer_instance_url",
            "tool_consumer_instance_contact_email",
            "tool_consumer_instance_guid",
            "custom_canvas_api_domain",
            "custom_canvas_course_id",
        ]:
            if field in params:
                setattr(group_info, field, params[field])

        if self._lti_user.is_instructor:
            group_info.upsert_instructor(
                {"email": self._lti_user.email, **self._lti_user.h_user._asdict()}
            )
