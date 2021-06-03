"""Proxy API views for files-related Blackboard API endpoints."""
from pyramid.view import view_config, view_defaults

from lms.security import Permissions
from lms.services import NoOAuth2Token, OAuth2TokenService, ProxyAPIAccessTokenError
from lms.views import helpers


@view_defaults(permission=Permissions.API, renderer="json")
class BlackboardFilesAPIViews:
    def __init__(self, request):
        self.request = request

    @view_config(request_method="GET", route_name="blackboard_api.courses.files.list")
    def list_files(self):
        """Return the list of files in the given course."""
        # Get the user's access token from the DB.
        # We're not actually going to *use* the access token, since this view
        # just returns a list of hard-coded files. But we want to *get* the
        # access token so that we can raise an exception if it's missing and
        # trigger the authentication flow.
        try:
            self.request.find_service(OAuth2TokenService).get()
        except NoOAuth2Token as err:
            raise ProxyAPIAccessTokenError() from err

        # Return a temporary hard-coded list of files.
        return [
            {
                "id": "blackboard://content-resource/123",
                "display_name": "Fake Blackboard File 1",
                "updated_at": "2020-06-10T16:49:19Z",
            },
            {
                "id": "blackboard://content-resource/456",
                "display_name": "Fake Blackboard File 2",
                "updated_at": "2020-06-10T16:48:53Z",
            },
            {
                "id": "blackboard://content-resource/789",
                "display_name": "Fake Blackboard File 3",
                "updated_at": "2020-08-03T14:06:00Z",
            },
        ]

    @view_config(request_method="GET", route_name="blackboard_api.files.via_url")
    def via_url(self):
        """Return the Via URL for annotating the given Blackboard file."""
        # Get the user's access token from the DB.
        # We're not actually going to *use* the access token, since this view
        # just returns hard-coded URLs. But we want to *get* the access token
        # so that we can raise an exception if it's missing and trigger the
        # authentication flow.
        try:
            self.request.find_service(OAuth2TokenService).get()
        except NoOAuth2Token as err:
            raise ProxyAPIAccessTokenError() from err

        # Look up the file_id in a temporary hard-coded list of public URLs.
        public_url = {
            "123": "https://h.readthedocs.io/_/downloads/en/latest/pdf/",
            "456": "https://h.readthedocs.io/_/downloads/client/en/latest/pdf/",
            "789": "https://packaging.python.org/_/downloads/en/latest/pdf/",
        }[self.request.matchdict["file_id"]]

        return {
            "via_url": helpers.via_url(self.request, public_url, content_type="pdf"),
        }
