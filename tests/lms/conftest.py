import functools
import json
import os
import re
from unittest import mock

import httpretty
import jwt
import pytest
import sqlalchemy
from pyramid import testing
from pyramid.request import apply_request_extensions
from sqlalchemy.orm import sessionmaker

from lms import db
from lms.models import ApplicationInstance
from lms.services.application_instance_getter import ApplicationInstanceGetter
from lms.services.launch_verifier import LaunchVerifier
from lms.values import LTIUser

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql://postgres@localhost:5433/lms_test"
)


SESSION = sessionmaker()


@pytest.fixture(scope="session")
def db_engine():
    engine = sqlalchemy.create_engine(TEST_DATABASE_URL)
    db.init(engine)
    return engine


@pytest.yield_fixture
def db_session(db_engine):
    """
    Yield the SQLAlchemy session object.

    We enable fast repeatable database tests by setting up the database only
    once per session (see :func:`db_engine`) and then wrapping each test
    function in a transaction that is rolled back.

    Additionally, we set a SAVEPOINT before entering the test, and if we
    detect that the test has committed (i.e. released the savepoint) we
    immediately open another. This has the effect of preventing test code from
    committing the outer transaction.

    """
    conn = db_engine.connect()
    trans = conn.begin()
    session = SESSION(bind=conn)
    session.begin_nested()

    @sqlalchemy.event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):  # pylint:disable=unused-variable
        if (
            transaction.nested and not transaction._parent.nested
        ):  # pylint:disable=protected-access
            session.begin_nested()

    try:
        yield session
    finally:
        session.close()
        trans.rollback()
        conn.close()


def autopatcher(request, target, **kwargs):
    """Patch and cleanup automatically. Wraps :py:func:`mock.patch`."""
    options = {"autospec": True}
    options.update(kwargs)
    patcher = mock.patch(target, **options)
    obj = patcher.start()
    request.addfinalizer(patcher.stop)
    return obj


@pytest.fixture
def patch(request):
    return functools.partial(autopatcher, request)


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
        lambda feature: False, return_value=False
    )
    pyramid_request.lti_user = LTIUser(
        "TEST_USER_ID", "TEST_OAUTH_CONSUMER_KEY", "TEST_ROLES"
    )

    return pyramid_request


def configure_jinja2_assets(config):
    jinja2_env = config.get_jinja2_environment()
    jinja2_env.globals["asset_url"] = "http://example.com"
    jinja2_env.globals["asset_urls"] = lambda bundle: "http://example.com"
    jinja2_env.globals["js_config"] = {}


@pytest.yield_fixture
def pyramid_config(pyramid_request):
    """
    Return a test Pyramid config (Configurator) object.

    The returned Configurator uses the dummy request from the pyramid_request
    fixture above.

    """
    # Settings that will end up in pyramid_request.registry.settings.
    settings = {
        "sqlalchemy.url": TEST_DATABASE_URL,
        "via_url": "http://TEST_VIA_SERVER.is/",
        "via2_url": "http://TEST_VIA2_SERVER.is/",
        "jwt_secret": "test_secret",
        "google_client_id": "fake_client_id",
        "google_developer_key": "fake_developer_key",
        "google_app_id": "fake_app_id",
        "lms_secret": "TEST_LMS_SECRET",
        "hashed_pw": "e46df2a5b4d50e259b5154b190529483a5f8b7aaaa22a50447e377d33792577a",
        "salt": "fbe82ee0da72b77b",
        "username": "report_viewer",
        "aes_secret": b"TSeQ7E3dzbHgu5ydX2xCrKJiXTmfJbOe",
        "jinja2.filters": {
            "static_path": "pyramid_jinja2.filters:static_path_filter",
            "static_url": "pyramid_jinja2.filters:static_url_filter",
        },
        "h_client_id": "TEST_CLIENT_ID",
        "h_client_secret": "TEST_CLIENT_SECRET",
        "h_jwt_client_id": "TEST_JWT_CLIENT_ID",
        "h_jwt_client_secret": "TEST_JWT_CLIENT_SECRET",
        "h_authority": "TEST_AUTHORITY",
        "h_api_url_public": "https://example.com/api/",
        "h_api_url_private": "https://private.com/api/",
        "rpc_allowed_origins": ["http://localhost:5000"],
        "oauth2_state_secret": "test_oauth2_state_secret",
    }

    with testing.testConfig(request=pyramid_request, settings=settings) as config:
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
