# -*- coding: utf-8 -*-

import urllib
import urlparse

from pyramid.view import view_config

from pyramid.httpexceptions import HTTPFound

from lti import util


@view_config(route_name='lti_export')
def lti_export(request):
    """
    Call from Speed Grader, which presents the URL that the student submitted.

    Redirects to a variant of our viewer/export prototype which displays annotations for the
    assignment's PDF or URL, filtered to threads involving the (self-identified) H user, and
    highlighting contributions by that user.
    """
    args = util.requests.get_query_param(request, 'args')  # because canvas swallows & in the submitted pox, we pass an opaque construct and unpack here
    parsed_args = urlparse.parse_qs(args)
    user = parsed_args['user'][0]
    uri = parsed_args['uri'][0]
    export_url = '%s/export/facet.html?facet=uri&mode=documents&search=%s&user=%s' % (request.registry.settings['lti_server'], urllib.quote(uri), user)
    return HTTPFound(location=export_url)
