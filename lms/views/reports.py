from pyramid.view import view_config


@view_config(route_name='reports',
             renderer="lms:templates/reports/application_report.html.jinja2")
def list_application_instances(_):
    return {}
