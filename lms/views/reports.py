from pyramid.view import view_config
from lms.models.application_instance import ApplicationInstance
from pyramid.httpexceptions import HTTPFound
from pyramid.security import remember, forget

from pyramid.view import view_config, view_defaults, forbidden_view_config
from lms.security import USERS, check_password

# TODO: add authentication
@view_config(route_name='reports',
             renderer="lms:templates/reports/application_report.html.jinja2",
             permission='view')
def list_application_instances(request):
    return {
        'apps': request.db.query(ApplicationInstance).all(),
        'logout_url': request.route_url('logout')
    }
