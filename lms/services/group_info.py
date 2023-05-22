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
    }

    def upsert_group_info(
        self, grouping: Grouping, context_id, context_title, context_label
    ):
        """
        Upsert a row into the `group_info` DB table.

        :param grouping: grouping to upsert based on
        :param context_id: context_id of of the grouping or parent grouping.
        :param context_title: context_id of of the grouping or parent grouping.
        :param context_label: context_label of of the grouping or parent grouping.
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
        ai = grouping.application_instance
        group_info.application_instance = ai

        # GroupingInfo duplicates lots of info from the AI
        group_info.consumer_key = ai.consumer_key
        group_info.tool_consumer_info_product_family_code = (
            ai.tool_consumer_info_product_family_code
        )
        group_info.tool_consumer_info_version = ai.tool_consumer_info_version
        group_info.tool_consumer_instance_name = ai.tool_consumer_instance_name
        group_info.tool_consumer_instance_description = (
            ai.tool_consumer_instance_description
        )
        group_info.tool_consumer_instance_url = ai.tool_consumer_instance_url
        group_info.tool_consumer_instance_contact_email = (
            ai.tool_consumer_instance_contact_email
        )
        group_info.tool_consumer_instance_guid = ai.tool_consumer_instance_guid
        group_info.custom_canvas_api_domain = ai.custom_canvas_api_domain

        group_info.type = self._GROUPING_TYPES[grouping.type]

        # GroupInfo always has info about the context, even if it's representing a sectoin or group
        group_info.context_id = context_id
        group_info.context_title = context_title
        group_info.context_label = context_label

        if self._lti_user.is_instructor:
            group_info.upsert_instructor(
                {"email": self._lti_user.email, **self._lti_user.h_user._asdict()}
            )
