# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os
import functools

import mock
import pytest
from pyramid import testing
from pyramid.request import apply_request_extensions
import sqlalchemy
from sqlalchemy.orm import sessionmaker

from lti import constants
from lti import db
from lti.services import auth_data


TEST_DATABASE_URL = os.environ.get(
    'TEST_DATABASE_URL', 'postgresql://postgres@localhost:5433/lti_test')


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
        'lti_server': 'http://TEST_LTI_SERVER.com',
        'lti_files_path': '/var/lib/lti',
        'sqlalchemy.url': TEST_DATABASE_URL,
        'via_url': 'https://via.hypothes.is',
    }

    with testing.testConfig(request=pyramid_request, settings=settings) as config:
        config.include('pyramid_services')
        config.include('lti.db')

        apply_request_extensions(pyramid_request)

        auth_data_svc = mock.create_autospec(auth_data.AuthDataService, instance=True)
        auth_data_svc.get_canvas_server.return_value = 'https://TEST_CANVAS_SERVER.com'
        auth_data_svc.get_lti_secret.return_value = 'TEST_CLIENT_SECRET'
        auth_data_svc.get_lti_token.return_value = 'TEST_OAUTH_ACCESS_TOKEN'
        auth_data_svc.get_lti_refresh_token.return_value = 'TEST_OAUTH_REFRESH_TOKEN'
        config.register_service(auth_data_svc, name='auth_data')

        yield config


@pytest.fixture
def auth_data_svc(pyramid_request):
    return pyramid_request.find_service(name='auth_data')


@pytest.fixture(autouse=True)
def routes(pyramid_config):
    """Add all the routes that would be added in production."""
    pyramid_config.add_route('lti_setup', '/lti_setup')
    pyramid_config.add_route('canvas_resource_selection', '/canvas/resource_selection')
    pyramid_config.add_static_view(
        name='cache', path=pyramid_config.registry.settings['lti_files_path'])


@pytest.yield_fixture
def factories(db_session):
    import factories  # pylint:disable=relative-import
    factories.set_session(db_session)
    yield factories
    factories.set_session(None)
