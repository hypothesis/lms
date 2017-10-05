# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid.response import Response
from pyramid.renderers import render


# pylint: disable=too-many-arguments, too-many-locals
def web_response(request, oauth_consumer_key, lis_outcome_service_url,
                 lis_result_sourcedid, name, url):
    """
    Return an annotatable proxied copy of the given URL.

    The `url` argument is the URL to return. Pass this URL to Via and return
    Via's response (after some modification) as an HTML response.

    The HTTP request to Via is done synchronously in this function.

    Also cache the response from Via, with our own post-Via modifications,
    to the local disk. If the given URL has already been cached to disk
    previously then use the cached copy instead of requesting it from Via
    again.

    """
    html = render('lti:templates/html_assignment.html.jinja2', dict(
        name=name,
        url=request.registry.settings['via_url'] + '/' + url,
        oauth_consumer_key=oauth_consumer_key,
        lis_outcome_service_url=lis_outcome_service_url,
        lis_result_sourcedid=lis_result_sourcedid,
        lti_server=request.registry.settings['lti_server'],
    ))
    return Response(html.encode('utf-8'), content_type='text/html')
