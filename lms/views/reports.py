from pyramid.view import view_config

from lms.models.application_instance import ApplicationInstance
from lms.models.lti_launches import LtiLaunches


@view_config(route_name='reports',
             renderer="lms:templates/reports/application_report.html.jinja2",
             permission='view')
def list_application_instances(request):
    launches = request.db.execute("SELECT context_id, count(context_id), \
      lms_url, requesters_email, consumer_key FROM lti_launches LEFT JOIN \
      application_instances on \
      lti_launches.lti_key=application_instances.consumer_key GROUP BY \
      context_id, consumer_key, requesters_email, lms_url;").fetchall()
    return {
        'apps': request.db.query(ApplicationInstance).all(),
        'launches': launches,
        'num_launches': request.db.query(LtiLaunches).count(),
        'logout_url': request.route_url('logout')
    }
