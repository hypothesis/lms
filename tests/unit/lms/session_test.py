from pyramid.interfaces import ISessionFactory

from lms.session import includeme


def test_includeme(pyramid_config):
    includeme(pyramid_config)

    session_factory = pyramid_config.registry.queryUtility(ISessionFactory)
    assert session_factory is not None
    assert session_factory._cookie_secure is True  # pylint:disable=protected-access
