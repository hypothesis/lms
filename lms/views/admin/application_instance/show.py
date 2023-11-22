from pyramid.view import view_config

from lms.security import Permissions
from lms.views.admin.application_instance._core import BaseApplicationInstanceView


class ShowApplicationInstanceView(BaseApplicationInstanceView):
    @view_config(
        route_name="admin.instance",
        renderer="lms:templates/admin/application_instance/show.html.jinja2",
        permission=Permissions.STAFF,
        request_method="GET",
    )
    def show_instance(self):
        return {"instance": self.application_instance}
