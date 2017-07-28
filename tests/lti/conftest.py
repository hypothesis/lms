# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import functools

import mock
import pytest
from pyramid import testing
from pyramid.request import apply_request_extensions

from lti.models import AuthData


def autopatcher(request, target, **kwargs):
    """Patch and cleanup automatically. Wraps :py:func:`mock.patch`."""
    options = {'autospec': True}
    options.update(kwargs)
    patcher = mock.patch(target, **options)
    obj = patcher.start()
    request.addfinalizer(patcher.stop)
    return obj


@pytest.fixture
def patch(request):
    return functools.partial(autopatcher, request)


@pytest.fixture
def pyramid_request():
    """
    Return a dummy Pyramid request object.

    This is the same dummy request object as is used by the pyramid_config
    fixture below.

    """
    pyramid_request = testing.DummyRequest()

    pyramid_request.auth_data = mock.create_autospec(AuthData, instance=True)
    pyramid_request.auth_data.get_canvas_server.return_value = 'https://TEST_CANVAS_SERVER.com'
    pyramid_request.auth_data.get_lti_secret.return_value = 'TEST_CLIENT_SECRET'
    pyramid_request.auth_data.get_lti_refresh_token.return_value = 'TEST_OAUTH_REFRESH_TOKEN'

    return pyramid_request


@pytest.yield_fixture
def pyramid_config(pyramid_request):
    """
    Return a test Pyramid config (Configurator) object.

    The returned Configurator uses the dummy request from the pyramid_request
    fixture above.

    """
    # Settings that will end up in pyramid_request.registry.settings.
    settings = {
        'lti_server': 'http://TEST_LTI_SERVER.com',
    }

    with testing.testConfig(request=pyramid_request, settings=settings) as config:
        apply_request_extensions(pyramid_request)
        yield config


@pytest.fixture(autouse=True)
def routes(pyramid_config):
    """Add all the routes that would be added in production."""
    pyramid_config.add_route('lti_setup', '/lti_setup')
