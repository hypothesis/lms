# -*- coding: utf-8 -*-

import mock
import pytest
import urllib
import urlparse

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound

from lti import util
import lti.views.export


class TestLTIExport(object):

    def test_it_redirects_to_the_export_facet_static_file(self, pyramid_request):
        pyramid_request.query_string = 'args='+urllib.quote('uri=http://www.example.com&user=someone')
        returned = lti.views.export.lti_export(pyramid_request)
        assert isinstance(returned, HTTPFound)
        assert returned.location == 'http://TEST_LTI_SERVER.com/export/facet.html?facet=uri&mode=documents&search=http%3A//www.example.com&user=someone'

    def test_it_raises_attribute_error_when_args_is_not_set(self, pyramid_request):
        pyramid_request.query_string = 'something_else='+urllib.quote('uri=http://www.example.com')
        with pytest.raises(AttributeError) as ex:
            lti.views.export.lti_export(pyramid_request)

    def test_it_raises_key_error_when_user_param_is_not_set(self, pyramid_request):
        pyramid_request.query_string = 'args='+urllib.quote('uri=http://www.example.com')
        with pytest.raises(KeyError) as ex:
            lti.views.export.lti_export(pyramid_request)

    def test_it_raises_key_error_when_user_param_is_set_without_value(self, pyramid_request):
        pyramid_request.query_string = 'args='+urllib.quote('uri=http://www.example.com&user=')
        with pytest.raises(KeyError) as ex:
            lti.views.export.lti_export(pyramid_request)

    def test_it_raises_key_error_when_uri_param_is_not_set(self, pyramid_request):
        pyramid_request.query_string = 'args='+urllib.quote('user=someone')
        with pytest.raises(KeyError) as ex:
            lti.views.export.lti_export(pyramid_request)

    def test_it_raises_key_error_when_uri_param_is_set_without_value(self, pyramid_request):
        pyramid_request.query_string = 'args='+urllib.quote('uri=&user=someone')
        with pytest.raises(KeyError) as ex:
            lti.views.export.lti_export(pyramid_request)
