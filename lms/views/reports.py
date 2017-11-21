from pyramid.view import view_config
from lms.models.application_instance import ApplicationInstance


# TODO: add authentication
@view_config(route_name='reports',
             renderer="lms:templates/reports/application_report.html.jinja2")
def list_application_instances(request):
    # TODO: Is it a security issue that this dictionary has the secret in it?
    # Maybe better to create a new dict, leaving out secret.
    return {
        'apps': request.db.query(ApplicationInstance).all()
    }
