from pyramid.httpexceptions import HTTPFound
from pyramid.security import remember, forget
from pyramid.view import view_config, forbidden_view_config

from lms.security import check_password


class AuthenticationViews:
    def __init__(self, request):
        self.request = request
        self.logged_in = request.authenticated_userid

    @view_config(
        route_name='login',
        renderer='templates/login.html.jinja2')
    @forbidden_view_config(renderer='templates/login.html.jinja2')
    def login(self):
        request = self.request
        login_url = request.route_url('login')
        referrer = request.url
        if referrer == login_url or referrer == '/':
            referrer = '/reports'  # never use login form itself as came_from
        came_from = request.params.get('came_from', referrer)
        message = ''
        username = ''
        if 'form.submitted' in request.params:
            settings = request.registry.settings
            expected_username = settings['username']
            expected_hashed_pw = settings['hashed_pw']
            salt = settings['salt']

            username = request.params['username']
            password = request.params['password']

            if (expected_username == username and
                    password and
                    check_password(password, expected_hashed_pw, salt)):
                headers = remember(request, username)
                return HTTPFound(location=came_from, headers=headers)
            message = 'Failed login'

        return dict(
            name='Login',
            message=message,
            url=request.application_url + '/login',
            username=username,
            came_from=came_from,
        )

    @view_config(route_name='logout')
    def logout(self):
        request = self.request
        headers = forget(request)
        url = request.route_url('login')
        return HTTPFound(location=url,
                         headers=headers)
