# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os
import functools
import mock
import pytest
import jwt
import sqlalchemy
from pyramid import testing
from pyramid.request import apply_request_extensions
from sqlalchemy.orm import sessionmaker
from lms import constants
from lms import db
from lms.config.settings import env_setting


TEST_DATABASE_URL = os.environ.get(
    'TEST_DATABASE_URL', 'postgresql://postgres@localhost:5433/lms_test')


SESSION = sessionmaker()


@pytest.fixture(scope='session')
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
        if transaction.nested and not transaction._parent.nested:  # pylint:disable=protected-access
            session.begin_nested()

    try:
        yield session
    finally:
        session.close()
        trans.rollback()
        conn.close()


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

    pyramid_request.POST.update({
        constants.OAUTH_CONSUMER_KEY: 'TEST_OAUTH_CONSUMER_KEY',
        constants.CUSTOM_CANVAS_USER_ID: 'TEST_CUSTOM_CANVAS_USER_ID',
        constants.CUSTOM_CANVAS_COURSE_ID: 'TEST_CUSTOM_CANVAS_COURSE_ID',
        constants.CUSTOM_CANVAS_ASSIGNMENT_ID: 'TEST_CUSTOM_CANVAS_ASSIGNMENT_ID',
        constants.EXT_CONTENT_RETURN_TYPES: 'TEST_EXT_CONTENT_RETURN_TYPES',
        constants.EXT_CONTENT_RETURN_URL: 'TEST_EXT_CONTENT_RETURN_URL',
        constants.LIS_OUTCOME_SERVICE_URL: 'TEST_LIS_OUTCOME_SERVICE_URL',
        constants.LIS_RESULT_SOURCEDID: 'TEST_LIS_RESULT_SOURCEDID',
        'oauth_timestamp': 'TEST_TIMESTAMP',
        'oauth_nonce': 'TEST_NONCE',
        'oauth_signature_method': 'SHA256',
        'oauth_signature': 'TEST_OAUTH_SIGNATURE',
        'oauth_version': '1p0p0',
        'user_id': 'TEST_USER_ID',
        'roles': 'Instructor',
        'tool_consumer_instance_guid': 'TEST_GUID',
        'content_item_return_url': 'https://www.example.com',
        'lti_version': 'TEST'
    })

    pyramid_request.raven = mock.MagicMock(spec_set=['captureException'])

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
        'lms_server': 'http://TEST_LMS_SERVER.com',
        'sqlalchemy.url': TEST_DATABASE_URL,
        'client_origin': 'http://TEST_H_SERVER.is',
        'via_url': 'http://TEST_VIA_SERVER.is',
        'jwt_secret': 'test_secret'
    }

    with testing.testConfig(request=pyramid_request, settings=settings) as config:
        config.include('pyramid_services')
        config.include('lms.db')
        config.include('pyramid_jinja2')
        apply_request_extensions(pyramid_request)

#        auth_data_svc = mock.create_autospec(auth_data.AuthDataService, instance=True)
#        auth_data_svc.get_canvas_server.return_value = 'https://TEST_CANVAS_SERVER.com'
#        auth_data_svc.get_lms_secret.return_value = 'TEST_CLIENT_SECRET'
#        auth_data_svc.get_lms_token.return_value = 'TEST_OAUTH_ACCESS_TOKEN'
#        auth_data_svc.get_lms_refresh_token.return_value = 'TEST_OAUTH_REFRESH_TOKEN'
#        config.register_service(auth_data_svc, name='auth_data')

        yield config


@pytest.fixture
def auth_data_svc(pyramid_request):
    return pyramid_request.find_service(name='auth_data')


@pytest.fixture(autouse=True)
def routes(pyramid_config):
    """Add all the routes that would be added in production."""
    pyramid_config.add_route('welcome', '/welcome')
    pyramid_config.add_route('config_xml', '/config_xml')
    pyramid_config.add_route('module_item_configurations', '/module_item_configurations')

    # lms routes
    pyramid_config.add_route('lti_launches', '/lti_launches')
    pyramid_config.add_route('content_item_selection', '/content_item_selection')


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
    from lms.models import application_instance as ai # pylint:disable=relative-import
    instance = ai.build_from_lms_url('https://hypothesis.instructure.com')
    pyramid_request.db.add(instance)
    pyramid_request.params['oauth_consumer_key'] = instance.consumer_key
    monkeypatch.setattr('pylti.common.verify_request_common', lambda a,b,c,d,e: True)
    yield pyramid_request


@pytest.fixture
def module_item_configuration():
  from lms.models import ModuleItemConfiguration # pylint:disable=relative-import
  instance = ModuleItemConfiguration(
      document_url='https://www.example.com',
      resource_link_id='TEST_RESOURCE_LINK_ID',
      tool_consumer_instance_guid='TEST_GUID'
  )
  yield instance

@pytest.fixture
def authenticated_request(pyramid_request):
    data = {'user_id': 'TEST_USER_ID', 'roles': 'Instructor'}
    jwt_token = jwt.encode(data, env_setting('JWT_SECRET'), 'HS256').decode('utf-8')
    pyramid_request.params['jwt'] = jwt_token
    yield pyramid_request


