# -*- coding: utf-8 -*-

from pyramid.view import view_config

from pyramid.response import FileResponse


@view_config(route_name='about')
def about(request):
    return FileResponse('./about.html',
                        request=request,
                        content_type='text/html')
