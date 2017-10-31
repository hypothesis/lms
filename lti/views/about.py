# -*- coding: utf-8 -*-

from pyramid.view import view_config

from pyramid.response import FileResponse


@view_config(route_name='sixty_six')
def sixty_six(request):
    return FileResponse('./lti/templates/test/test.html.jinja2',
                        request=request,
                        content_type='text/html')

# @view_config(route_name='about')
# def about(request):
#     return FileResponse('./about.html',
#                         request=request,
#                         content_type='text/html')
