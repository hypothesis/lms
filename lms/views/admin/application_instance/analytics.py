from pyramid.view import view_config

from lms.views.admin.application_instance._core import BaseApplicationInstanceView


class AssignmentAnalyticsView(BaseApplicationInstanceView):
    @view_config(
        route_name="analytics.assignment",
        renderer="lms:templates/analytics/application_instance.html.jinja2",
        request_method="GET",
    )
    def show_analitycs(self):
        js_config = {
            "mode": "analytics",
        }

        return {"jsConfig": js_config}
