import pytest

from lms.app import create_app


class TestCreateApp:
    def test_it_doesnt_crash(self, pyramid_config):
        create_app(pyramid_config)


@pytest.fixture(autouse=True)
def configure(patch):
    return patch("lms.app.configure")
