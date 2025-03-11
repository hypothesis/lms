from pyramid.view import view_config, view_defaults

from lms.security import Permissions
from lms.views.admin.application_instance._core import BaseApplicationInstanceView


@view_defaults(
    renderer="lms:templates/admin/application_instance/show.html.jinja2",
    permission=Permissions.STAFF,
    request_method="GET",
)
class ShowApplicationInstanceView(BaseApplicationInstanceView):
    @view_config(route_name="admin.instance")
    @view_config(route_name="admin.instance.section")
    def show_instance(self):
        return {
            "instance": self.application_instance,
            "Settings": self.application_instance.settings.Settings,
            "fields": self.application_instance.settings.fields,
        }
