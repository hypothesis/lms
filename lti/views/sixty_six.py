
from pyramid.view import view_config

from pyramid.response import FileResponse


@view_config(route_name='sixty_six')
def sixty_six(request):
  return FileResponse('./lti/templates/sixty_six/sixty_six.html.jinja2',
    request=request,
    content_type='text/html'
  )
