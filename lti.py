import json
import urllib
import urlparse
import requests
import  traceback
import pyramid
import sys
import time
import os
from pyramid.httpexceptions import HTTPFound

#argv = sys.argv
argv = [None, 'http', 'h.jonudell.info', 3000, 'http', 'h.jonudell.info', 8000]
#argv = [None, 'http', 'h.jonudell.info', 3000, 'http', '10.0.0.9', 8000]

canvas_scheme = argv[1]
canvas_host = argv[2]
canvas_port = argv[3]
canvas_server = '%s://%s:%s' % (canvas_scheme, canvas_host, canvas_port)

lti_scheme = argv[4]
lti_host = argv[5]
lti_port = int(argv[6])
lti_server = '%s://%s:%s' % (lti_scheme, lti_host, lti_port)

# just for local testing
#lti_server_external = '%s://%s:%s' % (lti_scheme, '98.234.245.185', lti_port)
lti_server_external = lti_server
print lti_server, lti_server_external

lti_token = None
lti_refresh_token = None

print '%s, %s, %s, %s, %s, %s' % (canvas_scheme, canvas_host, canvas_port, lti_scheme, lti_host, lti_port)
lti_keys = ['context_title', 'custom_canvas_assignment_id', 'custom_canvas_assignment_title', 'custom_canvas_user_login_id', 'user_id']



CUSTOM_CANVAS_COURSE_ID = 'custom_canvas_course_id'
CUSTOM_CANVAS_USER_ID = 'custom_canvas_user_id'
CUSTOM_CANVAS_ASSIGNMENT_ID = 'custom_canvas_assignment_id'
OAUTH_CONSUMER_KEY = 'oauth_consumer_key'

canvas_client_secret = None

lti_setup_url = '%s/lti_setup' % lti_server_external
lti_pdf_url   = '%s/lti_pdf'   % lti_server_external
lti_web_url   = '%s/lti_web'   % lti_server_external
lti_test_url  = '%s/lti_test'  % lti_server_external

def lti_test(request):
    post_data = capture_post_data(request)
    if lti_token is None:
      return token_init(request, 'test:' + urllib.quote(json.dumps(post_data)))
    r = Response('ok')
    return r

def show_exception():
    print traceback.print_exc()

def show_post_keys(request):
    for k in request.POST.keys():
        print '%s: %s' % (k, request.POST[k])

def unpack_state(state):
    s = state.replace('setup:','').replace('web:','').replace('pdf:','').replace('test:','')
    j = json.loads(urllib.unquote(s))
    return j

def redirect_helper(state, course, user, assignment, oauth_consumer_key):
    fmt = '%s=%s&%s=%s&%s=%s&%s=%s'
    pairs = (CUSTOM_CANVAS_COURSE_ID, course, CUSTOM_CANVAS_USER_ID, user, CUSTOM_CANVAS_ASSIGNMENT_ID, assignment, OAUTH_CONSUMER_KEY, oauth_consumer_key)
    params = fmt % pairs
    if state.startswith('setup'):
        redirect = lti_setup_url + '?' + params
    elif state.startswith('pdf'):
        redirect = lti_pdf_url   + '?' + params
    elif state.startswith('web'):
        redirect = lti_web_url   + '?' + params
    else:
        redirect = lti_test_url  + '?' + params
    return redirect

def token_init(request, state=None):
    j = unpack_state(state)
    oauth_consumer_key = j[OAUTH_CONSUMER_KEY]
    token_redirect_uri = '%s/login/oauth2/auth?client_id=%s&response_type=code&redirect_uri=%s/token_callback&state=%s' % (canvas_server, oauth_consumer_key, lti_server_external, state)
    ret = HTTPFound(location=token_redirect_uri)
    return ret

def token_callback(request):
    print 'token_callback'
    global lti_token, lti_refresh_token
    q = urlparse.parse_qs(request.query_string)
    code = q['code'][0]
    state = q['state'][0]
    j = unpack_state(state)
    course = j[CUSTOM_CANVAS_COURSE_ID]
    user = j[CUSTOM_CANVAS_USER_ID]
    assignment = j[CUSTOM_CANVAS_ASSIGNMENT_ID]
    oauth_consumer_key = j[OAUTH_CONSUMER_KEY]
    canvas_client_secret = get_client_secret(oauth_consumer_key)
    print oauth_consumer_key, canvas_client_secret

    url = '%s/login/oauth2/token' % canvas_server
    params = { 
        'grant_type':'authorization_code',
        'client_id': oauth_consumer_key,
        'client_secret': canvas_client_secret,
        'redirect_uri': '%s/token_init' % lti_server_external,
        'code': code
        }
    r = requests.post(url, params)
    j = r.json()
    print j
    lti_token = j['access_token']
    if j.has_key('refresh_token'):
        lti_refresh_token = j['refresh_token']
    redirect = redirect_helper(state, course, user, assignment, oauth_consumer_key)
    return HTTPFound(location=redirect)

def refresh_init(request, state=None):
    j = unpack_state(state)
    oauth_consumer_key = j[OAUTH_CONSUMER_KEY]
    token_redirect_uri = '%s/login/oauth2/auth?client_id=%s&response_type=code&redirect_uri=%s/refresh_callback&state=%s' % (canvas_server, oauth_consumer_key, lti_server_external, state)
    ret = HTTPFound(location=token_redirect_uri)
    return ret

def refresh_callback(request):
    global lti_token, lti_refresh_token
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

def get_external_tools(course):
    assert course is not None
    sess = requests.Session()
    url = '%s/api/v1/courses/%s/external_tools' % (canvas_server, course)
    r = sess.get(url, headers={'Authorization':'Bearer %s' % lti_token})
    return r.json()

def get_assignments(course):
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

def create_pdf_external_tool(oauth_consumer_key, course):
    external_tools = get_external_tools(course)
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
    create_pdf_external_tool(oauth_consumer_key, course)
    assignments = get_assignments(course)
    existing = [x for x in assignments if x['integration_data'].has_key('pdf') and x['integration_data']['pdf'] == str(file_id)]
    if len(existing):
        return '<p>reusing pdf assignment for %s' % filename
    sess = requests.Session()
    data = {
        "assignment" : {
            "name": "Annotate " + filename,
            "integration_id" : "Hypothesis",
            "integration_data": {"pdf": str(file_id)},
            "submission_types" : ["external_tool"],
            "external_tool_tag_attributes": {
                "url":"%s/lti_pdf" % lti_server_external,
                "new_tab" : "true"
                }
            }
        }
    url = '%s/api/v1/courses/%s/assignments' % (canvas_server, course)
    r = sess.post(url=url, headers={'Content-Type':'application/json', 'Authorization':'Bearer %s' % lti_token}, data=json.dumps(data))
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

def get_client_secret(client_id):
    s = open('canvas-secrets.json').read()
    j = json.loads(s)
    if j.has_key(client_id):
        return j[client_id]
    else:
        return None

def lti_setup(request):
    post_data = capture_post_data(request)
    if lti_token is None:
      return token_init(request, 'setup:' + urllib.quote(json.dumps(post_data)))
    course = get_post_or_query_param(request, CUSTOM_CANVAS_COURSE_ID)
    oauth_consumer_key = get_post_or_query_param(request, OAUTH_CONSUMER_KEY)
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
    post_data = {%s: %s, 'files': %s, 'urls':urls}
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
<p>Existing PDF assignments:</p>
%s
<p>PDF assignments to create:</p>
%s
<p>Existing web assignments:</p>
%s
<p>Web assignments to create:</p>
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

    assignments = get_assignments(course)
    pdf_assignments = [a for a in assignments if a["integration_data"].has_key("pdf")]
    existing_pdf_ids = []

    for pdf_assignment in pdf_assignments:
        existing_pdf_assignments += '<li>%s</li>' % pdf_assignment['name']
        existing_pdf_ids.append(pdf_assignment["integration_data"]["pdf"])
    
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
            pdf_assignments_to_create += '<li><input type="checkbox" value="%s" id="%s">%s</li>' % (name, id, id) 
            unassigned_files.append({ 'id': id, 'name': name })
    
    web_assignments = [a for a in assignments if a["integration_data"].has_key("web")]
    web_assignments_to_create = ''
    for web_assignment in web_assignments:
        existing_web_assignments += '<li>%s</li>' % web_assignment['name']

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
    course = j[CUSTOM_CANVAS_COURSE_ID]
    urls = j['urls']
    files = j['files']

    str = ''
    try:
        for file in files:
            display_name = file['name']
            file_id = file['id']
            str += create_pdf_annotation_assignment(oauth_consumer_key, course, display_name, file_id)
    except:
        show_exception()

    try:
        for url in urls:
            if url == '':
                continue
            str += create_web_annotation_assignment(oauth_consumer_key, course, url)
    except:
        show_exception()

    print str
    html = template % (str)
    r = Response(html.encode('utf-8'))
    r.content_type = 'text/html'
    return r

def lti_pdf(request):
    post_data = capture_post_data(request)
    if lti_token is None:
      return token_init(request, 'pdf:' + urllib.quote(json.dumps(post_data)))
    course = get_post_or_query_param(request, CUSTOM_CANVAS_COURSE_ID)
    assignment = get_post_or_query_param(request, CUSTOM_CANVAS_ASSIGNMENT_ID)
    assignment_url = '%s/api/v1/courses/%s/assignments/%s' % (canvas_server, course, assignment)
    sess = requests.Session()
    r = sess.get(url=assignment_url, headers={'Authorization':'Bearer %s' % lti_token})
    if r.status_code == 401:
      return refresh_init(request, 'pdf:' + urllib.quote(json.dumps(post_data)))
    j = r.json()
    assert j.has_key("integration_data")
    file_id = j["integration_data"]["pdf"]
    url = '%s/api/v1/courses/%s/files/%s' % (canvas_server, course, file_id)
    sess = requests.Session()
    r = sess.get(url=url, headers={'Authorization':'Bearer %s' % lti_token})
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
    external_tools = get_external_tools(course)
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
    assignments = get_assignments(course)
    existing = [x for x in assignments if x['integration_data'].has_key('web') and x['integration_data']['web'] == url]
    if len(existing):
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
    r = '<p>created web annotation assignment for %s: %s' % (url, r.status_code)
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
    if lti_token is None:
      return token_init(request, 'web:' + urllib.quote(json.dumps(post_data)))
    course = get_post_or_query_param(request, CUSTOM_CANVAS_COURSE_ID)
    assignment = get_post_or_query_param(request, CUSTOM_CANVAS_ASSIGNMENT_ID)
    user = get_post_or_query_param(request, CUSTOM_CANVAS_USER_ID)
    assignment_url = '%s/api/v1/courses/%s/assignments/%s' % (canvas_server, course, assignment)
    sess = requests.Session()
    r = sess.get(url=assignment_url, headers={'Authorization':'Bearer %s' % lti_token})
    if r.status_code == 401: # and req header includes www-authenticate? https://canvas.instructure.com/doc/api/file.oauth.html
      return refresh_init(request, 'web:' + urllib.quote(json.dumps(post_data)))
    j = r.json()
    url = j["integration_data"]["web"]
    return web_response_with_post_data(request, url, user)

if __name__ == '__main__':

    from wsgiref.simple_server import make_server
    from pyramid.config import Configurator
    from pyramid.response import Response

    config = Configurator()

    config.add_route('lti_test', '/lti_test')
    config.add_view(lti_test, route_name='lti_test')

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
    server = make_server(lti_host, lti_port, app)
    server.serve_forever()
    

