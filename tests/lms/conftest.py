# -*- coding: utf-8 -*-

import os
import functools
import json
import re

import httpretty
from unittest import mock
import pytest
import jwt
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from pyramid import testing
from pyramid.request import apply_request_extensions

from lms import db
from lms.config.resources import LTILaunch
from lms.models import User
from lms.models import Token
from lms.models import OauthState
from lms.models import build_from_lms_url
from lms.util import GET

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


def unwrap(decorated_function):
    """
    Return the function wrapped by a decorated function.

    Given a function which has been decorated by one or more `functools.wraps`
    decorators, return the wrapped function.
    """
    unwrapped = decorated_function
    while hasattr(unwrapped, "__wrapped__"):
        unwrapped = unwrapped.__wrapped__
    return unwrapped


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

    return pyramid_request


def configure_jinja2_assets(config):
    jinja2_env = config.get_jinja2_environment()
    jinja2_env.globals["asset_url"] = "http://example.com"
    jinja2_env.globals["asset_urls"] = lambda bundle: "http://example.com"


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
        "jwt_secret": "test_secret",
        "google_client_id": "fake_client_id",
        "google_developer_key": "fake_developer_key",
        "google_app_id": "fake_app_id",
        "lms_secret": "J4hd4epmhDGUibjsiUtKaLbyDEtUis8qGMFnQUJlDtYrQB1m2SM0j2oRpCXhSp7K",
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
        "h_api_url": "https://example.com/api/",
        "rpc_allowed_origins": ["http://localhost:5000"],
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


@pytest.yield_fixture
def factories(db_session):
    import factories  # pylint:disable=relative-import

    factories.set_session(db_session)
    yield factories
    factories.set_session(None)


@pytest.fixture
def lti_launch_request(monkeypatch, pyramid_request):
    """
    Handle setting up the lti launch request by monkeypatching the validation.

    This also creates the application instance that is needed in the decorator.
    """
    from lms.models import application_instance as ai  # pylint:disable=relative-import

    instance = ai.build_from_lms_url(
        "https://hypothesis.instructure.com",
        "address@)hypothes.is",
        "test",
        b"test",
        encryption_key=pyramid_request.registry.settings["aes_secret"],
    )
    pyramid_request.db.add(instance)
    pyramid_request.params["oauth_consumer_key"] = instance.consumer_key
    pyramid_request.params["custom_canvas_course_id"] = "1"
    pyramid_request.params["context_id"] = "fake_context_id"
    monkeypatch.setattr(
        "pylti.common.verify_request_common", lambda a, b, c, d, e: True
    )

    pyramid_request.context = mock.create_autospec(
        LTILaunch,
        spec_set=True,
        instance=True,
        rpc_server_config={},
        hypothesis_config={},
        provisioning_enabled=True,
    )

    yield pyramid_request


@pytest.fixture
def canvas_api_proxy(pyramid_request):

    user_id = "asdf"
    application_instance = build_from_lms_url(
        "https://example.com", "test@example.com", "test", b"test"
    )
    data = {
        "user_id": user_id,
        "roles": "",
        "consumer_key": application_instance.consumer_key,
    }
    pyramid_request.db.add(application_instance)
    user = User(lms_guid=user_id)
    pyramid_request.db.add(user)
    pyramid_request.db.flush()
    token = Token(access_token="test_token", user_id=user.id)
    pyramid_request.db.add(token)
    pyramid_request.db.flush()

    jwt_secret = pyramid_request.registry.settings["jwt_secret"]
    jwt_token = jwt.encode(data, jwt_secret, "HS256").decode("utf-8")

    pyramid_request.headers["Authorization"] = jwt_token

    pyramid_request.params["endpoint_url"] = "/test"
    pyramid_request.params["method"] = GET
    pyramid_request.params["params"] = {}
    yield {
        "request": pyramid_request,
        "user": user,
        "application_instance": application_instance,
        "jwt_token": jwt_token,
        "decoded_jwt": data,
        "token": token,
    }


@pytest.fixture
def module_item_configuration():
    from lms.models import ModuleItemConfiguration  # pylint:disable=relative-import

    instance = ModuleItemConfiguration(
        document_url="https://www.example.com",
        resource_link_id="TEST_RESOURCE_LINK_ID",
        tool_consumer_instance_guid="TEST_GUID",
    )
    yield instance


@pytest.fixture
def authenticated_request(pyramid_request):
    user_id = "TEST_USER_ID"
    consumer_key = "test_application_instance"
    data = {"user_id": user_id, "roles": "Instructor", "consumer_key": consumer_key}

    pyramid_request.db.add(User(lms_guid=user_id))
    pyramid_request.db.flush()

    jwt_secret = pyramid_request.registry.settings["jwt_secret"]
    jwt_token = jwt.encode(data, jwt_secret, "HS256").decode("utf-8")
    pyramid_request.params["jwt_token"] = jwt_token
    yield pyramid_request


class MockOauth2Session:
    def __init__(self, *args, **kwargs):
        """Mock the session."""
        pass

    def fetch_token(self, _token_url, **_):
        return {
            "access_token": "4346~asdf",
            "token_type": "Bearer",
            "user": {
                "id": 403,
                "name": "Nick Benoit",
                "global_id": "43460000000000403",
            },
            "refresh_token": "4346~refresh",
            "expires_in": 3600,
            "expires_at": 1513619852.757844,
        }


@pytest.fixture
def oauth_response(monkeypatch, pyramid_request):
    user_id = "test_user_123"
    roles = "fake_lti_roles"
    app_instance = build_from_lms_url(
        "https://example.com",
        "test@example.com",
        "test",
        b"test",
        pyramid_request.registry.settings["aes_secret"],
    )
    state_guid = "test_oauth_state"
    user = User(lms_guid=user_id)
    pyramid_request.db.add(user)
    pyramid_request.db.flush()
    lti_params = json.dumps(
        {
            "oauth_consumer_key": app_instance.consumer_key,
            "user_id": user_id,
            "roles": roles,
        }
    )
    pyramid_request.db.add(
        OauthState(user_id=user.id, guid=state_guid, lti_params=lti_params)
    )
    pyramid_request.db.add(app_instance)

    monkeypatch.setattr("requests_oauthlib.OAuth2Session", MockOauth2Session)

    pyramid_request.params["state"] = state_guid
    pyramid_request.params["code"] = "test_code"
    yield pyramid_request


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
