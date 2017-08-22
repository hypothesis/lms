# -*- coding: utf-8 -*-

from lti.views import config


def test_it_returns_config_xml_object(pyramid_request):
    actual = config.config_xml(pyramid_request)
    assert actual['launch_url'] == 'http://example.com/lti_setup'
    assert actual['resource_selection_url'] == 'http://example.com/lti_setup'
