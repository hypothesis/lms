from pyramid.view import view_config

from lms.models.application_instance import ApplicationInstance
from lms.models.lti_launches import LtiLaunches


@view_config(route_name='reports',
             renderer="lms:templates/reports/application_report.html.jinja2",
             permission='view')
def list_application_instances(request):
    return {
        'apps': request.db.query(ApplicationInstance).all(),
        'launches': request.db.query(LtiLaunches).all(),
        'logout_url': request.route_url('logout')
    }
