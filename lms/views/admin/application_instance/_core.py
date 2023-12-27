from pyramid.httpexceptions import HTTPFound, HTTPNotFound

from lms.models import ApplicationInstance
from lms.services import ApplicationInstanceNotFound
from lms.services.application_instance import ApplicationInstanceService


class BaseApplicationInstanceView:
    def __init__(self, request) -> None:
        self.request = request
        self.application_instance_service: ApplicationInstanceService = (
            request.find_service(name="application_instance")
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
