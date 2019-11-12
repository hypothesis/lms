import re
from unittest import mock

import httpretty
import pytest
from pyramid import testing
from pyramid.request import apply_request_extensions

from lms.services.application_instance_getter import ApplicationInstanceGetter
from lms.services.launch_verifier import LaunchVerifier
from lms.values import LTIUser
from tests.conftest import *


@pytest.fixture
def pyramid_request(db_session):
    """
    Return a dummy Pyramid request object.

    This is the same dummy request object as is used by the pyramid_config
    fixture below.

    """
    pyramid_request = testing.DummyRequest(db=db_session)
    pyramid_request.POST.update(
        {
            "oauth_consumer_key": "TEST_OAUTH_CONSUMER_KEY",
            "oauth_timestamp": "TEST_TIMESTAMP",
            "oauth_nonce": "TEST_NONCE",
            "oauth_signature_method": "SHA256",
            "oauth_signature": "TEST_OAUTH_SIGNATURE",
            "oauth_version": "1p0p0",
            "user_id": "TEST_USER_ID",
            "roles": "Instructor",
            "tool_consumer_instance_guid": "TEST_GUID",
            "content_item_return_url": "https://www.example.com",
            "lti_version": "TEST",
        }
    )
    pyramid_request.feature = mock.create_autospec(
        lambda feature: False, return_value=False  # pragma: no cover
    )
    pyramid_request.lti_user = LTIUser(
        "TEST_USER_ID", "TEST_OAUTH_CONSUMER_KEY", "TEST_ROLES"
    )

    return pyramid_request


def configure_jinja2_assets(config):
    jinja2_env = config.get_jinja2_environment()
    jinja2_env.globals["asset_url"] = "http://example.com"
    jinja2_env.globals[
        "asset_urls"
    ] = lambda bundle: "http://example.com"  # pragma: no cover
    jinja2_env.globals["js_config"] = {}


@pytest.yield_fixture
def pyramid_config(pyramid_request):
    """
    Return a test Pyramid config (Configurator) object.

    The returned Configurator uses the dummy request from the pyramid_request
    fixture above.

    """

    with testing.testConfig(request=pyramid_request, settings=TEST_SETTINGS) as config:
        config.include("pyramid_jinja2")
        config.include("pyramid_services")
        config.include("pyramid_tm")

        config.include("lms.sentry")
        config.include("lms.models")
        config.include("lms.db")
        config.include("lms.routes")

        config.add_static_view(name="export", path="lms:static/export")
        config.add_static_view(name="static", path="lms:static")

        config.action(None, configure_jinja2_assets, args=(config,))

        apply_request_extensions(pyramid_request)

        yield config


@pytest.fixture(autouse=True)
def ai_getter(pyramid_config):
    ai_getter = mock.create_autospec(
        ApplicationInstanceGetter, spec_set=True, instance=True
    )
    ai_getter.provisioning_enabled.return_value = True
    ai_getter.lms_url.return_value = "https://example.com"
    ai_getter.shared_secret.return_value = "TEST_SECRET"
    pyramid_config.register_service(ai_getter, name="ai_getter")
    return ai_getter


@pytest.fixture(autouse=True)
def launch_verifier(pyramid_config):
    launch_verifier = mock.create_autospec(LaunchVerifier, spec_set=True, instance=True)
    pyramid_config.register_service(launch_verifier, name="launch_verifier")
    return launch_verifier


@pytest.fixture(autouse=True)
def routes(pyramid_config):
    """Add all the routes that would be added in production."""
    pyramid_config.add_route("welcome", "/welcome")
    pyramid_config.add_route("config_xml", "/config_xml")
    pyramid_config.add_route(
        "module_item_configurations", "/module_item_configurations"
    )

    # lms routes
    pyramid_config.add_route("lti_launches", "/lti_launches")
    pyramid_config.add_route("content_item_selection", "/content_item_selection")


@pytest.fixture(autouse=True)
def httpretty_():
    """
    Monkey-patch Python's socket core module to mock all HTTP responses.

    We never want real HTTP requests to be sent by the tests so replace them
    all with mock responses. This handles requests sent using the standard
    urllib2 library and the third-party httplib2 and requests libraries.
    """
    httpretty.enable()

    # Tell httpretty which HTTP requests we want it to mock (all of them).
    for method in (
        httpretty.GET,
        httpretty.PUT,
        httpretty.POST,
        httpretty.DELETE,
        httpretty.HEAD,
        httpretty.PATCH,
        httpretty.OPTIONS,
        httpretty.CONNECT,
    ):
        httpretty.register_uri(
            method=method,
            uri=re.compile(r"http(s?)://.*"),  # Matches all http:// and https:// URLs.
            body="",
        )

    yield

    httpretty.disable()
    httpretty.reset()
