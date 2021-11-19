from unittest import mock

import httpretty
import pytest
import sqlalchemy
from pyramid import testing
from pyramid.request import apply_request_extensions

from lms.db import SESSION
from lms.models import ApplicationSettings
from tests import factories
from tests.conftest import TEST_SETTINGS, get_test_database_url
from tests.unit.services import *  # pylint: disable=wildcard-import,unused-wildcard-import

TEST_SETTINGS["sqlalchemy.url"] = get_test_database_url(
    default="postgresql://postgres@localhost:5433/lms_test"
)


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
            "tool_consumer_info_product_family_code": "whiteboard",
            "content_item_return_url": "https://www.example.com",
            "lti_version": "TEST",
            "resource_link_id": "TEST_RESOURCE_LINK_ID",
        }
    )
    pyramid_request.feature = mock.create_autospec(
        lambda feature: False, return_value=False  # pragma: no cover
    )
    pyramid_request.lti_user = factories.LTIUser()

    # The DummyRequest request lacks a content_type property which the real
    # request has
    pyramid_request.content_type = None

    return pyramid_request


@pytest.fixture
def user_is_learner(pyramid_request):
    pyramid_request.lti_user = pyramid_request.lti_user._replace(roles="Learner")


@pytest.fixture
def user_is_instructor(pyramid_request):
    pyramid_request.lti_user = pyramid_request.lti_user._replace(roles="Instructor")


def configure_jinja2_assets(config):
    jinja2_env = config.get_jinja2_environment()
    jinja2_env.globals["asset_url"] = "http://example.com"
    jinja2_env.globals[
        "asset_urls"
    ] = lambda bundle: "http://example.com"  # pragma: no cover
    jinja2_env.globals["js_config"] = {}


@pytest.fixture
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
        config.include("pyramid_googleauth")

        config.include("lms.sentry")
        config.include("lms.models")
        config.include("lms.db")
        config.include("lms.routes")

        config.add_static_view(name="export", path="lms:static/export")
        config.add_static_view(name="static", path="lms:static")

        config.action(None, configure_jinja2_assets, args=(config,))

        apply_request_extensions(pyramid_request)

        yield config


@pytest.fixture
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
    def restart_savepoint(session, transaction):
        if (
            transaction.nested
            and not transaction._parent.nested  # pylint: disable=protected-access
        ):
            session.begin_nested()

    factories.set_sqlalchemy_session(session)

    try:
        yield session
    finally:
        factories.clear_sqlalchemy_session()
        session.close()
        trans.rollback()
        conn.close()


@pytest.fixture(autouse=True)
def routes(pyramid_config):
    """Add all the routes that would be added in production."""
    pyramid_config.add_route("welcome", "/welcome")
    pyramid_config.add_route("config_xml", "/config_xml")
    pyramid_config.add_route(
        "configure_assignment", "/assignment", request_method="POST"
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
    httpretty.enable(allow_net_connect=False)

    yield

    httpretty.disable()
    httpretty.reset()


@pytest.fixture
def application_instance(pyramid_request):
    return factories.ApplicationInstance(
        consumer_key=pyramid_request.lti_user.oauth_consumer_key
        if pyramid_request.lti_user
        else None,
        developer_key="TEST_DEVELOPER_KEY",
        provisioning=True,
        settings=ApplicationSettings({}),
    )


@pytest.fixture
def lti_user(pyramid_request):
    return pyramid_request.lti_user


@pytest.fixture
def oauth_token(lti_user, application_instance):
    return factories.OAuth2Token(
        user_id=lti_user.user_id, application_instance=application_instance
    )
