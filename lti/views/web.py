# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import md5
import os.path

import requests
from pyramid.response import Response
from pyramid.renderers import render

from lti import util


# pylint: disable=too-many-arguments, too-many-locals
def web_response(request, auth_data_svc, oauth_consumer_key=None, course=None,
                 lis_outcome_service_url=None, lis_result_sourcedid=None,
                 name=None, value=None, open_=None):
    """
    Return an annotatable proxied copy of the given URL.

    The `value` argument is the URL to return. Pass this URL to Via and return
    Via's response (after some modification) as an HTML response.

    The HTTP request to Via is done synchronously in this function.

    Also cache the response from Via, with our own post-Via modifications,
    to the local disk. If the given URL has already been cached to disk
    previously then use the cached copy instead of requesting it from Via
    again.

    """
    open_ = open_ or open  # Test seam.

    url = value

    canvas_server = auth_data_svc.get_canvas_server(oauth_consumer_key)

    # Create a fingerprint of the URL of the page to be annotated.
    # The fingerprint is Canvas instance- and course-specific.
    md5_obj = md5.new()
    md5_obj.update('%s/%s/%s' % (canvas_server, course, url))
    digest = md5_obj.hexdigest()

    if util.filecache.exists_html(digest, request.registry.settings) is False:
        # This URL isn't cached yet (for this Canvas instance and course),
        # so request the page from Via and cache it.
        via_response = requests.get('https://via.hypothes.is/%s' % url,
                                    headers={'User-Agent': 'Mozilla'})

        # Work around https://github.com/hypothesis/via/issues/76
        text = via_response.text.replace('return;', '// return')

        # ?
        text = text.replace("""src="/im_""", 'src="https://via.hypothes.is')

        cached_file = open_('%s/%s.html' % (request.registry.settings['lti_files_path'], digest), 'wb')
        cached_file.write(text.encode('utf-8'))
        cached_file.close()

    html = render('lti:templates/html_assignment.html.jinja2', dict(
        name=name,
        path=request.static_path(os.path.join(
            request.registry.settings['lti_files_path'], digest + '.html')),
        oauth_consumer_key=oauth_consumer_key,
        lis_outcome_service_url=lis_outcome_service_url,
        lis_result_sourcedid=lis_result_sourcedid,
        lti_server=request.registry.settings['lti_server'],
    ))
    return Response(html.encode('utf-8'), content_type='text/html')
