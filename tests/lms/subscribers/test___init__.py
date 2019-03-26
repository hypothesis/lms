from pyramid.testing import testConfig

from lms.subscribers import includeme


class TestIncludeMe:
    def test_it_doesnt_crash(self):
        with testConfig() as config:
            includeme(config)
