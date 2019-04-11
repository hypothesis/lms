from pyramid.view import view_config
from pyramid import security


@view_config(route_name="test", renderer="lms:templates/test.html.jinja2")
def test_view(request):
    """Temporary test view."""
    return {}


@view_config(route_name="test_xhr", renderer="json", permission="test_permission")
def test_xhr_view(request):
    """Temporary test view."""
    return {
        "authenticated_userid": request.authenticated_userid,
        "unauthenticated_userid": request.unauthenticated_userid,
        "effective_principals": request.effective_principals,
    }
