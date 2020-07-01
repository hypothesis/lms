import re
from unittest import mock

import httpretty
import pytest
import sqlalchemy
from pyramid import testing
from pyramid.request import apply_request_extensions

from lms.models import ApplicationSettings
from lms.services.application_instance_getter import ApplicationInstanceGetter
from lms.services.canvas_api import CanvasAPIClient
from lms.services.course import CourseService
from lms.services.grading_info import GradingInfoService
from lms.services.group_info import GroupInfoService
from lms.services.h_api import HAPI
from lms.services.launch_verifier import LaunchVerifier
from lms.services.lti_h import LTIHService
from lms.services.lti_outcomes import LTIOutcomesClient
from lms.services.oauth1 import OAuth1Service
from tests import factories
from tests.conftest import SESSION, TEST_SETTINGS, get_test_database_url

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
    def restart_savepoint(session, transaction):  # pylint:disable=unused-variable
        if (
            transaction.nested
            and not transaction._parent.nested  # pylint: disable=protected-access
        ):  # pylint:disable=protected-access
            session.begin_nested()

    factories.set_sqlalchemy_session(session)

    try:
        yield session
    finally:
        factories.clear_sqlalchemy_session()
        session.close()
        trans.rollback()
        conn.close()


@pytest.fixture
def ai_getter(pyramid_config):
    ai_getter = mock.create_autospec(
        ApplicationInstanceGetter, spec_set=True, instance=True
    )
    ai_getter.provisioning_enabled.return_value = True
    ai_getter.lms_url.return_value = "https://example.com"
    ai_getter.shared_secret.return_value = "TEST_SECRET"
    ai_getter.settings.return_value = ApplicationSettings({})
    ai_getter.settings().set("canvas", "sections_enabled", True)
    pyramid_config.register_service(ai_getter, name="ai_getter")
    return ai_getter


@pytest.fixture
def canvas_api_client(pyramid_config):
    canvas_api_client = mock.create_autospec(
        CanvasAPIClient, spec_set=True, instance=True
    )
    canvas_api_client.get_token.return_value = (
        "test_access_token",
        "test_refresh_token",
        3600,
    )
    pyramid_config.register_service(canvas_api_client, name="canvas_api_client")
    return canvas_api_client


@pytest.fixture
def course_service(pyramid_config):
    course_service = mock.create_autospec(CourseService, spec_set=True, instance=True)
    pyramid_config.register_service(course_service, name="course")
    return course_service


@pytest.fixture
def launch_verifier(pyramid_config):
    launch_verifier = mock.create_autospec(LaunchVerifier, spec_set=True, instance=True)
    pyramid_config.register_service(launch_verifier, name="launch_verifier")
    return launch_verifier


@pytest.fixture
def grading_info_service(pyramid_config):
    grading_info_service = mock.create_autospec(
        GradingInfoService, instance=True, spec_set=True
    )
    grading_info_service.get_by_assignment.return_value = []
    pyramid_config.register_service(grading_info_service, name="grading_info")
    return grading_info_service


@pytest.fixture
def group_info_service(pyramid_config):
    group_info_service = mock.create_autospec(
        GroupInfoService, instance=True, spec_set=True
    )
    pyramid_config.register_service(group_info_service, name="group_info")
    return group_info_service


@pytest.fixture
def h_api(pyramid_config):
    h_api = mock.create_autospec(HAPI, spec_set=True, instance=True)
    h_api.get_user.return_value = factories.HUser()
    pyramid_config.register_service(h_api, name="h_api")
    return h_api


@pytest.fixture
def lti_h_service(pyramid_config):
    lti_h_service = mock.create_autospec(LTIHService, instance=True, spec_set=True)
    pyramid_config.register_service(lti_h_service, name="lti_h")
    return lti_h_service


@pytest.fixture
def lti_outcomes_client(pyramid_config):
    lti_outcomes_client = mock.create_autospec(
        LTIOutcomesClient, instance=True, spec_set=True
    )
    pyramid_config.register_service(lti_outcomes_client, name="lti_outcomes_client")
    return lti_outcomes_client


@pytest.fixture
def oauth1_service(pyramid_config):
    oauth1_service = mock.create_autospec(OAuth1Service, instance=True, spec_set=True)
    pyramid_config.register_service(oauth1_service, name="oauth1")
    return oauth1_service


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
