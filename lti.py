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

# canvas server

canvas_server_scheme = 'https'
canvas_server_host = 'canvas.instructure.com'
canvas_server_port = None

#canvas_server_scheme = 'http'
#canvas_server_host = 'h.jonudell.info'
#canvas_server_port = 3000

if canvas_server_port is None:
    canvas_server = '%s://%s' % (canvas_server_scheme, canvas_server_host)
else:
    canvas_server = '%s://%s:%s' % (canvas_server_scheme, canvas_server_host, canvas_server_port)

# lti local testing

lti_server_host_internal = '10.0.0.9'  # for local testing
lti_server_port_internal = 8000

# lti server

lti_server_scheme = 'https'
lti_server_host = 'h.jonudell.info'
lti_server_port = None

#lti_server_scheme = 'http'
#lti_server_host = '98.234.245.185'
#lti_server_port = 8000

if lti_server_port is None:
    lti_server = '%s://%s' % (lti_server_scheme, lti_server_host)
else:
    lti_server = '%s://%s:%s' % (lti_server_scheme, lti_server_host, lti_server_port)

print '%s, %s' % (canvas_server, lti_server)

lti_keys = ['context_title', 'custom_canvas_assignment_id', 'custom_canvas_assignment_title', 'custom_canvas_user_login_id', 'user_id']

# just for local testing
#lti_server_external = '%s://%s:%s' % (lti_scheme, '98.234.245.185', lti_port)
lti_server_external = lti_server

CUSTOM_CANVAS_COURSE_ID = 'custom_canvas_course_id'
CUSTOM_CANVAS_USER_ID = 'custom_canvas_user_id'
CUSTOM_CANVAS_ASSIGNMENT_ID = 'custom_canvas_assignment_id'
OAUTH_CONSUMER_KEY = 'oauth_consumer_key'

lti_setup_url = '%s/lti_setup' % lti_server_external
lti_pdf_url = '%s/lti_pdf' % lti_server_external
lti_web_url = '%s/lti_web' % lti_server_external

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

    def load(self):
        f = open(self.name)
        self.auth_data = json.loads(f.read())
        f.close()

    def save(self):
        f = open(self.name, 'wb')
        j = json.dumps(self.auth_data)
        f.write(j)
        f.close()  

class IntegrationData(): # was hoping to avoid but per-assignment integration data in canvas requires elevated privilege
    def __init__(self):
        self.name = 'integration-data.json'
        self.assignments = []
        self.load()

    def get(self, oauth_consumer_key, course, type, assignment_id):
        l = [x for x in self.assignments if x['oauth_consumer_key']==oauth_consumer_key and x['course']==course and x['type']==type  and x['assignment_id']==assignment_id ]
        assert ( len(l) == 1 )
        return l[0]
    
    def set(self, oauth_consumer_key, course, type, assignment_id, data):
        d = {'oauth_consumer_key':oauth_consumer_key, 'course':course, 'type':type, 'assignment_id':assignment_id, 'data':data}
        self.assignments.append(d)
        self.save()

    def delete(self, oauth_consumer_key, course, assignment_id):
        for x in self.assignments:
            if x['oauth_consumer_key']==oauth_consumer_key and x['course']==course and x['assignment_id']==assignment_id:
                self.assignments.remove(x)
                self.save()

    def exists(self, oauth_consumer_key, course, type, id_or_url):
        l = [x for x in self.assignments if x['oauth_consumer_key']==oauth_consumer_key and x['course']==course and x['type']==type and x['data']['id_or_url'] == id_or_url]
        assert ( len(l) == 0 or len(l) == 1)
        return len(l) == 1

    def get_assignments_for_type(self, type):
        return [x for x in self.assignments if x['type'] == type]

    def get_all_assignments(self):
        return self.assignments

    def load(self):
        f = open(self.name)
        self.assignments = json.loads(f.read())
        f.close()

    def save(self):
        f = open(self.name, 'wb')
        j = json.dumps(self.assignments)
        f.write(j)
        f.close()  

auth_data = AuthData()
integration_data = IntegrationData()

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

def redirect_helper(state, course, user, assignment, oauth_consumer_key):
    if state.startswith('setup'):
        redirect = lti_setup_url + '?%s=%s&%s=%s&%s=%s&%s=%s' % (CUSTOM_CANVAS_COURSE_ID, course, CUSTOM_CANVAS_USER_ID, user, CUSTOM_CANVAS_ASSIGNMENT_ID, assignment, OAUTH_CONSUMER_KEY, oauth_consumer_key)
    elif state.startswith('pdf'):
        redirect = lti_pdf_url   + '?%s=%s&%s=%s&%s=%s&%s=%s' % (CUSTOM_CANVAS_COURSE_ID, course, CUSTOM_CANVAS_USER_ID, user, CUSTOM_CANVAS_ASSIGNMENT_ID, assignment, OAUTH_CONSUMER_KEY, oauth_consumer_key)
    elif state.startswith('web'):
        redirect = lti_web_url   + '?%s=%s&%s=%s&%s=%s&%s=%s' % (CUSTOM_CANVAS_COURSE_ID, course, CUSTOM_CANVAS_USER_ID, user, CUSTOM_CANVAS_ASSIGNMENT_ID, assignment, OAUTH_CONSUMER_KEY, oauth_consumer_key)
    else:
        redirect = 'unexpected state'
    return redirect

def token_init(request, state=None):
    j = unpack_state(state)
    print j
    oauth_consumer_key = j[OAUTH_CONSUMER_KEY]
    token_redirect_uri = '%s/login/oauth2/auth?client_id=%s&response_type=code&redirect_uri=%s/token_callback&state=%s' % (canvas_server, oauth_consumer_key, lti_server_external, state)
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
    assignment = j[CUSTOM_CANVAS_ASSIGNMENT_ID]
    oauth_consumer_key = j[OAUTH_CONSUMER_KEY]
    canvas_client_secret = auth_data.get_lti_secret(oauth_consumer_key)
    url = '%s://%s:%s/login/oauth2/token' % (canvas_server_scheme, canvas_server_host, canvas_server_port)
    params = { 
        'grant_type':'authorization_code',
        'client_id': oauth_consumer_key,
        'client_secret': canvas_client_secret,
        'redirect_uri': '%s/token_init' % lti_server_external,
        'code': code
        }
    r = requests.post(url, params)
    j = r.json()
    lti_token = j['access_token']
    if j.has_key('refresh_token'):
        lti_refresh_token = j['refresh_token']
    auth_data.set_tokens(oauth_consumer_key, lti_token, lti_refresh_token)
    redirect = redirect_helper(state, course, user, assignment, oauth_consumer_key)
    return HTTPFound(location=redirect)

def refresh_init(request, state=None):
    j = unpack_state(state)
    oauth_consumer_key = j[OAUTH_CONSUMER_KEY]
    token_redirect_uri = '%s/login/oauth2/auth?client_id=%s&response_type=code&redirect_uri=%s/refresh_callback&state=%s' % (canvas_server, oauth_consumer_key, lti_server_external, state)
    ret = HTTPFound(location=token_redirect_uri)
    return ret

def refresh_callback(request):
    q = urlparse.parse_qs(request.query_string)
    code = q['code'][0]
    state = q['state'][0]
    j = unpack_state(state)
    course = j[CUSTOM_CANVAS_COURSE_ID]
    user = j[CUSTOM_CANVAS_USER_ID]
    assignment = j[CUSTOM_CANVAS_ASSIGNMENT_ID]
    oauth_consumer_key = j[OAUTH_CONSUMER_KEY]
    url = '%s/login/oauth2/token' % canvas_server
    params = { 
        'grant_type':'refresh_token',
        'client_id': oauth_consumer_key,
        'client_secret': canvas_client_secret,
        'redirect_uri': '%s/token_init' % lti_server_external,
        'refresh_token': lti_refresh_token
        }
    r = requests.post(url, params)
    j = r.json()
    lti_token = j['access_token']
    if j.has_key('refresh_token'):
        lti_refresh_token = j['refresh_token']
    auth_data.set_tokens(oauth_consumer_key, lti_token, lti_refresh_token)
    redirect = redirect_helper(state, course, user, assignment, oauth_consumer_key)
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

def get_external_tools(oauth_consumer_key, course):
    assert course is not None
    lti_token = auth_data.get_lti_token(oauth_consumer_key)
    sess = requests.Session()
    url = '%s/api/v1/courses/%s/external_tools' % (canvas_server, course)
    r = sess.get(url, headers={'Authorization':'Bearer %s' % lti_token})
    return r.json()

def get_assignments(oauth_consumer_key, course):
    lti_token = auth_data.get_lti_token(oauth_consumer_key)
    assert course is not None
    sess = requests.Session()
    url = '%s/api/v1/courses/%s/assignments' % (canvas_server, course)
    r = sess.get(url, headers={'Authorization':'Bearer %s' % lti_token})
    return r.json()

def display_lti_keys(request, lti_keys):
    post_data = ''
    for key in request.POST.keys(): 
        if key in lti_keys:
            post_data += '<div>%s: %s</div>' % (key, request.POST[key])
    return post_data

"""
def delete_assignment(course, id):
    sess = requests.Session()
    print 'deleting assignment %s' % id
    url = '%s/api/v1/courses/%s/assignments/%s' % (canvas_server, course, id)
    r = sess.delete(url=url, headers={'Authorization':'Bearer %s' % lti_token})
    print r.status_code

def delete_tool(course, id):
    sess = requests.Session()
    print 'deleting tool %s' % id
    url = '%s/api/v1/courses/%s/assignments/%s' % (canvas_server, course, id)
    r = sess.delete(url=url, headers={'Authorization':'Bearer %s' % lti_token})
    print r.status_code
"""

def create_pdf_external_tool(oauth_consumer_key, course):
    lti_token = auth_data.get_lti_token(oauth_consumer_key)
    external_tools = get_external_tools(oauth_consumer_key,course)
    existing = [x for x in external_tools if x['url'].find('lti_pdf') > -1]
    if len(existing):
        print 'create_pdf_external_tool: reusing'
        return
    sess = requests.Session()
    tool_url = '%s/api/v1/courses/%s/external_tools' % (canvas_server, course)
    wrapper_url = '%s/lti_pdf' % (lti_server_external)
    payload = {'name':'pdf_annotation_assignment_tool', 'privacy_level':'public', 'consumer_key': oauth_consumer_key, 'shared_secret':'None', 'url':wrapper_url}
    r = sess.post(url=tool_url, headers={'Authorization':'Bearer %s' % lti_token}, data=payload)
    print 'create_pdf_external_tool: %s' % r.status_code

def create_pdf_annotation_assignment(oauth_consumer_key, course, filename, file_id):
    lti_token = auth_data.get_lti_token(oauth_consumer_key)
    create_pdf_external_tool(oauth_consumer_key, course)
    assignments = get_assignments(oauth_consumer_key, course)
    existing = [x for x in assignments if integration_data.exists(oauth_consumer_key, course, 'pdf', x['id'])]
    if existing:
        return '<p>reusing pdf assignment for %s' % filename
    sess = requests.Session()
    # "are you using a teacher token or admin token? Teachers are not allowed to edit/create integration IDs because doing so requires the admin level permission to manage SIS"
    data = {
        "assignment" : {
            "name": "Annotate " + filename,
            "integration_id" : "Hypothesis",                # this may be ignored
            "integration_data": {"pdf": str(file_id)},      # hence IntegrationData class in this app
            "submission_types" : ["external_tool"],
            "external_tool_tag_attributes": {
                "url":"%s/lti_pdf" % lti_server_external,
                "new_tab" : "true"
                }
            }
        }
    print data
    url = '%s/api/v1/courses/%s/assignments' % (canvas_server, course)
    r = sess.post(url=url, headers={'Content-Type':'application/json', 'Authorization':'Bearer %s' % lti_token}, data=json.dumps(data))
    status = r.status_code
    id = r.json()['id']
    name = r.json()['name']
    integration_data.set(oauth_consumer_key, course, 'pdf', str(id), {'name':name, 'id_or_url':str(file_id) })
    return '<p>created pdf assignment for %s: %s</p>' % (filename, r.status_code)

def pdf_response_with_post_data(request,fname):
    template = """
 <html> 
 <head> <style> body { font-family:verdana; margin:.5in; } </style> </head>
 <body>
 <h1>LTI launch data</h1>
 %s
 <p>Hello, student %s. Your assignment: annotate %s.</p>
 <h1>Annotatable PDF</h1>
 <iframe width="100%%" height="1000px" src="/viewer/web/viewer.html?file=%s"></iframe>
 </body>
 </html>
""" 
    post_data = display_lti_keys(request, lti_keys)
    user = request.POST['user_id'] if request.POST.has_key('user_id') else 'unknown'
    html = template % (post_data, user, fname, fname)
    r = Response(html.encode('utf-8'))
    r.content_type = 'text/html'
    return r

def capture_post_data(request):
    ret = { OAUTH_CONSUMER_KEY: None, CUSTOM_CANVAS_USER_ID: None, CUSTOM_CANVAS_COURSE_ID: None, CUSTOM_CANVAS_ASSIGNMENT_ID: None }
    if request.POST.has_key(OAUTH_CONSUMER_KEY):
        ret[OAUTH_CONSUMER_KEY] = request.POST[OAUTH_CONSUMER_KEY]
    if request.POST.has_key(CUSTOM_CANVAS_COURSE_ID):
        ret[CUSTOM_CANVAS_COURSE_ID] = request.POST[CUSTOM_CANVAS_COURSE_ID]
    if request.POST.has_key(CUSTOM_CANVAS_ASSIGNMENT_ID):
        ret[CUSTOM_CANVAS_ASSIGNMENT_ID] = request.POST[CUSTOM_CANVAS_ASSIGNMENT_ID]
    if request.POST.has_key(CUSTOM_CANVAS_USER_ID):
        ret[CUSTOM_CANVAS_USER_ID] = request.POST[CUSTOM_CANVAS_USER_ID]
    return ret

def get_post_or_query_param(request, key):
    value = get_query_param(request, key)
    if value is not None:
        ret = value
    else:
        value = get_post_param(request, key)
        ret = value
    assert ret is not None
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
    course = get_post_or_query_param(request, CUSTOM_CANVAS_COURSE_ID)
    oauth_consumer_key = get_post_or_query_param(request, OAUTH_CONSUMER_KEY)
    lti_token = auth_data.get_lti_token(oauth_consumer_key)
    if lti_token is None:
      return token_init(request, 'setup:' + urllib.quote(json.dumps(post_data)))
    template = """
<html><head> 
<style> 
body { font-family:verdana; margin:.5in; font-size:smaller } 
p { font-weight: bold }
ul { list-style-type: none; }
li { margin: 4px 0 }
</style> 
<script src="https://ajax.aspnetcdn.com/ajax/jQuery/jquery-1.11.2.min.js"></script>
<script>
function go() {
    var urls = document.getElementById('web_urls').value;
    urls = urls.split('\\n');
    var checked_boxes = document.querySelectorAll('input[value][type="checkbox"]:checked');
    var checked_files = [];
    for (var i=0; i<checked_boxes.length; i++)
        checked_files.push(checked_boxes[i].id);
    post_data = {%s: %s, 'files': %s, 'checked_files':checked_files, 'checked_boxes':checked_boxes, 'urls':urls}
    var json = JSON.stringify(post_data);
    $.ajax({
        url: '%s/lti_create?oauth_consumer_key=%s',
        data: json,
        type: "POST",
        success: function(data) { 
        console.log(data);
        document.getElementById('outcome').innerHTML = data;
        window.top.location = '%s/courses/%s/assignments';
		}
      });
  }
</script>
</head>
<body>
<p>Existing PDF assignments</p>
%s
<p>PDF assignments to create</p>
%s
<p>Existing web assignments</p>
%s
<p>Web assignments to create</p>
%s
<textarea style="width:600px;height:100px" id="web_urls">
</textarea>
<p>
<input type="submit" onclick="go()">
</p>
<p id="outcome">
</p>
</body>
</html>
""" 
    existing_web_assignments = '<ul>'
    existing_pdf_assignments = '<ul>'
    pdf_assignments_to_create = '<ul>'

    assignments = get_assignments(oauth_consumer_key, course)
    assignment_ids = [str(x['id']) for x in assignments]
    integration_assignment_ids = [y['assignment_id'] for y in integration_data.get_all_assignments()]
    for integration_assignment_id in integration_assignment_ids:
        if integration_assignment_id not in assignment_ids:
            integration_data.delete(oauth_consumer_key, course, integration_assignment_id)

    #pdf_assignments = [a for a in assignments if a["integration_data"].has_key("pdf")]
    pdf_assignments = integration_data.get_assignments_for_type('pdf')


    existing_pdf_ids = []

    for pdf_assignment in pdf_assignments:
        existing_pdf_assignments += '<li>%s</li>' % pdf_assignment['data']['name']
        existing_pdf_ids.append(pdf_assignment['data']['id_or_url'])
    
    sess = requests.Session()
    url = '%s/api/v1/courses/%s/files' % (canvas_server, course)
    r = sess.get(url=url, headers={'Authorization':'Bearer %s' % lti_token })
    if r.status_code == 401:
      return refresh_init(request, 'setup:' + urllib.quote(json.dumps(post_data)))
    files = r.json()
    unassigned_files = []

    for file in files:
        id = str(file['id'])
        name = file['display_name']
        if id not in existing_pdf_ids:
            pdf_assignments_to_create += '<li><input type="checkbox" value="%s" id="%s">%s</li>' % (id, id, name) 
            unassigned_files.append({ 'id': id, 'name': name })
    
    #web_assignments = [a for a in assignments if a["integration_data"].has_key("web")]
    web_assignments = integration_data.get_assignments_for_type('web')
    web_assignments_to_create = ''
    for web_assignment in web_assignments:
        existing_web_assignments += '<li>%s</li>' % web_assignment['data']['id_or_url']

    existing_pdf_assignments += '</ul>'
    pdf_assignments_to_create += '</ul>'
    existing_web_assignments += '</ul>'
    
    html = template % (CUSTOM_CANVAS_COURSE_ID, 
        course, 
        json.dumps(unassigned_files), 
        lti_server_external, 
        oauth_consumer_key, 
        canvas_server,
        course,
        existing_pdf_assignments, 
        pdf_assignments_to_create, 
        existing_web_assignments, 
        web_assignments_to_create)
    r = Response(html.encode('utf-8'))
    r.content_type = 'text/html'
    return r

def lti_create(request):
    oauth_consumer_key = get_post_or_query_param(request, OAUTH_CONSUMER_KEY)
    template = """
 <html> <head> <style> body { font-family:verdana; margin:.5in; } </style> </head>
 <body>
%s
 </body>
 </html>
""" 
    post_data = request.POST
    json_as_str = post_data.items()[0][0]
    j = json.loads(json_as_str)
    course = str(j[CUSTOM_CANVAS_COURSE_ID])
    urls = j['urls']
    files = j['files']
    checked_boxes = j['checked_boxes']
    checked_files = j['checked_files']
    s = ''
    try:
        for file in files:
            display_name = file['name']
            file_id = file['id']
            if file_id in checked_files:
                s += create_pdf_annotation_assignment(oauth_consumer_key, course, display_name, file_id)
    except:
        show_exception()

    try:
        for url in urls:
            if url == '':
                continue
            s += create_web_annotation_assignment(oauth_consumer_key, course, url)
    except:
        show_exception()

    print s
    html = template % (s)
    r = Response(html.encode('utf-8'))
    r.content_type = 'text/html'
    return r

def lti_pdf(request):
    post_data = capture_post_data(request)
    oauth_consumer_key = get_post_or_query_param(request, OAUTH_CONSUMER_KEY)
    lti_token = auth_data.get_lti_token(oauth_consumer_key)
    if lti_token is None:
      return token_init(request, 'pdf:' + urllib.quote(json.dumps(post_data)))
    course = get_post_or_query_param(request, CUSTOM_CANVAS_COURSE_ID)
    assignment_id = get_post_or_query_param(request, CUSTOM_CANVAS_ASSIGNMENT_ID)
    assignment = integration_data.get(oauth_consumer_key, course, 'pdf', str(assignment_id))
    file_id = assignment['data']['id_or_url']
    url = '%s/api/v1/courses/%s/files/%s' % (canvas_server, course, file_id)
    sess = requests.Session()
    r = sess.get(url=url, headers={'Authorization':'Bearer %s' % lti_token})
    if r.status_code == 401:
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
            return pdf_response_with_post_data(request, fname)
        except:
            return error_response(traceback.print_exc())
    else:
        return error_response('no file %s in course %s' % (file, course))

def create_web_external_tool(oauth_consumer_key, course, url):
    external_tools = get_external_tools(oauth_consumer_key, course)
    lti_token = auth_data.get_lti_token(oauth_consumer_key)
    existing = [x for x in external_tools if x['url'].find('lti_web') > -1]
    if len(existing):
        return '<p>create web external tool: reusing' 
    sess = requests.Session()
    tool_url = '%s/api/v1/courses/%s/external_tools' % (canvas_server, course)
    wrapper_url = '%s/lti_web' % lti_server_external
    payload = {'name':'web_annotation_assignment_tool (%s)' % url, 'privacy_level':'public', 'consumer_key': oauth_consumer_key, 'shared_secret':'None', 'url':wrapper_url}
    print oauth_consumer_key, payload, lti_token
    r = sess.post(url=tool_url, headers={'Authorization':'Bearer %s' % lti_token}, data=payload)
    print 'r: %s' % r.json()
    return '<p>created web external tool for %s: %s' % (url, r.status_code)

def create_web_annotation_assignment(oauth_consumer_key, course, url):
    create_web_external_tool(oauth_consumer_key, course, url)
    assignments = get_assignments(oauth_consumer_key, course)
    lti_token = auth_data.get_lti_token(oauth_consumer_key)
    #existing = [x for x in assignments if integration_data.get(oauth_consumer_key, course, 'web', url) == x['id']]
    existing = [x for x in assignments if integration_data.exists(oauth_consumer_key, course, 'web', url)]
    if existing:
        return '<p>reusing web assignment for %s' % url  
    sess = requests.Session()
    data = {
        "assignment" : {
            "name": "Annotate " + url,
            "integration_id" : "Hypothesis",
            "integration_data": {"web": url},
            "submission_types" : ["external_tool"],
            "external_tool_tag_attributes": {
                "url":"%s/lti_web" % lti_server_external,
                "new_tab" : "true"
                }
            }
        }
    api_url = '%s/api/v1/courses/%s/assignments' % (canvas_server, course)
    r = sess.post(url=api_url, headers={'Content-Type':'application/json', 'Authorization':'Bearer %s' % lti_token}, data=json.dumps(data))
    id = r.json()['id']
    name = r.json()['name']
    integration_data.set(oauth_consumer_key, course, 'web', str(id), {'name':name, 'id_or_url':url })
    status = r.status_code
    r = '<p>created web annotation assignment for %s: %s' % (url, status)
    return r
    
def web_response_with_post_data(request, url, user):
    template = """
 <html>
 <head>
 <style>
 body { font-family:verdana; margin:.5in; }
 </style>
 </head>
 <body>
 <h1>LTI launch data</h1>
 %s
 <h1>Annotatable Web Page</h1>
 <p>Hello, student #%s. Your assignment: annotate %s.</p>
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
    html = template % (post_data, user, url, fname)
    r = Response(html.encode('utf-8'))
    r.content_type = 'text/html'
    return r

def lti_web(request):
    post_data = capture_post_data(request)
    oauth_consumer_key = get_post_or_query_param(request, OAUTH_CONSUMER_KEY)
    lti_token = auth_data.get_lti_token(oauth_consumer_key)
    if lti_token is None:
      return token_init(request, 'web:' + urllib.quote(json.dumps(post_data)))
    post_data = capture_post_data(request)
    course = get_post_or_query_param(request, CUSTOM_CANVAS_COURSE_ID)
    assignment_id = get_post_or_query_param(request, CUSTOM_CANVAS_ASSIGNMENT_ID)
    user = get_post_or_query_param(request, CUSTOM_CANVAS_USER_ID)
    assignment = integration_data.get(oauth_consumer_key, course, 'web', str(assignment_id))
    url = assignment['data']['id_or_url']
    return web_response_with_post_data(request, url, user)

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

config.add_route('lti_create', '/lti_create')
config.add_view(lti_create, route_name='lti_create')

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
    

