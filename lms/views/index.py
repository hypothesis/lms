from pyramid.view import view_config


@view_config(route_name='index',
             renderer="lms:templates/base.html.jinja2")
def index():
    """Render an empty page that contains a needed Google verification meta tag."""
    return {}
