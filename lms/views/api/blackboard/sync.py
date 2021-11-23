from pyramid.view import view_config

from lms.security import Permissions


class Sync:
    def __init__(self, request):
        self._request = request

    @view_config(
        route_name="blackboard_api.sync",
        request_method="POST",
        renderer="json",
        permission=Permissions.API,
    )  # pylint: disable=no-self-use
    def sync(self):
        return []
