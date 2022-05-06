from lms.resources.lti_launch.base import LTILaunchResource
from lms.services import ApplicationInstanceNotFound


class BlackboardLTILaunchResource(LTILaunchResource):
    @property
    def is_group_launch(self):
        """Return True if the current assignment uses Blackboard groups."""
        tool_consumer_instance_guid = self._request.parsed_params[
            "tool_consumer_instance_guid"
        ]
        assignment = self._assignment_service.get(
            tool_consumer_instance_guid, self.resource_link_id
        )
        return bool(assignment and assignment.extra.get("group_set_id"))

    @property
    def groups_enabled(self):
        """Return True if Blackboard groups are enabled at the school/installation level."""
        try:
            application_instance = self._application_instance_service.get_current()
        except ApplicationInstanceNotFound:
            return False

        return bool(application_instance.settings.get("blackboard", "groups_enabled"))

    def sync_api_config(self):
        if not self.is_group_launch:
            return None

        req = self._request
        return {
            "authUrl": req.route_url("blackboard_api.oauth.authorize"),
            "path": req.route_path("blackboard_api.sync"),
            "data": {
                "lms": {
                    "tool_consumer_instance_guid": req.params[
                        "tool_consumer_instance_guid"
                    ],
                },
                "course": {
                    "context_id": req.params["context_id"],
                },
                "assignment": {
                    "resource_link_id": req.params["resource_link_id"],
                },
                "group_info": {
                    key: value
                    for key, value in req.params.items()
                    if key in GroupInfo.columns()
                },
            },
        }
