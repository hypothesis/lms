# -*- coding: utf-8 -*-
from pyramid.view import view_config


@view_config(route_name='file_picker', renderer='lms:templates/file_picker/file_picker.html.jinja2')
def file_picker(_request):
    return {}
