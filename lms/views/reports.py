from pyramid.view import view_config
from lms.models.application_instance import ApplicationInstance


# TODO: add authentication
@view_config(route_name='reports',
             renderer="lms:templates/reports/application_report.html.jinja2",
             permission='viewer')
def list_application_instances(request):
    return {
        'apps': request.db.query(ApplicationInstance).all()
    }
