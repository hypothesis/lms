import json
import urllib
import urlparse
import requests
import traceback
import pyramid
import sys
import time
import os
from pyramid.httpexceptions import HTTPFound

# lti local testing

lti_server_host_internal = '10.0.0.9'  # for local testing
lti_server_port_internal = 8000

# lti server

lti_server_scheme = 'https'
lti_server_host = 'lti.jonudell.info'
lti_server_port = None

#lti_server_scheme = 'http'
#lti_server_host = '98.234.245.185'
#lti_server_port = 8000

if lti_server_port is None:
    lti_server = '%s://%s' % (lti_server_scheme, lti_server_host)
else:
    lti_server = '%s://%s:%s' % (lti_server_scheme, lti_server_host, lti_server_port)

print 'lti_server: %s' % lti_server

lti_keys = ['context_title', 'custom_canvas_assignment_id', 'custom_canvas_assignment_title', 'custom_canvas_user_login_id', 'user_id']

CUSTOM_CANVAS_COURSE_ID = 'custom_canvas_course_id'
CUSTOM_CANVAS_USER_ID = 'custom_canvas_user_id'
CUSTOM_CANVAS_ASSIGNMENT_ID = 'custom_canvas_assignment_id'
OAUTH_CONSUMER_KEY = 'oauth_consumer_key'
EXT_CONTENT_RETURN_TYPES = 'ext_content_return_types'
EXT_CONTENT_RETURN_URL = 'ext_content_return_url'

lti_setup_url = '%s/lti_setup' % lti_server
lti_pdf_url = '%s/lti_pdf' % lti_server
lti_web_url = '%s/lti_web' % lti_server

boilerplate = """<p>
This document is annotatable using hypothes.is. 
You can click highlighted text or expand the sidebar to view existing annotations. 
You'll need to register for or log in to an <a href="https://hypothes.is">hypothes.is</a> account in order to create annotations; 
you can do so in the sidebar.</p>"""

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

def get_config_value(client_id, key):
    if canvas_config.has_key(client_id):
        return canvas_config[client_id][key]
    else:
        print 'no config value for ' + key
        return None

def show_exception():
    print traceback.print_exc()

def show_post_keys(request):
    for k in request.POST.keys():
        print '%s: %s' % (k, request.POST[k])

def unpack_state(state):
    s = state.replace('setup:','').replace('web:','').replace('pdf:','')
    j = json.loads(urllib.unquote(s))
    return j

def redirect_helper(state, course, user, oauth_consumer_key):
    if state.startswith('setup'):
        redirect = lti_setup_url + '?%s=%s&%s=%s&%s=%s' % (CUSTOM_CANVAS_COURSE_ID, course, CUSTOM_CANVAS_USER_ID, user, OAUTH_CONSUMER_KEY, oauth_consumer_key)
    elif state.startswith('pdf'):
        redirect = lti_pdf_url   + '?%s=%s&%s=%s&%s=%s' % (CUSTOM_CANVAS_COURSE_ID, course, CUSTOM_CANVAS_USER_ID, user, OAUTH_CONSUMER_KEY, oauth_consumer_key)
    elif state.startswith('web'):
        redirect = lti_web_url   + '?%s=%s&%s=%s&%s=%s' % (CUSTOM_CANVAS_COURSE_ID, course, CUSTOM_CANVAS_USER_ID, user, OAUTH_CONSUMER_KEY, oauth_consumer_key)
    else:
        redirect = 'unexpected state'
    return redirect

def token_init(request, state=None):
    j = unpack_state(state)
    print j
    oauth_consumer_key = j[OAUTH_CONSUMER_KEY]
    canvas_server = auth_data.get_canvas_server(oauth_consumer_key)
    token_redirect_uri = '%s/login/oauth2/auth?client_id=%s&response_type=code&redirect_uri=%s/token_callback&state=%s' % (canvas_server, oauth_consumer_key, lti_server, state)
    ret = HTTPFound(location=token_redirect_uri)
    print 'token_init '
    print token_redirect_uri
    return ret

def token_callback(request):
    q = urlparse.parse_qs(request.query_string)
    code = q['code'][0]
    state = q['state'][0]
    j = unpack_state(state)
    course = j[CUSTOM_CANVAS_COURSE_ID]
    user = j[CUSTOM_CANVAS_USER_ID]
    #assignment = j[CUSTOM_CANVAS_ASSIGNMENT_ID]
    oauth_consumer_key = j[OAUTH_CONSUMER_KEY]
    canvas_client_secret = auth_data.get_lti_secret(oauth_consumer_key)
    canvas_server = auth_data.get_canvas_server(oauth_consumer_key)
    url = '%s/login/oauth2/token' % canvas_server
    params = { 
        'grant_type':'authorization_code',
        'client_id': oauth_consumer_key,
        'client_secret': canvas_client_secret,
        'redirect_uri': '%s/token_init' % lti_server,
        'code': code
        }
    r = requests.post(url, params)
    j = r.json()
    lti_token = j['access_token']
    if j.has_key('refresh_token'):
        lti_refresh_token = j['refresh_token']
    auth_data.set_tokens(oauth_consumer_key, lti_token, lti_refresh_token)
    redirect = redirect_helper(state, course, user, oauth_consumer_key)
    return HTTPFound(location=redirect)

def refresh_init(request, state=None):
    j = unpack_state(state)
    oauth_consumer_key = j[OAUTH_CONSUMER_KEY]
    canvas_server = auth_data.get_canvas_server(oauth_consumer_key)
    token_redirect_uri = '%s/login/oauth2/auth?client_id=%s&response_type=code&redirect_uri=%s/refresh_callback&state=%s' % (canvas_server, oauth_consumer_key, lti_server, state)
    ret = HTTPFound(location=token_redirect_uri)
    return ret

def refresh_callback(request):
    q = urlparse.parse_qs(request.query_string)
    code = q['code'][0]
    state = q['state'][0]
    j = unpack_state(state)
    course = j[CUSTOM_CANVAS_COURSE_ID]
    user = j[CUSTOM_CANVAS_USER_ID]
    #assignment = j[CUSTOM_CANVAS_ASSIGNMENT_ID]
    oauth_consumer_key = j[OAUTH_CONSUMER_KEY]
    canvas_client_secret = auth_data.get_lti_secret(oauth_consumer_key)
    lti_refresh_token = auth_data.get_lti_refresh_token(oauth_consumer_key)
    canvas_server = auth_data.get_canvas_server(oauth_consumer_key)
    url = '%s/login/oauth2/token' % canvas_server
    params = { 
        'grant_type':'refresh_token',
        'client_id': oauth_consumer_key,
        'client_secret': canvas_client_secret,
        'redirect_uri': '%s/token_init' % lti_server,
        'refresh_token': lti_refresh_token
        }
    r = requests.post(url, params)
    j = r.json()
    lti_token = j['access_token']
    if j.has_key('refresh_token'):
        lti_refresh_token = j['refresh_token']
    auth_data.set_tokens(oauth_consumer_key, lti_token, lti_refresh_token)
    redirect = redirect_helper(state, course, user, oauth_consumer_key)
    return HTTPFound(location=redirect)

def error_response(exc_str):
    template = """
 <html>
 <head> <style> body { font-family:verdana; margin:.5in; } </style> </head>
 <body>%s</body>
 </html>"""
    html = template % exc_str
    r = Response(html.encode('utf-8'))
    r.content_type = 'text/html'
    return r

def display_lti_keys(request, lti_keys):
    post_data = ''
    for key in request.POST.keys(): 
        if key in lti_keys:
            post_data += '<div>%s: %s</div>' % (key, request.POST[key])
    return post_data

def pdf_response(name, fname):
    template = """
 <html> 
 <head> <style> body { font-family:verdana; margin:.5in; } </style> </head>
 <body>
%s
<p>%s</p>
 <iframe width="100%%" height="1000px" src="/viewer/web/viewer.html?file=%s"></iframe>
 </body>
 </html>
""" 
    html = template % (boilerplate, name, fname)
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
            EXT_CONTENT_RETURN_URL
            ]:
        if key in request.POST.keys():
            ret[key] = request.POST[key]
    return ret

def get_post_or_query_param(request, key):
    value = get_query_param(request, key)
    if value is not None:
        ret = value
    else:
        value = get_post_param(request, key)
        ret = value
    if ret is None:
        print 'no post or query param for %s' % key
        if key == CUSTOM_CANVAS_COURSE_ID:
            print 'is privacy set to public in courses/COURSE_NUM/settings/configurations?'
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
    lti_token = auth_data.get_lti_token(oauth_consumer_key)
    if lti_token is None:
      return token_init(request, 'setup:' + urllib.quote(json.dumps(post_data)))

    #return HTTPFound(location='http://h.jonudell.info:3000/courses/2/external_content/success/external_tool_dialog?return_type=lti_launch_url&url=http%3A%2F%2F98.234.245.185%3A8000%2Flti_setup%3FCUSTOM_CANVAS_COURSE_ID%3D2%26type%3Dpdf%26name%3Dfilename%26value%3D9')

    course = get_post_or_query_param(request, CUSTOM_CANVAS_COURSE_ID)
    if course is None:
        return error_response('No course number. Was Privacy set to Public for this installation of the Hypothesis LTI app? If not please do so (or ask someone who can to do so).')

    type = get_post_or_query_param(request, 'type')
    name = get_post_or_query_param(request, 'name')
    value = get_post_or_query_param(request, 'value')
    
    if type == 'pdf':
        return lti_pdf(request, oauth_consumer_key, course, name, value)

    if type == 'web':
        return lti_web(request, oauth_consumer_key, course, name, value)

    return_url = get_post_or_query_param(request, EXT_CONTENT_RETURN_URL)

    print 'return_url: %s' % return_url

    launch_url_template = '%s/lti_setup?type=__TYPE__&name=__NAME__&value=__VALUE__' % lti_server

    sess = requests.Session()  # do this first to ensure we have a token
    canvas_server = auth_data.get_canvas_server(oauth_consumer_key)
    print 'canvas_server: %s' % canvas_server

    url = '%s/api/v1/courses/%s/files' % (canvas_server, course)
    r = sess.get(url=url, headers={'Authorization':'Bearer %s' % lti_token })
    if r.status_code == 401:
      print 'lti_setup: refreshing token'  
      return refresh_init(request, 'setup:' + urllib.quote(json.dumps(post_data)))
    files = r.json()

    print 'key %s, course %s, token %s' % (oauth_consumer_key, course, lti_token)

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
    
    launch_url = '%s/lti_setup?type=__TYPE__&name=__NAME__&value=__VALUE__' % (lti_server)
    
    html = template % (
        return_url,
        launch_url,
        pdf_choices
        )
    r = Response(html.encode('utf-8'))
    r.content_type = 'text/html'
    return r

def lti_pdf(request, oauth_consumer_key, course, name, file_id):
    lti_token = auth_data.get_lti_token(oauth_consumer_key)
    if lti_token is None:
      return token_init(request, 'pdf:' + urllib.quote(json.dumps(post_data)))
    canvas_server = auth_data.get_canvas_server(oauth_consumer_key)
    url = '%s/api/v1/courses/%s/files/%s' % (canvas_server, course, file_id)
    sess = requests.Session()
    r = sess.get(url=url, headers={'Authorization':'Bearer %s' % lti_token})
    if r.status_code == 401:
      print 'lti_pdf: refreshing token'  
      return refresh_init(request, 'pdf:' + urllib.quote(json.dumps(post_data)))
    if r.status_code == 200:
        j = r.json()
        print j
        try:
            url = j['url']
            print url
            fname = str(time.time()) + '.pdf'
            urllib.urlretrieve(url, fname)
            os.rename(fname, './pdfjs/viewer/web/' + fname)
            return pdf_response(name, fname)
        except:
            return error_response(traceback.print_exc())
    else:
        return error_response('no file %s in course %s' % (file, course))

def web_response(request, name, url, user):
    template = """
 <html>
 <head>
 <style>
 body { font-family:verdana; margin:.5in; }
 </style>
 </head>
 <body>
<!-- %s -->
 %s
 <p>%s</p>
 <iframe width="100%%" height="1000px" src="/viewer/web/%s"></iframe>
 </body>
 </html>
""" 
    post_data = display_lti_keys(request, lti_keys)
    # work around https://github.com/hypothesis/via/issues/76
    fname = str(time.time()) + '.html'
    print 'via url: %s' % url
    r = requests.get('https://via.hypothes.is/%s' % url)
    print 'via result: %s' % r.status_code
    text = r.text.replace('return', '// return')
    fname = str(time.time()) + '.html'
    f = open('./pdfjs/viewer/web/%s' % fname, 'wb') # temporary!
    f.write(text.encode('utf-8'))
    f.close()
    html = template % (post_data, boilerplate, name, fname)
    r = Response(html.encode('utf-8'))
    r.content_type = 'text/html'
    return r

def lti_web(request, oauth_consumer_key, course, name, url):  # no api token needed in this case
    oauth_consumer_key = get_post_or_query_param(request, OAUTH_CONSUMER_KEY)
    course = get_post_or_query_param(request, CUSTOM_CANVAS_COURSE_ID)
    user = get_post_or_query_param(request, CUSTOM_CANVAS_USER_ID)
    return web_response(request, name, url, user)

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

from pyramid.static import static_view
pdf_view = static_view('./pdfjs', use_subpath=True)
config.add_route('catchall_static', '/*subpath')
config.add_view(pdf_view, route_name='catchall_static')
   
app = config.make_wsgi_app()

if __name__ == '__main__': # local testing

    server = make_server(lti_server_host_internal, lti_server_port_internal, app)
    server.serve_forever()
    

