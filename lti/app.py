import requests
import logging
from pyramid.view import view_config
from requests_oauthlib import OAuth1

from pyramid.renderers import render

from lti.config import configure
from lti import util
from lti import constants


log = logging.getLogger(__name__)


@view_config( route_name='lti_submit' )
def lti_submit(request, oauth_consumer_key=None, lis_outcome_service_url=None, lis_result_sourcedid=None, export_url=None):
    """
    Called from a student's view of an assignment.

    In theory can be an LTI launch but that's undocumented and did not seem to work. 
    So we use info we send to ourselves from the JS we generate on the assignment page.
    """
    auth_data_svc = request.find_service(name='auth_data')


    log.info ( 'lti_submit: query: %s' % request.query_string )
    log.info ( 'lti_submit: post: %s' % request.POST )
    oauth_consumer_key = util.requests.get_post_or_query_param(request, constants.OAUTH_CONSUMER_KEY)
    lis_outcome_service_url = util.requests.get_post_or_query_param(request, constants.LIS_OUTCOME_SERVICE_URL)
    lis_result_sourcedid = util.requests.get_post_or_query_param(request, constants.LIS_RESULT_SOURCEDID)
    export_url = util.requests.get_post_or_query_param(request, constants.EXPORT_URL)

    try:
        secret = auth_data_svc.get_lti_secret(oauth_consumer_key)   # because the submission must be OAuth1-signed
    except:
        return util.simple_response("We don't have the Consumer Key %s in our database yet." % oauth_consumer_key)

    oauth_client = OAuth1(client_key=oauth_consumer_key, client_secret=secret, signature_method='HMAC-SHA1', signature_type='auth_header', force_include_body=True)
    body = render('lti:templates/submission.xml.jinja2', dict(
        url=export_url,
        sourcedid=lis_result_sourcedid,
    ))
    headers = {'Content-Type': 'application/xml'}
    r = requests.post(url=lis_outcome_service_url, data=body, headers=headers, auth=oauth_client)
    log.info ( 'lti_submit: %s' % r.status_code )
    log.info ( 'lti_submit: %s' % r.text )
    response = None
    if ( r.status_code == 200 ):
        response = 'OK! Assignment successfully submitted.'
    else:
        response = 'Something is wrong. %s %s' % (r.status_code, r.text)        
    return util.simple_response(response)


def create_app(global_config, **settings):  # pylint: disable=unused-argument
    config = configure(settings=settings)

    config.include('pyramid_jinja2')
    config.include('pyramid_services')
    config.include('pyramid_tm')

    config.include('lti.sentry')
    config.include('lti.models')
    config.include('lti.db')
    config.include('lti.routes')
    config.include('lti.services')

    config.add_static_view(name='export', path='lti:static/export')

    config.add_static_view(name='static', path='lti:static')

    config.add_static_view(name='cache', path=config.registry.settings['lti_files_path'])

    config.registry.settings['jinja2.filters'] = {
        'static_path': 'pyramid_jinja2.filters:static_path_filter',
        'static_url': 'pyramid_jinja2.filters:static_url_filter',
    }

    config.scan()

    return config.make_wsgi_app()
