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
import md5
import logging
import filelock
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
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

lti_server_scheme = 'https'
lti_server_host = 'lti.hypothesislabs.com'
lti_server_port = None

#lti_server_scheme = 'https'
#lti_server_host = 'h.jonudell.info'
#lti_server_port = None

#lti_server_scheme = 'http'
#lti_server_host = '98.234.245.185'
#lti_server_port = 8000

if lti_server_port is None:
    lti_server = '%s://%s' % (lti_server_scheme, lti_server_host)
else:
    lti_server = '%s://%s:%s' % (lti_server_scheme, lti_server_host, lti_server_port)

logger.info( 'lti_server: %s' % lti_server )

lti_keys = ['context_title', 'custom_canvas_assignment_id', 'custom_canvas_assignment_title', 'custom_canvas_user_login_id', 'user_id']

# canvas params
CUSTOM_CANVAS_COURSE_ID = 'custom_canvas_course_id'
CUSTOM_CANVAS_USER_ID = 'custom_canvas_user_id'
CUSTOM_CANVAS_ASSIGNMENT_ID = 'custom_canvas_assignment_id'
OAUTH_CONSUMER_KEY = 'oauth_consumer_key'
EXT_CONTENT_RETURN_TYPES = 'ext_content_return_types'
EXT_CONTENT_RETURN_URL = 'ext_content_return_url'
LIS_OUTCOME_SERVICE_URL = 'lis_outcome_service_url'
LIS_RESULT_SOURCEDID = 'lis_result_sourcedid'

# our params
EXPORT_URL = 'export_url'
ASSIGNMENT_TYPE = 'assignment_type'
ASSIGNMENT_NAME = 'assignment_name'
ASSIGNMENT_VALUE = 'assignment_value'

lti_setup_url = '%s/lti_setup' % lti_server
lti_pdf_url = '%s/lti_pdf' % lti_server
lti_web_url = '%s/lti_web' % lti_server
lti_submit_url = '%s/lti_submit' % lti_server
lti_export_url = '%s/lti_export' % lti_server

NO_PDF_FINGERPRINT = 'no pdf fingerprint'

submission_pox_template = """
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
          <resultData>
            <url>__URL__</url>
          </resultData>
        </result>
      </resultRecord>
    </replaceResultRequest>
  </imsx_POXBody>
</imsx_POXEnvelopeRequest
"""

submission_form_template = """
<script>
function make_submit_url() {
    var h_user = document.querySelector('#h_username').value.trim();
    var submit_url = '/lti_submit?oauth_consumer_key=__OAUTH_CONSUMER_KEY__&lis_outcome_service_url=__LIS_OUTCOME_SERVICE_URL__&lis_result_sourcedid=__LIS_RESULT_SOURCEDID__';
    var export_url = '__LTI_SERVER__/lti_export?args=' + encodeURIComponent('uri=__DOC_URI__&user=' + h_user);
    console.log(export_url);
    console.log(encodeURIComponent(export_url));
    submit_url += '&export_url=' + encodeURIComponent(export_url);
    return submit_url;
}
function clear_input() {
  var h_user = document.querySelector('#h_username');
  var check_element = document.getElementById('check_username');
  h_user.value = '';
  check_element.querySelector('a').innerText = '';
  check_element.querySelector('a').href = '';

}
function show_stream_link() {
    var h_user = document.querySelector('#h_username').value.trim();
    var check_element = document.getElementById('check_username');
    check_element.style.display = 'inline';
    check_element.querySelector('a').innerText = h_user;
    check_element.querySelector('a').href = 'https://hypothes.is/stream?q=user:' + h_user;
}
</script>
<p>
When you're done annotating:
<div>1. Enter your Hypothesis username: <input onfocus="javascript:clear_input()" onchange="javascript:show_stream_link()" id="h_username"></div>
<div>2. Check the name:  <span style="display:none" id="check_username"> <a target="stream" title="check your name" href=""> </a></span>
<div>3. Click <input type="button" value="Submit Assignment" onclick="javascript:location.href=make_submit_url()"></div>
</p>


"""  

assignment_boilerplate = """<p>
This document is annotatable using <a href="https://hypothes.is">Hypothes.is</a>. 
You can click highlighted text or expand the sidebar to view existing annotations. 
You'll need to register for (or log in to) an account in order to create annotations; 
you can do so in the Hypothesis sidebar.</p>
"""

class AuthData(): 
    """
    A simple config db, with records like so:

    "93820000000000002": {        # situation 1 in the install doc: admin provided key/secret
      "canvas_server_host": "hypothesis.instructure.com", 
      "canvas_server_port": null, 
      "canvas_server_scheme": "https", 
      "lti_refresh_token": "9382~yRo ... Rlid9UXLhxfvwkWDnj",        # this was written back after oauth
      "lti_token": "9382~IAbeGEFScV  ... IIMaEdK3dXlm2d9cjozd",      # this was written back after oauth
      "secret": "tJzcNSZadqlHTCW6ow  ... wodX3dfeuIokkLMjrQJqw3Y2",  # from the canvas dev key/secret record
      "redirect": "https://lti.hypothesislabs.com"  # a comment to help visually associate the record with the canvas dev key/secret record
  }, 
     "jaimejordan": {       # situation 2: teacher created a token, we installed it and created the key/secret
      "canvas_server_host": "hypothesis.instructure.com", 
      "canvas_server_port": null, 
      "canvas_server_scheme": "https", 
      "lti_refresh_token": null,                      # unused because token hardcoded in this case
      "lti_token": "9382~IAbeGEFSc ... VGmtBU",       # token generated by teacher (canvas "approved integration")
      "secret": "jaimejordan",  
      "redirect": "https://lti.hypothesislabs.com"    # a comment to help visually associate the record with the canvas dev key/secret record
  }, 

    """
    def __init__(self):
        self.name = 'canvas-auth.json'
        self.auth_data = {}
        self.load()

    def set_tokens(self, oauth_consumer_key, lti_token, lti_refresh_token):
        assert (self.auth_data.has_key(oauth_consumer_key))
        lock = filelock.FileLock("authdata.lock")
        with lock.acquire(timeout = 1):
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
        for key in self.auth_data.keys():
            logger.info( 'key: %s' % key) 
        f.close()

    def save(self):
        f = open(self.name, 'wb')
        j = json.dumps(self.auth_data, indent=2, sort_keys=True)
        f.write(j)
        f.close()  

auth_data = AuthData()

def get_pdf_fingerprint(hash):
    """
    We need the fingerprint to query for annotations on the submission page.

    NB: PDFJS always reports fingerpints with lowercase letters and that's required for a Hypothesis lookup,
    even when the fingerprint found in the doc uses uppercase!
    """
    f = open('./pdfjs/viewer/web/%s.pdf' % hash, 'rb')
    s = f.read()
    m = re.findall('ID\s*\[\s*<(\w+)>',s)
    f.close()
    if len(m) > 0:
        return m[0].lower()
    else:
        return NO_PDF_FINGERPRINT

def instantiate_submission_template( oauth_consumer_key=None, lis_outcome_service_url=None, lis_result_sourcedid=None, doc_uri=None):
    """
    For the Find interaction we need to inject these values into the JS we generate.
    """
    submit_html = submission_form_template
    submit_html = submit_html.replace('__OAUTH_CONSUMER_KEY__', oauth_consumer_key)
    submit_html = submit_html.replace('__LIS_OUTCOME_SERVICE_URL__', lis_outcome_service_url)
    submit_html = submit_html.replace('__LIS_RESULT_SOURCEDID__', lis_result_sourcedid)
    submit_html = submit_html.replace('__DOC_URI__', doc_uri)
    submit_html = submit_html.replace('__LTI_SERVER__', lti_server)
    return submit_html

def unpack_state(state):
    dict = json.loads(urllib.unquote(state))
    return dict

def pack_state(dict):
    state = urllib.quote(json.dumps(dict))
    return state

def token_init(request, state=None):
    """ We don't have a Canvas API token yet. Ask Canvas for an authorization code to begin the token-getting OAuth flow """
    dict = unpack_state(state)
    logger.info( 'token_init: state: %s' % dict )
    oauth_consumer_key = dict[OAUTH_CONSUMER_KEY]
    canvas_server = auth_data.get_canvas_server(oauth_consumer_key)
    token_redirect_uri = '%s/login/oauth2/auth?client_id=%s&response_type=code&redirect_uri=%s/token_callback&state=%s' % (canvas_server, oauth_consumer_key, lti_server, state)
    ret = HTTPFound(location=token_redirect_uri)
    logger.info( 'token_init ' + token_redirect_uri )
    return ret

def refresh_init(request, state=None):
    """ Our Canvas API token expired. Ask Canvas for an authorization code to begin the token-refreshing OAuth flow """
    dict = unpack_state(state)
    logger.info( 'refresh_init: state: %s' % dict )
    oauth_consumer_key = dict[OAUTH_CONSUMER_KEY]
    canvas_server = auth_data.get_canvas_server(oauth_consumer_key)
    token_redirect_uri = '%s/login/oauth2/auth?client_id=%s&response_type=code&redirect_uri=%s/refresh_callback&state=%s' % (canvas_server, oauth_consumer_key, lti_server, state)
    ret = HTTPFound(location=token_redirect_uri)
    return ret

@view_config( route_name='token_callback' )
def token_callback(request):
    return oauth_callback(request, type='token')

@view_config( route_name='refresh_callback' )
def refresh_callback(request):
    return oauth_callback(request, type='refresh')

def oauth_callback(request, type=None):
    """ Canvas called back with an authorization code. Use it to get or refresh an API token """
    logger.info ( 'oauth_callback: %s' % request.query_string )
    q = urlparse.parse_qs(request.query_string)
    code = q['code'][0]
    state = q['state'][0]
    dict = unpack_state(state)
    logger.info ( 'oauth_callback: %s' % state)

    course = dict[CUSTOM_CANVAS_COURSE_ID]
    user = dict[CUSTOM_CANVAS_USER_ID]
    oauth_consumer_key = dict[OAUTH_CONSUMER_KEY]
    ext_content_return_url = dict[EXT_CONTENT_RETURN_URL]
    lis_outcome_service_url = dict[LIS_OUTCOME_SERVICE_URL]
    lis_result_sourcedid = dict[LIS_RESULT_SOURCEDID]

    assignment_type = dict[ASSIGNMENT_TYPE]
    assignment_name = dict[ASSIGNMENT_NAME]
    assignment_value = dict[ASSIGNMENT_VALUE]

    canvas_client_secret = auth_data.get_lti_secret(oauth_consumer_key)
    lti_refresh_token = auth_data.get_lti_refresh_token(oauth_consumer_key)
    canvas_server = auth_data.get_canvas_server(oauth_consumer_key)
    url = '%s/login/oauth2/token' % canvas_server
    grant_type = 'authorization_code' if type == 'token' else 'refresh_token'
    params = { 
            'grant_type': grant_type,
            'client_id': oauth_consumer_key,
            'client_secret': canvas_client_secret,
            'redirect_uri': '%s/token_init' % lti_server # this uri must match the uri in Developer Keys but is not called from
            }                                            # canvas. rather it calls token_callback or refresh callback 
    if grant_type == 'authorization_code': 
        params['code'] = code
    else:
        params['refresh_token'] = lti_refresh_token
    r = requests.post(url, params)
    dict = r.json()
    lti_token = dict['access_token']
    if dict.has_key('refresh_token'): # does it ever not?
        lti_refresh_token = dict['refresh_token']
    auth_data.set_tokens(oauth_consumer_key, lti_token, lti_refresh_token)
    redirect = lti_setup_url + '?%s=%s&%s=%s&%s=%s&%s=%s&%s=%s&%s=%s&%s=%s' % (
        CUSTOM_CANVAS_COURSE_ID, course, 
        CUSTOM_CANVAS_USER_ID, user, 
        OAUTH_CONSUMER_KEY, oauth_consumer_key, 
        EXT_CONTENT_RETURN_URL, ext_content_return_url,
        ASSIGNMENT_TYPE, assignment_type,
        ASSIGNMENT_NAME, assignment_name,
        ASSIGNMENT_VALUE, assignment_value
        )
    return HTTPFound(location=redirect)

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

@view_config( route_name='config_xml' )
def config_xml(request):
    with open('config.xml') as f:
        xml = f.read()
        logger.info( 'config request' )
        r = Response(xml)
        r.content_type = 'text/xml'
        return r

@view_config( route_name='about' )
def about(request):
    with open('about.html') as f:
        html = f.read()
        logger.info( 'about request' )
        r = Response(html)
        r.content_type = 'text/html'                  
        return r

def pdf_response(oauth_consumer_key=None, lis_outcome_service_url=None, lis_result_sourcedid=None, name=None, hash=None, doc_uri=None):
    logger.info( 'pdf_response: %s, %s, %s, %s, %s, %s' % (oauth_consumer_key, lis_outcome_service_url, lis_result_sourcedid, name, hash, doc_uri) )
    template = """
 <html>
 <head> <style> body { font-family:verdana; margin:.5in; } </style> </head>
 <body>
%s
<p><i>%s</i></p>
%s
 <iframe width="100%%" height="1000px" src="/viewer/web/viewer.html?file=%s.pdf"></iframe>
 </body>
 </html>
"""                 
    submit_html = ''
    if lis_result_sourcedid is not None:
        submit_html = instantiate_submission_template(oauth_consumer_key, lis_outcome_service_url, lis_result_sourcedid, doc_uri)
    html = template % (assignment_boilerplate, name, submit_html, hash)
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

@view_config( route_name='lti_setup' )
def lti_setup(request):
    """
    LTI-launched from a Canvas assignment's Find interaction to present choice of doc (PDF or URL) to annotate.
  
    LTI-launched again when the Canvas assignment opens.
  
    In those two cases we have LTI params in the HTTP POST -- if we have a Canvas API token.

    If there is no token, or the token is expired, called instead by way of OAuth redirect. 
    In that case we expect params in the query string.
    """
    logger.info ( 'lti_setup: query: %s' % request.query_string )
    logger.info ( 'lti_setup: post: %s' % request.POST )
    dict = capture_post_data(request)

    oauth_consumer_key = get_post_or_query_param(request, OAUTH_CONSUMER_KEY)
    if oauth_consumer_key is None:
        logger.error( 'oauth_consumer_key cannot be None %s' % request.POST )
    oauth_consumer_key = oauth_consumer_key.strip()
    lis_outcome_service_url = get_post_or_query_param(request, LIS_OUTCOME_SERVICE_URL)
    lis_result_sourcedid = get_post_or_query_param(request, LIS_RESULT_SOURCEDID)

    course = get_post_or_query_param(request, CUSTOM_CANVAS_COURSE_ID)
    if course is None:
        logger.error ( 'course cannot be None' )
        return simple_response('No course number. Was Privacy set to Public for this installation of the Hypothesis LTI app? If not please do so (or ask someone who can to do so).')
    
    dict[ASSIGNMENT_TYPE] = get_post_or_query_param(request, ASSIGNMENT_TYPE)
    dict[ASSIGNMENT_NAME] = get_post_or_query_param(request, ASSIGNMENT_NAME)
    dict[ASSIGNMENT_VALUE] = get_post_or_query_param(request, ASSIGNMENT_VALUE)

    logger.info ( 'lti_setup: dict: %s' % dict )

    try:
        lti_token = auth_data.get_lti_token(oauth_consumer_key)
    except:
        response = "We don't have the Consumer Key %s in our database yet." % oauth_consumer_key
        logger.error ( response )
        logger.error ( traceback.print_exc() )
        return simple_response(response)

    if lti_token is None:
        logger.info ( 'lti_setup: getting token' )
        return token_init(request, pack_state(dict))

    sess = requests.Session()  # ensure we have a token before calling lti_pdf or lti_web
    canvas_server = auth_data.get_canvas_server(oauth_consumer_key)
    logger.info ( 'canvas_server: %s' % canvas_server )
    url = '%s/api/v1/courses/%s/files?per_page=100' % (canvas_server, course)
    r = sess.get(url=url, headers={'Authorization':'Bearer %s' % lti_token })
    if r.status_code == 401:
      logger.info ( 'lti_setup: refreshing token' )
      return refresh_init(request, pack_state(dict))
    files = r.json()

    #return HTTPFound(location='http://h.jonudell.info:3000/courses/2/external_content/success/external_tool_dialog?return_type=lti_launch_url&url=http%3A%2F%2F98.234.245.185%3A8000%2Flti_setup%3FCUSTOM_CANVAS_COURSE_ID%3D2%26type%3Dpdf%26name%3Dfilename%26value%3D9')
    
    assignment_type = dict[ASSIGNMENT_TYPE]
    assignment_name = dict[ASSIGNMENT_NAME]
    assignment_value = dict[ASSIGNMENT_VALUE]

    if assignment_type == 'pdf':
        return lti_pdf(request, oauth_consumer_key=oauth_consumer_key, lis_outcome_service_url=lis_outcome_service_url, lis_result_sourcedid=lis_result_sourcedid, course=course, name=assignment_name, value=assignment_value)

    if assignment_type == 'web':
        return lti_web(request, oauth_consumer_key=oauth_consumer_key, lis_outcome_service_url=lis_outcome_service_url, lis_result_sourcedid=lis_result_sourcedid, course=course, name=assignment_name, value=assignment_value)

    return_url = get_post_or_query_param(request, EXT_CONTENT_RETURN_URL)
    if return_url is None: # this is an oauth redirect so get what we sent ourselves
        return_url = get_post_or_query_param(request, 'return_url')

    logger.info ( 'return_url: %s' % return_url )

    launch_url_template = '%s/lti_setup?assignment_type=__TYPE__&assignment_name=__NAME__&assignment_value=__VALUE__&return_url=__RETURN_URL__' % lti_server

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
<input size="80" id="web_url" onchange="javascript:go()"></input>
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

def exists_pdf(hash):
    return os.path.isfile('./pdfjs/viewer/web/%s.pdf' % hash)

def exists_html(hash):
    return os.path.isfile('./pdfjs/viewer/web/%s.html' % hash)

def lti_pdf(request, oauth_consumer_key=None, lis_outcome_service_url=None, lis_result_sourcedid=None, course=None, name=None, value=None):
    """ 
    Called from lti_setup if it was called from a pdf assignment. 

    We expect to know at least the oauth_consume_key, course number, name of the PDF, 
    and value of the PDF (its number as known to the Canvas API)

    If we are called in a student context we also expect the lis* params needed for the submission URL.

    Download the PDF to a timestamp-based name in the PDFJS subtree, and call pdf_response to 
    return a page that serves it back in an iframe.
    """
    logger.info ( 'lti_pdf: query: %s' % request.query_string )
    logger.info ( 'lti_pdf: post: %s' % request.POST )
    post_data = capture_post_data(request)
    if oauth_consumer_key is None:
        oauth_consumer_key = get_post_or_query_param(request, OAUTH_CONSUMER_KEY)
    file_id = value
    try:
        lti_token = auth_data.get_lti_token(oauth_consumer_key)
    except:
        return simple_response("We don't have the Consumer Key %s in our database yet." % oauth_consumer_key)
    canvas_server = auth_data.get_canvas_server(oauth_consumer_key)
    url = '%s/api/v1/courses/%s/files/%s' % (canvas_server, course, file_id)
    m = md5.new()
    m.update('%s/%s/%s' % ( canvas_server, course, file_id ))
    hash = m.hexdigest()
    logger.info( 'server %s, course %s, file_id %s, hash %s' % ( canvas_server, course, file_id, hash ))
    if exists_pdf(hash) is False:
        sess = requests.Session()
        r = sess.get(url=url, headers={'Authorization':'Bearer %s' % lti_token})
        if r.status_code == 401:
          logger.info( 'lti_pdf: refreshing token' )
          return refresh_init(request, 'pdf:' + urllib.quote(json.dumps(post_data)))
        if r.status_code == 200:
            j = r.json()
            logger.info( j )
            url = j['url']
            logger.info( url )
            urllib.urlretrieve(url, hash)
            os.rename(hash, './pdfjs/viewer/web/%s.pdf' % hash)
        else:
            logger.error('%s retrieving %s, %s, %s' % (r.status_code, canvas_server, course, file_id))
    fingerprint = get_pdf_fingerprint(hash)
    if fingerprint == NO_PDF_FINGERPRINT:
        pdf_uri = '%s/viewer/web/%s.pdf' % ( lti_server, hash )
    else:
        pdf_uri = 'urn:x-pdf:%s' % fingerprint
    return pdf_response(oauth_consumer_key=oauth_consumer_key, lis_outcome_service_url=lis_outcome_service_url, lis_result_sourcedid=lis_result_sourcedid, name=name, hash=hash, doc_uri=pdf_uri)

def web_response(oauth_consumer_key=None, course=None, lis_outcome_service_url=None, lis_result_sourcedid=None, name=None, value=None, user=None, ):
    """
    Our app was called from an assignment to annotate a web page.

    Run it through via, and save it as a timestamped name in the PDFJS subtree.

    Neuter the JS return so the page will run in a Canvas iframe.

    Instantiate the submission template so the student can submit the assignment.

    Serve a page that wraps the (lightly) transformed via output in an iframe.
    """
    url = value
    template = """
<html>
 <head> <style> body { font-family:verdana; margin:.5in; } </style> </head>
<body>
%s
<p><i>%s</i></p>
%s
<iframe width="100%%" height="1000px" src="/viewer/web/%s.html"></iframe>
</body>
</html>
""" 
    canvas_server = auth_data.get_canvas_server(oauth_consumer_key)
    m = md5.new()
    m.update('%s/%s/%s' % ( canvas_server, course, url ))
    hash = m.hexdigest()
    logger.info( 'via url: %s' % url )
    if exists_html(hash) is False:
        r = requests.get('https://via.hypothes.is/%s' % url, headers={'User-Agent':'Mozilla'})     
        logger.info ( 'via result: %s' % r.status_code )
        text = r.text.replace('return', '// return')               # work around https://github.com/hypothesis/via/issues/76
        text = text.replace ("""src="/im_""", 'src="https://via.hypothes.is')  # and that
        f = open('./pdfjs/viewer/web/%s.html' % hash, 'wb') 
        f.write(text.encode('utf-8'))
        f.close()
    export_url = '%s?uri=%s&user=__USER__' % (lti_export_url, url)
    submit_html = ''
    if lis_result_sourcedid is not None:
        submit_html = instantiate_submission_template(oauth_consumer_key, lis_outcome_service_url, lis_result_sourcedid, url)  
    html = template % (assignment_boilerplate, name, submit_html, hash)
    r = Response(html.encode('utf-8'))
    r.content_type = 'text/html'
    return r

def lti_web(request, oauth_consumer_key=None, lis_outcome_service_url=None, lis_result_sourcedid=None, course=None, name=None, value=None):  # no api token needed in this case
    if oauth_consumer_key is None:
        oauth_consumer_key = get_post_or_query_param(request, OAUTH_CONSUMER_KEY)
    course = get_post_or_query_param(request, CUSTOM_CANVAS_COURSE_ID)
    user = get_post_or_query_param(request, CUSTOM_CANVAS_USER_ID)
    return web_response(oauth_consumer_key, course, lis_outcome_service_url, lis_result_sourcedid, name, value)

@view_config( route_name='lti_submit' )
def lti_submit(request, oauth_consumer_key=None, lis_outcome_service_url=None, lis_result_sourcedid=None, export_url=None):
    """
    Called from a student's view of an assignment.

    In theory can be an LTI launch but that's undocumented and did not seem to work. 
    So we use info we send to ourselves from the JS we generate on the assignment page.
    """
    logger.info ( 'lti_submit: query: %s' % request.query_string )
    logger.info ( 'lti_submit: post: %s' % request.POST )
    post_data = capture_post_data(request)  # unused until/unless this becomes an lti launch
    oauth_consumer_key = get_post_or_query_param(request, OAUTH_CONSUMER_KEY)
    lis_outcome_service_url = get_post_or_query_param(request, LIS_OUTCOME_SERVICE_URL)
    lis_result_sourcedid = get_post_or_query_param(request, LIS_RESULT_SOURCEDID)
    export_url = get_post_or_query_param(request, EXPORT_URL)

    try:
        secret = auth_data.get_lti_secret(oauth_consumer_key)   # because the submission must be OAuth1-signed
    except:
        return simple_response("We don't have the Consumer Key %s in our database yet." % oauth_consumer_key)

    oauth = OAuth1(client_key=oauth_consumer_key, client_secret=secret, signature_method='HMAC-SHA1', signature_type='auth_header', force_include_body=True)
    body = submission_pox_template
    body = body.replace('__URL__', export_url)
    body = body.replace('__SOURCEDID__', lis_result_sourcedid)
    headers = {'Content-Type': 'application/xml'}
    r = requests.post(url=lis_outcome_service_url, data=body, headers=headers, auth=oauth)
    logger.info ( 'lti_submit: %s' % r.status_code )
    logger.info ( 'lti_submit: %s' % r.text )
    response = None
    if ( r.status_code == 200 ):
        response = 'OK! Assignment successfully submitted.'
    else:
        response = 'Something is wrong. %s %s' % (r.status_code, r.text)        
    return simple_response(response)

@view_config( route_name='lti_export' )
def lti_export(request):
    """ 
    Called from Speed Grader, which presents the URL that the student submitted.

    Redirects to a variant of our viewer/export prototype which displays annotations for the
    assignment's PDF or URL, filtered to threads involving the (self-identified) H user, and
    highlighting contributions by that user.
    """
    args = get_query_param(request, 'args')  # because canvas swallows & in the submitted pox, we pass an opaque construct and unpack here
    logger.info ( 'lti_export: query: %s' % request.query_string )
    parsed_args = urlparse.parse_qs(args)
    user = parsed_args['user'][0]
    uri = parsed_args['uri'][0]
    logger.info( 'lti_export user: %s, uri %s' % ( user, uri) )
    export_url = '%s/export/facet.html?facet=uri&mode=documents&search=%s&user=%s' % ( lti_server, urllib.quote(uri), user )
    return HTTPFound(location=export_url)

from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.response import Response

#############
def cors_helper(request, response=None):
    if response is None:
        response = Response()
    request_headers = request.headers['Access-Control-Request-Headers'].lower()
    request_headers = re.findall('\w(?:[-\w]*\w)', request_headers)
    response_headers = ['access-control-allow-origin']
    for req_acoa_header in request_headers:
        if req_acoa_header not in response_headers:
            response_headers.append(req_acoa_header)
    response_headers = ','.join(response_headers)
    response.headers.update({
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': '%s' % response_headers
        })
    response.status_int = 204
    print ( response.headers )
    return response

@view_config( route_name='update' )
def update(request):
    if  request.method == 'OPTIONS':
        print ( 'cors preflight' )
        return cors_helper(request)
    else:
        qs = urlparse.parse_qs(request.query_string)
        id = qs['id'][0]
        token = qs['token'][0]
        data = request.body
        print ( id, token, data )
        headers = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json;charset=utf-8' }
        r1 = requests.put('https://hypothes.is/api/annotations/' + id, headers=headers, data=data, verify=False)
        print ( r1.status_code )
        print ( r1.text )
        r2 = Response(r1.text)
        r2.headers.update({
            'Access-Control-Allow-Origin': '*'
            })
        return r2
##################

config = Configurator()

config.scan()

###
config.add_route('update', '/update')
###

config.add_route('token_callback',      '/token_callback')
config.add_route('refresh_callback',    '/refresh_callback')
config.add_route('lti_setup',           '/lti_setup')
config.add_route('lti_submit',          '/lti_submit')
config.add_route('lti_export',          '/lti_export')
config.add_route('config_xml',          '/config')
config.add_route('about',               '/')

from pyramid.static import static_view

pdf_view = static_view('./pdfjs')
config.add_route('catchall_pdf', '/viewer/*subpath')
config.add_view(pdf_view, route_name='catchall_pdf')

config.add_static_view(name='export', path='./export')

app = config.make_wsgi_app()

if __name__ == '__main__': # local testing

    server = make_server(lti_server_host_internal, lti_server_port_internal, app)
    server.serve_forever()
    

