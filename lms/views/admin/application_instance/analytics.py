from pyramid.view import view_config

from lms.security import Permissions
from lms.views.admin.application_instance._core import BaseApplicationInstanceView


class AnalyticsApplicationInstanceView(BaseApplicationInstanceView):
    @view_config(
        route_name="admin.instance.analytics",
        renderer="lms:templates/admin/application_instance/analytics.html.jinja2",
        permission=Permissions.STAFF,
        request_method="GET",
    )
    def show_instance(self):
        js_config = {"mode": "analytics"}
        return {"instance": self.application_instance, "jsConfig": js_config}
