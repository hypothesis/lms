from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.settings import asbool

from lms.models import ApplicationInstance
from lms.services import ApplicationInstanceNotFound

# Helper to declare settings as secret
AES_SECRET = object()
APPLICATION_INSTANCE_SETTINGS = {
    ("blackboard", "files_enabled"): asbool,
    ("blackboard", "groups_enabled"): asbool,
    ("canvas", "sections_enabled"): asbool,
    ("canvas", "groups_enabled"): asbool,
    ("desire2learn", "client_id"): str,
    ("desire2learn", "client_secret"): AES_SECRET,
    ("desire2learn", "groups_enabled"): asbool,
    ("desire2learn", "files_enabled"): asbool,
    ("desire2learn", "create_line_item"): asbool,
    ("microsoft_onedrive", "files_enabled"): asbool,
    ("vitalsource", "enabled"): asbool,
    ("vitalsource", "user_lti_param"): str,
    ("vitalsource", "user_lti_pattern"): str,
    ("vitalsource", "api_key"): str,
    ("vitalsource", "disable_licence_check"): asbool,
    ("jstor", "enabled"): asbool,
    ("jstor", "site_code"): str,
    ("hypothesis", "notes"): str,
}


class BaseApplicationInstanceView:
    def __init__(self, request):
        self.request = request
        self.application_instance_service = request.find_service(
            name="application_instance"
        )

    @property
    def application_instance(self) -> ApplicationInstance:
        """
        Get the current application instance from the route by id.

        :raises HTTPNotFound: If the application instance cannot be found.
        """
        try:
            return self.application_instance_service.get_by_id(
                id_=self.request.matchdict["id_"]
            )

        except ApplicationInstanceNotFound as err:
            raise HTTPNotFound() from err

    def _redirect(self, route_name, **kwargs):
        return HTTPFound(location=self.request.route_url(route_name, **kwargs))
