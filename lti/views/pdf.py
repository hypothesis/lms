# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import md5
import urllib
import os
import json

import requests
from pyramid.renderers import render
from pyramid.response import Response

from lti import util
from lti.views import oauth
from lti import constants


def lti_pdf(request, oauth_consumer_key, lis_outcome_service_url,
            lis_result_sourcedid, course, name, value):
    """ 
    Called from lti_setup if it was called from a pdf assignment. 

    We expect to know at least the oauth_consume_key, course number, name of the PDF, 
    and value of the PDF (its number as known to the Canvas API)

    If we are called in a student context we also expect the lis* params needed for the submission URL.

    Download the PDF to a timestamp-based name in the PDFJS subtree, and call pdf_response to 
    return a page that serves it back in an iframe.
    """
    post_data = util.requests.capture_post_data(request)
    file_id = value
    try:
        lti_token = request.auth_data.get_lti_token(oauth_consumer_key)
    except:
        return util.simple_response("We don't have the Consumer Key %s in our database yet." % oauth_consumer_key)
    canvas_server = request.auth_data.get_canvas_server(oauth_consumer_key)
    url = '%s/api/v1/courses/%s/files/%s' % (canvas_server, course, file_id)
    m = md5.new()
    m.update('%s/%s/%s' % ( canvas_server, course, file_id ))
    hash = m.hexdigest()
    if util.filecache.exists_pdf(hash) is False:
        sess = requests.Session()
        r = sess.get(url=url, headers={'Authorization':'Bearer %s' % lti_token})
        if r.status_code == 401:
          return oauth.make_authorization_request(
                request, 'pdf:' + urllib.quote(json.dumps(post_data)),
                refresh=True)
        if r.status_code == 200:
            j = r.json()
            url = j['url']
            urllib.urlretrieve(url, hash)
            os.rename(hash, '%s/%s.pdf' % (constants.FILES_PATH, hash))
    fingerprint = util.pdf.get_fingerprint(hash)
    if fingerprint is None:
        pdf_uri = '%s/viewer/web/%s.pdf' % ( request.registry.settings['lti_server'], hash )
    else:
        pdf_uri = 'urn:x-pdf:%s' % fingerprint

    return Response(
        render('lti:templates/pdf_assignment.html.jinja2', dict(
                name=name,
                hash=hash,
                oauth_consumer_key=oauth_consumer_key,
                lis_outcome_service_url=lis_outcome_service_url,
                lis_result_sourcedid=lis_result_sourcedid,
                doc_uri=pdf_uri,
                lti_server=request.registry.settings['lti_server'],
            ),
        ).encode('utf-8'),
        content_type='text/html',
    )

