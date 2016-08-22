import json
import urllib
import urlparse
import requests
import traceback
import pyramid
import sys
import time
import os
import re
import logging
from pyramid.httpexceptions import HTTPFound
from requests_oauthlib import OAuth1

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='lti.log',level=logging.DEBUG
                    )
logger = logging.getLogger('')
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
logger.addHandler(console)

# lti local testing

lti_server_host_internal = '10.0.0.9'  # for local testing
lti_server_port_internal = 8000

# lti server

#lti_server_scheme = 'https'
#lti_server_host = 'lti.hypothesislabs.com'
#lti_server_port = None

lti_server_scheme = 'http'
lti_server_host = '98.234.245.185'
lti_server_port = 8000

if lti_server_port is None:
    lti_server = '%s://%s' % (lti_server_scheme, lti_server_host)
else:
    lti_server = '%s://%s:%s' % (lti_server_scheme, lti_server_host, lti_server_port)

logger.info( 'lti_server: %s' % lti_server )

lti_keys = ['context_title', 'custom_canvas_assignment_id', 'custom_canvas_assignment_title', 'custom_canvas_user_login_id', 'user_id']

CUSTOM_CANVAS_COURSE_ID = 'custom_canvas_course_id'
CUSTOM_CANVAS_USER_ID = 'custom_canvas_user_id'
CUSTOM_CANVAS_ASSIGNMENT_ID = 'custom_canvas_assignment_id'
OAUTH_CONSUMER_KEY = 'oauth_consumer_key'
EXT_CONTENT_RETURN_TYPES = 'ext_content_return_types'
EXT_CONTENT_RETURN_URL = 'ext_content_return_url'
LIS_OUTCOME_SERVICE_URL = 'lis_outcome_service_url'
LIS_RESULT_SOURCEDID = 'lis_result_sourcedid'
EXPORT_URL = 'export_url'

lti_setup_url = '%s/lti_setup' % lti_server
lti_pdf_url = '%s/lti_pdf' % lti_server
lti_web_url = '%s/lti_web' % lti_server
lti_submit_url = '%s/lti_submit' % lti_server
lti_export_url = '%s/lti_export' % lti_server

submission_template = """
<?xml version = "1.0" encoding = "UTF-8"?>
<imsx_POXEnvelopeRequest xmlns="http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0">
  <imsx_POXHeader>
    <imsx_POXRequestHeaderInfo>
      <imsx_version>V1.0</imsx_version>
      <imsx_messageIdentifier>999999123</imsx_messageIdentifier>
    </imsx_POXRequestHeaderInfo>
  </imsx_POXHeader>
  <imsx_POXBody>
    <replaceResultRequest>
      <resultRecord>
        <sourcedGUID>
          <sourcedId>__SOURCEDID__</sourcedId>
        </sourcedGUID>
        <result>
          <resultScore>
            <language>en</language>
            <textString>1</textString>
          </resultScore>
          <resultData>
            <url>__URL__</url>
          </resultData>
        </result>
      </resultRecord>
    </replaceResultRequest>
  </imsx_POXBody>
</imsx_POXEnvelopeRequest
"""

boilerplate = """<p>
This document is annotatable using <a href="https://hypothes.is">Hypothes.is</a>. 
You can click highlighted text or expand the sidebar to view existing annotations. 
You'll need to register for (or log in to) an account in order to create annotations; 
you can do so in the Hypothesis sidebar.</p>"""

class AuthData(): # was hoping to avoid but per-assignment integration data in canvas requires elevated privilege
    def __init__(self):
        self.name = 'canvas-auth.json'
        self.auth_data = {}
        self.load()

    def set_tokens(self, oauth_consumer_key, lti_token, lti_refresh_token):
        assert (self.auth_data.has_key(oauth_consumer_key))
        self.auth_data[oauth_consumer_key]['lti_token'] = lti_token
        self.auth_data[oauth_consumer_key]['lti_refresh_token'] = lti_refresh_token
        self.save()

    def get_lti_token(self, oauth_consumer_key):
        return self.auth_data[oauth_consumer_key]['lti_token']

    def get_lti_refresh_token(self, oauth_consumer_key):
        return self.auth_data[oauth_consumer_key]['lti_refresh_token']

    def get_lti_secret(self, oauth_consumer_key):
        return self.auth_data[oauth_consumer_key]['secret']

    def get_canvas_server_scheme(self, oauth_consumer_key):
        return self.auth_data[oauth_consumer_key]['canvas_server_scheme']

    def get_canvas_server_host(self, oauth_consumer_key):
        return self.auth_data[oauth_consumer_key]['canvas_server_host']

    def get_canvas_server_port(self, oauth_consumer_key):
        return self.auth_data[oauth_consumer_key]['canvas_server_port']

    def get_canvas_server(self, oauth_consumer_key):
        canvas_server_scheme = self.get_canvas_server_scheme(oauth_consumer_key)
        canvas_server_host = self.get_canvas_server_host(oauth_consumer_key)
        canvas_server_port = self.get_canvas_server_port(oauth_consumer_key)
        canvas_server = None
        if canvas_server_port is None:
            canvas_server = '%s://%s' % (canvas_server_scheme, canvas_server_host)
        else:
            canvas_server = '%s://%s:%s' % (canvas_server_scheme, canvas_server_host, canvas_server_port)
        return canvas_server

    def load(self):
        f = open(self.name)
        self.auth_data = json.loads(f.read())
        f.close()

    def save(self):
        f = open(self.name, 'wb')
        j = json.dumps(self.auth_data, indent=2, sort_keys=True)
        f.write(j)
        f.close()  

auth_data = AuthData()

def get_pdf_fingerprint(fname):
    f = open(fname, 'rb')
    s = f.read()
    m = re.findall('ID\s*\[\s*<(\w+)>',s)
    f.close()
    if len(m) > 0:
        return m[0]
    else:
        return 'no pdf fingerprint'

def make_submit_url(oauth_consumer_key=None, lis_outcome_service_url=None, lis_result_sourcedid=None, export_url=None):
    submit_url = '/lti_submit?oauth_consumer_key=%s&lis_outcome_service_url=%s&lis_result_sourcedid=%s&export_url=%s' % ( 
        oauth_consumer_key,  
        lis_outcome_service_url,  
        lis_result_sourcedid,
        export_url)
    return submit_url

def get_config_value(client_id, key):
    if canvas_config.has_key(client_id):
        return canvas_config[client_id][key]
    else:
        logger.warning( 'no config value for ' + key )
        return None

def show_exception():
    logger.exception ( traceback.print_exc() )

def unpack_state(state):
    s = state.replace('setup:','').replace('web:','').replace('pdf:','').replace('submit:','')
    j = json.loads(urllib.unquote(s))
    return j

def redirect_helper(state, course=None, user=None, oauth_consumer_key=None, ext_content_return_url=None, lis_outcome_service_url=None, lis_result_sourcedid=None):
    if state.startswith('setup'):
        redirect = lti_setup_url + '?%s=%s&%s=%s&%s=%s&%s=%s' % (CUSTOM_CANVAS_COURSE_ID, course, CUSTOM_CANVAS_USER_ID, user, OAUTH_CONSUMER_KEY, oauth_consumer_key, EXT_CONTENT_RETURN_URL, ext_content_return_url)
    elif state.startswith('pdf'):
        redirect = lti_pdf_url   + '?%s=%s&%s=%s&%s=%s' % (CUSTOM_CANVAS_COURSE_ID, course, CUSTOM_CANVAS_USER_ID, user, OAUTH_CONSUMER_KEY, oauth_consumer_key)
    elif state.startswith('web'):
        redirect = lti_web_url   + '?%s=%s&%s=%s&%s=%s' % (CUSTOM_CANVAS_COURSE_ID, course, CUSTOM_CANVAS_USER_ID, user, OAUTH_CONSUMER_KEY, oauth_consumer_key)
    elif state.startswith('submit'):
        redirect = lti_submit_url   + '?%s=%s&%s=%s&%s=%s' % (OAUTH_CONSUMER_KEY, oauth_consumer_key, LIS_OUTCOME_SERVICE_URL, lis_outcome_service_url, LIS_RESULT_SOURCEDID, lis_result_sourcedid)
    else:
        redirect = 'unexpected state'
    return redirect

def token_init(request, state=None):
    j = unpack_state(state)
    logger.info( j )
    oauth_consumer_key = j[OAUTH_CONSUMER_KEY]
    canvas_server = auth_data.get_canvas_server(oauth_consumer_key)
    token_redirect_uri = '%s/login/oauth2/auth?client_id=%s&response_type=code&redirect_uri=%s/token_callback&state=%s' % (canvas_server, oauth_consumer_key, lti_server, state)
    ret = HTTPFound(location=token_redirect_uri)
    logger.info( 'token_init ' + token_redirect_uri )
    return ret

def oauth_callback(request, type=None):
    q = urlparse.parse_qs(request.query_string)
    code = q['code'][0]
    state = q['state'][0]
    j = unpack_state(state)
    course = j[CUSTOM_CANVAS_COURSE_ID]
    user = j[CUSTOM_CANVAS_USER_ID]
    oauth_consumer_key = j[OAUTH_CONSUMER_KEY]
    ext_content_return_url = j[EXT_CONTENT_RETURN_URL]
    lis_outcome_service_url = j[LIS_OUTCOME_SERVICE_URL]
    lis_result_sourcedid = j[LIS_RESULT_SOURCEDID]
    canvas_client_secret = auth_data.get_lti_secret(oauth_consumer_key)
    lti_refresh_token = auth_data.get_lti_refresh_token(oauth_consumer_key)
    canvas_server = auth_data.get_canvas_server(oauth_consumer_key)
    url = '%s/login/oauth2/token' % canvas_server
    grant_type = 'authorization_code' if type == 'token' else 'refresh_token'
    params = { 
            'grant_type': grant_type,
            'client_id': oauth_consumer_key,
            'client_secret': canvas_client_secret,
            'redirect_uri': '%s/token_init' % lti_server
            }
    if grant_type == 'authorization_code': 
        params['code'] = code
    else:
        params['refresh_token'] = lti_refresh_token
    r = requests.post(url, params)
    j = r.json()
    lti_token = j['access_token']
    if j.has_key('refresh_token'):
        lti_refresh_token = j['refresh_token']
    auth_data.set_tokens(oauth_consumer_key, lti_token, lti_refresh_token)
    redirect = redirect_helper(state, course=course, user=user, oauth_consumer_key=oauth_consumer_key, ext_content_return_url=ext_content_return_url, lis_outcome_service_url=lis_outcome_service_url, lis_result_sourcedid=lis_result_sourcedid)
    return HTTPFound(location=redirect)

def token_callback(request):
    return oauth_callback(request, type='token')

def refresh_callback(request):
    return oauth_callback(request, type='refresh')

def refresh_init(request, state=None):
    j = unpack_state(state)
    oauth_consumer_key = j[OAUTH_CONSUMER_KEY]
    canvas_server = auth_data.get_canvas_server(oauth_consumer_key)
    token_redirect_uri = '%s/login/oauth2/auth?client_id=%s&response_type=code&redirect_uri=%s/refresh_callback&state=%s' % (canvas_server, oauth_consumer_key, lti_server, state)
    ret = HTTPFound(location=token_redirect_uri)
    return ret

def simple_response(exc_str):
    template = """
 <html>
 <head> <style> body { font-family:verdana; margin:.5in; } </style> </head>
 <body>%s</body>
 </html>"""
    html = template % exc_str
    r = Response(html.encode('utf-8'))
    r.content_type = 'text/html'
    return r

def config_xml(request):
    with open('config.xml') as f:
        xml = f.read()
        logger.info( 'config request' )
        r = Response(xml)
        r.content_type = 'text/xml'
        return r

def about(request):
    with open('about.html') as f:
        html = f.read()
        logger.info( 'about request' )
        r = Response(html)
        r.content_type = 'text/html'                  
        return r

def pdf_response(oauth_consumer_key=None, lis_outcome_service_url=None, lis_result_sourcedid=None, name=None, fname=None, export_url=None):
    logger.info( 'pdf_response: %s, %s, %s, %s, %s, %s' % (oauth_consumer_key, lis_outcome_service_url, lis_result_sourcedid, name, fname, export_url) )
    template = """
 <html> 
 <head> <style> body { font-family:verdana; margin:.5in; } </style> </head>
 <body>
%s
<p>When you're done annotating <i>%s</i>, click <input type="button" value="Submit Assignment" onclick="javascript:location.href='%s'"></p>
 <iframe width="100%%" height="1000px" src="/viewer/web/viewer.html?file=%s"></iframe>
 </body>
 </html>
""" 
                  
    submit_url = make_submit_url (
        oauth_consumer_key=oauth_consumer_key, 
        lis_outcome_service_url=lis_outcome_service_url, 
        lis_result_sourcedid=lis_result_sourcedid, 
        export_url=export_url
        )

    html = template % (boilerplate, name, submit_url, fname)
    r = Response(html.encode('utf-8'))
    r.content_type = 'text/html'
    return r

def capture_post_data(request):
    ret = {}
    for key in [
            OAUTH_CONSUMER_KEY,
            CUSTOM_CANVAS_USER_ID,
            CUSTOM_CANVAS_COURSE_ID,
            CUSTOM_CANVAS_ASSIGNMENT_ID,
            EXT_CONTENT_RETURN_TYPES,
            EXT_CONTENT_RETURN_URL,
            LIS_OUTCOME_SERVICE_URL,
            LIS_RESULT_SOURCEDID
            ]:
        if key in request.POST.keys():
            ret[key] = request.POST[key]
        else:
            ret[key] = None
    return ret

def get_post_or_query_param(request, key):
    value = get_query_param(request, key)
    if value is not None:
        ret = value
    else:
        value = get_post_param(request, key)
        ret = value
    if ret is None:
        logger.warning( 'no post or query param for %s' % key )
        if key == CUSTOM_CANVAS_COURSE_ID:
            logger.warning ( 'is privacy set to public in courses/COURSE_NUM/settings/configurations?' )
    return ret

def get_query_param(request, key):
    q = urlparse.parse_qs(request.query_string)
    if q.has_key(key):
      return q[key][0]
    else:
      return None

def get_post_param(request, key):
    post_data = capture_post_data(request)
    if post_data.has_key(key):
        return post_data[key]
    else:
        return None

def lti_setup(request):
    post_data = capture_post_data(request)
    oauth_consumer_key = get_post_or_query_param(request, OAUTH_CONSUMER_KEY)
    lis_outcome_service_url = get_post_or_query_param(request, LIS_OUTCOME_SERVICE_URL)
    lis_result_sourcedid = get_post_or_query_param(request, LIS_RESULT_SOURCEDID)
    
    lti_token = auth_data.get_lti_token(oauth_consumer_key)
    if lti_token is None:
      return token_init(request, 'setup:' + urllib.quote(json.dumps(post_data)))

    #return HTTPFound(location='http://h.jonudell.info:3000/courses/2/external_content/success/external_tool_dialog?return_type=lti_launch_url&url=http%3A%2F%2F98.234.245.185%3A8000%2Flti_setup%3FCUSTOM_CANVAS_COURSE_ID%3D2%26type%3Dpdf%26name%3Dfilename%26value%3D9')

    course = get_post_or_query_param(request, CUSTOM_CANVAS_COURSE_ID)
    if course is None:
        return simple_response('No course number. Was Privacy set to Public for this installation of the Hypothesis LTI app? If not please do so (or ask someone who can to do so).')

    type = get_post_or_query_param(request, 'type')
    name = get_post_or_query_param(request, 'name')
    value = get_post_or_query_param(request, 'value')
    
    if type == 'pdf':
        return lti_pdf(request, oauth_consumer_key=oauth_consumer_key, lis_outcome_service_url=lis_outcome_service_url, lis_result_sourcedid=lis_result_sourcedid, course=course, name=name, value=value)

    if type == 'web':
        return lti_web(request, oauth_consumer_key=oauth_consumer_key, lis_outcome_service_url=lis_outcome_service_url, lis_result_sourcedid=lis_result_sourcedid, course=course, name=name, value=value)

    return_url = get_post_or_query_param(request, EXT_CONTENT_RETURN_URL)
    if return_url is None: # this is an oauth redirect so get what we sent ourselves
        return_url = get_post_or_query_param(request, 'return_url')

    logger.info ( 'return_url: %s' % return_url )

    launch_url_template = '%s/lti_setup?type=__TYPE__&name=__NAME__&value=__VALUE__&return_url=__RETURN_URL__' % lti_server

    sess = requests.Session()  # do this first to ensure we have a token
    canvas_server = auth_data.get_canvas_server(oauth_consumer_key)
    logger.info ( 'canvas_server: %s' % canvas_server )

    url = '%s/api/v1/courses/%s/files?per_page=100' % (canvas_server, course)
    r = sess.get(url=url, headers={'Authorization':'Bearer %s' % lti_token })
    if r.status_code == 401:
      logger.info ( 'lti_setup: refreshing token' )
      return refresh_init(request, 'setup:' + urllib.quote(json.dumps(post_data)))
    files = r.json()

    logger.info ( 'key %s, course %s, token %s' % (oauth_consumer_key, course, lti_token) )

    template = """
<html><head> 
<style> 
body { font-family:verdana; margin:.5in; font-size:smaller } 
p { font-weight: bold }
ul { list-style-type: none; padding: 0 }
li { margin: 4px 0 }
#pdf_select, #web_select { display: none }
</style> 
<script>
var checked_boxes;

function getRVBN(rName) {
    var radioButtons = document.getElementsByName(rName);
    for (var i = 0; i < radioButtons.length; i++) {
        if (radioButtons[i].checked)
            return radioButtons[i];
    }
    return '';
}

function show() {
  var type = getRVBN('format').value;
  if ( type=='pdf' ) {
    document.getElementById('pdf_select').style.display = 'block';
    document.getElementById('web_select').style.display = 'none';
    }
  if ( type=='web' ) {
    document.getElementById('web_select').style.display = 'block';
    document.getElementById('pdf_select').style.display = 'none';
    }
  }

function go() {
    var return_url = '%s';
    var launch_url = '%s';
    var redirect_url;
    var type = getRVBN('format').value;

    if ( type == 'pdf' ) {
      var pdf_choice = getRVBN('pdf_choice');
      launch_url = launch_url.replace('__TYPE__',  'pdf');
      launch_url = launch_url.replace('__NAME__',  encodeURIComponent(pdf_choice.value));
      launch_url = launch_url.replace('__VALUE__', pdf_choice.id);
      redirect_url = return_url + '?return_type=lti_launch_url&url=' + encodeURIComponent(launch_url);
      }

    if ( type == 'web' ) {
      var url = document.getElementById('web_url').value;
      launch_url = launch_url.replace('__TYPE__',  'web');
      launch_url = launch_url.replace('__NAME__',  url);
      launch_url = launch_url.replace('__VALUE__', url);
      launch_url = launch_url.replace('__RETURN_URL__', return_url);
      redirect_url = return_url + '?return_type=lti_launch_url&url=' + encodeURIComponent(launch_url);
      }

  window.location.href = redirect_url;
  }
</script>
</head>
<body>
<p>
I want students to annotate:
<div>
<input onchange="javascript:show()" id="pdf_choice" type="radio" name="format" value="pdf"> A PDF file
<input onchange="javascript:show()" id="web_choice" type="radio" name="format" value="web"> A web page
</div>
</p>

<div id="pdf_select">
<p<Select a PDF from the Canvas Files in this course</p>
%s 
</div>
<div id="web_select">
<p>Enter a URL</p>
<input id="web_url" onchange="javascript:go()"></input>
</p>
</div>

</body>
</html>
""" 
    pdf_choices = ''
    if len(files) > 0:
        pdf_choices += '<ul>'
        for file in files:
            id = str(file['id'])
            name = file['display_name']
            if not name.lower().endswith('.pdf'):
                continue
            pdf_choices += '<li><input type="radio" name="pdf_choice" onclick="javascript:go()" value="%s" id="%s">%s</li>' % (name, id, name) 
        pdf_choices += '</ul>'
   
    html = template % (
        return_url,
        launch_url_template,
        pdf_choices
        )
    r = Response(html.encode('utf-8'))
    r.content_type = 'text/html'
    return r

def lti_pdf(request, oauth_consumer_key=None, lis_outcome_service_url=None, lis_result_sourcedid=None, course=None, name=None, value=None):
    post_data = capture_post_data(request)
    file_id = value
    lti_token = auth_data.get_lti_token(oauth_consumer_key)
    if lti_token is None:
      return token_init(request, 'pdf:' + urllib.quote(json.dumps(post_data)))
    canvas_server = auth_data.get_canvas_server(oauth_consumer_key)
    url = '%s/api/v1/courses/%s/files/%s' % (canvas_server, course, file_id)
    sess = requests.Session()
    r = sess.get(url=url, headers={'Authorization':'Bearer %s' % lti_token})
    if r.status_code == 401:
      logger.info( 'lti_pdf: refreshing token' )
      return refresh_init(request, 'pdf:' + urllib.quote(json.dumps(post_data)))
    if r.status_code == 200:
        j = r.json()
        logger.info( j )
        try:
            url = j['url']
            logger.info( url )
            fname = str(time.time()) + '.pdf'
            urllib.urlretrieve(url, fname)
            fingerprint = get_pdf_fingerprint(fname)
            pdf_uri = 'urn:x-pdf:%s' % fingerprint
            export_url = '%s?uri=%s' % (lti_export_url, pdf_uri)
            os.rename(fname, './pdfjs/viewer/web/' + fname)
            return pdf_response(oauth_consumer_key=oauth_consumer_key, lis_outcome_service_url=lis_outcome_service_url, lis_result_sourcedid=lis_result_sourcedid, name=name, fname=fname, export_url=export_url)
        except:
            return simple_response(traceback.print_exc())
    else:
        return simple_response('no file %s in course %s' % (file, course))

def web_response(oauth_consumer_key=None, lis_outcome_service_url=None, lis_result_sourcedid=None, name=None, value=None, user=None, ):
    url = value
    template = """
<html>
<head>
<style>
body { font-family:verdana; margin:.5in; }
</style>
</head>
<body>
%s
<p>When you're done annotating <i>%s</i>, click <input type="button" value="Submit Assignment" onclick="javascript:location.href='%s'"></p>
<iframe width="100%%" height="1000px" src="/viewer/web/%s"></iframe>
</body>
</html>
""" 
    # work around https://github.com/hypothesis/via/issues/76
    fname = str(time.time()) + '.html'
    logger.info( 'via url: %s' % url )
    r = requests.get('https://via.hypothes.is/%s' % url)
    logger.info ( 'via result: %s' % r.status_code )
    text = r.text.replace('return', '// return')
    fname = str(time.time()) + '.html'
    f = open('./pdfjs/viewer/web/%s' % fname, 'wb') # temporary!
    f.write(text.encode('utf-8'))
    f.close()
    export_url = '%s?uri=%s' % (lti_export_url, url)
    submit_url = make_submit_url (
        oauth_consumer_key=oauth_consumer_key, 
        lis_outcome_service_url=lis_outcome_service_url, 
        lis_result_sourcedid=lis_result_sourcedid, 
        export_url=export_url
        )
    html = template % (boilerplate, name, submit_url, fname)
    r = Response(html.encode('utf-8'))
    r.content_type = 'text/html'
    return r

def lti_web(request, oauth_consumer_key=None, lis_outcome_service_url=None, lis_result_sourcedid=None, course=None, name=None, value=None):  # no api token needed in this case
    oauth_consumer_key = get_post_or_query_param(request, OAUTH_CONSUMER_KEY)
    course = get_post_or_query_param(request, CUSTOM_CANVAS_COURSE_ID)
    user = get_post_or_query_param(request, CUSTOM_CANVAS_USER_ID)
    return web_response(oauth_consumer_key, lis_outcome_service_url, lis_result_sourcedid, name, value)

def lti_submit(request, oauth_consumer_key=None, lis_outcome_service_url=None, lis_result_sourcedid=None, export_url=None):
    post_data = capture_post_data(request)
    oauth_consumer_key = get_post_or_query_param(request, OAUTH_CONSUMER_KEY)
    lis_outcome_service_url = get_post_or_query_param(request, LIS_OUTCOME_SERVICE_URL)
    lis_result_sourcedid = get_post_or_query_param(request, LIS_RESULT_SOURCEDID)
    export_url = get_post_or_query_param(request, EXPORT_URL)
    lti_token = auth_data.get_lti_token(oauth_consumer_key)
    if lti_token is None:
      return token_init(request, 'submit:' + urllib.quote(json.dumps(post_data)))
    secret = auth_data.get_lti_secret(oauth_consumer_key)
    oauth = OAuth1(client_key=oauth_consumer_key, client_secret=secret, signature_method='HMAC-SHA1', signature_type='auth_header', force_include_body=True)
    body = submission_template
    body = body.replace('__URL__', export_url)
    body = body.replace('__SOURCEDID__', lis_result_sourcedid)
    headers = {'Content-Type': 'application/xml'}
    r = requests.post(url=lis_outcome_service_url, data=body, headers=headers, auth=oauth)
    logger.info ( 'lti_submit: %s' % r.status_code )
    response = None
    if ( r.status_code == 200 ):
        response = 'OK! Assignment successfuly submitted.'
    else:
        response = 'Something is wrong. %s %s' % (r.status_code, r.text)        
    return simple_response(response)

def lti_export(request):
    uri = get_query_param(request, 'uri')
    export_url = '%s/export/facet.html?facet=uri&mode=documents&search=%s' % ( lti_server, urllib.quote(uri) )
    return HTTPFound(location=export_url)


from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.response import Response

config = Configurator()

config.add_route('token_callback', '/token_callback')
config.add_view(token_callback, route_name='token_callback')

config.add_route('refresh_callback', '/refresh_callback')
config.add_view(refresh_callback, route_name='refresh_callback')

config.add_route('lti_setup', '/lti_setup')
config.add_view(lti_setup, route_name='lti_setup')

config.add_route('lti_pdf', '/lti_pdf')
config.add_view(lti_pdf, route_name='lti_pdf')

config.add_route('lti_web', '/lti_web')
config.add_view(lti_web, route_name='lti_web')

config.add_route('lti_submit', '/lti_submit')
config.add_view(lti_submit, route_name='lti_submit')

config.add_route('lti_export', '/lti_export')
config.add_view(lti_export, route_name='lti_export')

config.add_route('config_xml', '/config')
config.add_view(config_xml, route_name='config_xml')

config.add_route('about', '/')
config.add_view(about, route_name='about')

from pyramid.static import static_view

pdf_view = static_view('./pdfjs')
config.add_route('catchall_pdf', '/viewer/*subpath')
config.add_view(pdf_view, route_name='catchall_pdf')

config.add_static_view(name='export', path='./export')
 
app = config.make_wsgi_app()

if __name__ == '__main__': # local testing

    server = make_server(lti_server_host_internal, lti_server_port_internal, app)
    server.serve_forever()
    

