from pyramid.httpexceptions import HTTPFound
from pyramid.security import remember, forget
from pyramid.view import view_config

from lms.security import USERS, check_password

class AuthenticationViews:
    @view_config(
        route_name='login',
        renderer='templates/login.html.jinja2')
    def login(self):
        request = self.request
        login_url = request.route_url('login')
        referrer = request.url
        if referrer == login_url:
            referrer = '/'  # never use login form itself as came_from
        came_from = request.params.get('came_from', referrer)
        message = ''
        login = ''
        password = ''
        if 'form.submitted' in request.params:
            login = request.params['login']
            password = request.params['password']
            hashed_pw = USERS.get(login)
            if hashed_pw and check_password(password, hashed_pw):
                headers = remember(request, login)
                return HTTPFound(location=came_from,
                                 headers=headers)
            message = 'Failed login'

        return dict(
            name='Login',
            message=message,
            url=request.application_url + '/login',
            came_from=came_from,
            login=login,
            password=password,
        )


    @view_config(route_name='logout')
    def logout(self):
        request = self.request
        headers = forget(request)
        url = request.route_url('login')
        return HTTPFound(location=url,
                         headers=headers)
