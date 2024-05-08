from dataclasses import asdict
from os import environ
from unittest import mock

import httpretty
import pytest
from pyramid import testing
from pyramid.request import apply_request_extensions

from lms.models import ApplicationSettings, LTIParams
from lms.models.lti_role import Role, RoleScope, RoleType
from lms.product import Product
from lms.security import Identity
from tests import factories
from tests.conftest import TEST_SETTINGS
from tests.unit.services import *  # pylint: disable=wildcard-import,unused-wildcard-import

TEST_SETTINGS["database_url"] = environ["DATABASE_URL"]


@pytest.fixture
def lti_v11_params():
    return {
        "oauth_consumer_key": "TEST_OAUTH_CONSUMER_KEY",
        "oauth_timestamp": "TEST_TIMESTAMP",
        "oauth_nonce": "TEST_NONCE",
        "oauth_signature_method": "SHA256",
        "oauth_signature": "TEST_OAUTH_SIGNATURE",
        "oauth_version": "1p0p0",
        "user_id": "TEST_USER_ID",
        "roles": "Instructor",
        "tool_consumer_instance_guid": "TEST_TOOL_CONSUMER_INSTANCE_GUID",
        "tool_consumer_info_product_family_code": "whiteboard",
        "content_item_return_url": "https://www.example.com",
        "lti_version": "LTI-1p0",
        "resource_link_id": "TEST_RESOURCE_LINK_ID",
        "resource_link_title": "TEST_RESOURCE_LINK_TITLE",
        "lis_person_name_given": "TEST_GIVEN_NAME",
        "lis_person_name_family": "TEST_FAMILY_NAME",
        "lis_person_name_full": "TEST_FULL_NAME",
        "lis_person_contact_email_primary": "EMAIL",
        "lti_message_type": "basic-lti-launch-request",
        "context_id": "DUMMY-CONTEXT-ID",
        "context_title": "A context title",
        "context_label": "A context label",
    }


@pytest.fixture
def lti_v13_params():
    return {
        "https://purl.imsglobal.org/spec/lti/claim/message_type": "LTI_MESSAGE_TYPE",
        "https://purl.imsglobal.org/spec/lti/claim/version": "LTI_VERSION",
        "https://purl.imsglobal.org/spec/lti/claim/resource_link": {
            "id": "RESOURCE_LINK_ID",
            "title": "RESOURCE_LINK_TITLE",
            "description": "RESOURCE_LINK_DESCRIPTION",
        },
        "iss": "ISSUER",
        "aud": "CLIENT_ID",
        "https://purl.imsglobal.org/spec/lti/claim/deployment_id": "DEPLOYMENT_ID",
        "sub": "USER_ID",
        "https://purl.imsglobal.org/spec/lti/claim/target_link_uri": "http://localhost:8001/lti_launches?url=https%3A%2F%2Felpais.es",
        "email": "EMAIL",
        "name": "FULL_NAME",
        "given_name": "GIVEN_NAME",
        "family_name": "FAMILY_NAME",
        "https://purl.imsglobal.org/spec/lti/claim/lis": {
            "person_sourcedid": "LIS_PERSON_SOURCEID"
        },
        "https://purl.imsglobal.org/spec/lti/claim/context": {
            "id": "CONTEXT_ID",
            "label": "LTI",
            "title": "CONTEXT_TITLE",
        },
        "https://purl.imsglobal.org/spec/lti/claim/tool_platform": {
            "guid": "GUID",
            "product_family_code": "FAMILY_CODE",
            "contact_email": "CONTACT_EMAIL",
            "name": "PLATFORM_NAME",
            "description": "PLATFORM_DESCRIPTION",
            "url": "PLATFORM_URL",
            "version": "PLATFORM_VERSION",
        },
        "https://purl.imsglobal.org/spec/lti/claim/roles": [
            "Instructor",
            "Student",
        ],
        "https://purl.imsglobal.org/spec/lti/claim/custom": {
            "canvas_course_id": 319,
            "canvas_api_domain": "hypothesis.instructure.com",
        },
        "https://purl.imsglobal.org/spec/lti/claim/launch_presentation": {
            "http://www.brightspace.com": {
                "org_defined_id": "ORG_DEFINED_ID",
            }
        },
    }


@pytest.fixture
def with_plugins(pyramid_request, mock_service):
    # Ensure that when plugins are read from the current product, all of its
    # plugins are mocked and ready to be looked up
    for plugin_class in asdict(pyramid_request.product.plugin_config).values():
        mock_service(plugin_class)


@pytest.fixture
def pyramid_request(db_session, application_instance, lti_v11_params):
    """
    Return a dummy Pyramid request object.

    This is the same dummy request object as is used by the pyramid_config
    fixture below.

    """
    pyramid_request = testing.DummyRequest(db=db_session)
    pyramid_request.POST.update(lti_v11_params)
    pyramid_request.feature = mock.create_autospec(
        lambda feature: False,  # noqa: ARG005
        return_value=False,  # pragma: no cover
    )
    pyramid_request.lti_user = factories.LTIUser(
        application_instance_id=application_instance.id,
        application_instance=application_instance,
        user_id=lti_v11_params["user_id"],
        roles=lti_v11_params["roles"],
    )
    pyramid_request.user = factories.User(
        application_instance_id=application_instance.id,
        user_id=lti_v11_params["user_id"],
    )

    pyramid_request.lti_jwt = {}
    pyramid_request.lti_params = LTIParams(v11=lti_v11_params)
    pyramid_request.product = Product.from_request(
        pyramid_request, dict(application_instance.settings)
    )

    # The DummyRequest request lacks a content_type property which the real
    # request has
    pyramid_request.content_type = None

    return pyramid_request


@pytest.fixture
def product(pyramid_request):
    return pyramid_request.product


@pytest.fixture
def user_is_learner(lti_user):
    lti_user.lti_roles = [
        factories.LTIRole(scope=RoleScope.COURSE, type=RoleType.LEARNER)
    ]
    lti_user.effective_lti_roles = [
        Role(scope=role.scope, type=role.type, value=role.value)
        for role in lti_user.lti_roles
    ]
    return lti_user


@pytest.fixture
def user_is_instructor(lti_user):
    lti_user.lti_roles = [
        factories.LTIRole(scope=RoleScope.COURSE, type=RoleType.INSTRUCTOR)
    ]
    lti_user.effective_lti_roles = [
        Role(scope=role.scope, type=role.type, value=role.value)
        for role in lti_user.lti_roles
    ]


@pytest.fixture
def user_has_no_roles(lti_user):
    lti_user.lti_roles = []
    lti_user.effective_lti_roles = []


def configure_jinja2_assets(config):
    jinja2_env = config.get_jinja2_environment()
    jinja2_env.globals["asset_url"] = "http://example.com"
    jinja2_env.globals["asset_urls"] = (
        lambda bundle: "http://example.com"  # noqa: ARG005
    )  # pragma: no cover
    jinja2_env.globals["js_config"] = {}


@pytest.fixture
def pyramid_config(pyramid_request, lti_v11_params):
    """
    Return a test Pyramid config (Configurator) object.

    The returned Configurator uses the dummy request from the pyramid_request
    fixture above.

    """

    with testing.testConfig(request=pyramid_request, settings=TEST_SETTINGS) as config:
        # Align request.identity with request.lti_user
        config.testing_securitypolicy(
            userid=lti_v11_params["user_id"],
            identity=Identity(lti_v11_params["user_id"], permissions=[]),
        )

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

        config.registry.notify = mock.Mock()

        apply_request_extensions(pyramid_request)

        yield config


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
def application_instance(db_session):
    application_instance = factories.ApplicationInstance(
        developer_key="TEST_DEVELOPER_KEY",
        provisioning=True,
        settings=ApplicationSettings({}),
        organization=factories.Organization(),
    )

    application_instance.settings.set("canvas", "sections_enabled", True)
    application_instance.settings.set("canvas", "groups_enabled", False)

    # Force flush to get a non None application_instance.id
    db_session.flush()
    return application_instance


@pytest.fixture
def organization(application_instance):
    return application_instance.organization


@pytest.fixture
def lti_registration():
    return factories.LTIRegistration()


@pytest.fixture
def lti_v13_application_instance(db_session, application_instance, lti_registration):
    # Force flush to get a non None application_instance and lti_registration IDs
    db_session.flush()

    application_instance.lti_registration_id = lti_registration.id
    application_instance.deployment_id = "ID"
    return application_instance


@pytest.fixture
def lti_user(pyramid_request):
    return pyramid_request.lti_user


@pytest.fixture
def oauth_token(lti_user, application_instance):
    return factories.OAuth2Token(
        user_id=lti_user.user_id,
        application_instance=application_instance,
    )
