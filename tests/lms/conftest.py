# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os
import functools
import mock
import pytest
import jwt
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from pyramid import testing
from pyramid.request import apply_request_extensions
from lms import db
from lms import constants
from lms.config import env_setting


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
        constants.OAUTH_TIMESTAMP: 'TEST_TIMESTAMP',
        constants.OAUTH_NONCE: 'TEST_NONCE',
        constants.OAUTH_SIGNATURE_METHOD: 'SHA256',
        constants.OAUTH_SIGNATURE: 'TEST_OAUTH_SIGNATURE',
        constants.OAUTH_VERSION: '1p0p0',
        constants.USER_ID: 'TEST_USER_ID',
        constants.ROLES: 'Instructor',
        constants.TOOL_CONSUMER_INSTANCE_GUID: 'TEST_GUID',
        constants.CONTENT_ITEM_RETURN_URL: 'https://www.example.com',
        constants.LTI_VERSION: 'TEST'
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
        'username': 'report_viewers',
        'hashed_pw': 'e46df2a5b4d50e259b5154b190529483a5f8b7aaaa22a50447e377d33792577a',
        'salt': 'fbe82ee0da72b77b',
        'jinja2.filters': {
            'static_path': 'pyramid_jinja2.filters:static_path_filter',
            'static_url': 'pyramid_jinja2.filters:static_url_filter',
        }
    }

    with testing.testConfig(request=pyramid_request, settings=settings) as config:
        config.include('pyramid_jinja2')
        config.include('pyramid_tm')

        config.include('lms.sentry')
        config.include('lms.models')
        config.include('lms.db')
        config.include('lms.routes')

        config.add_static_view(name='export', path='lms:static/export')
        config.add_static_view(name='static', path='lms:static')

        apply_request_extensions(pyramid_request)

        yield config


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
    from lms.models import application_instance as ai  # pylint:disable=relative-import
    instance = ai.build_from_lms_url(
        'https://hypothesis.instructure.com',
        'address@)hypothes.is')
    pyramid_request.db.add(instance)
    pyramid_request.params['oauth_consumer_key'] = instance.consumer_key
    monkeypatch.setattr('pylti.common.verify_request_common', lambda a, b, c, d, e: True)
    yield pyramid_request


@pytest.fixture
def module_item_configuration():
    from lms.models import ModuleItemConfiguration  # pylint:disable=relative-import
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
    pyramid_request.params['jwt_token'] = jwt_token
    yield pyramid_request
